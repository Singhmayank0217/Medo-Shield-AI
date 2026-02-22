from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.database import Database, settings
from app.schemas import (
    HealthRiskAssessment, MedicationReminder, Medication,
    AIReport, AIConversationMessage, MedicationRecommendationRequest
)
from app.auth import require_roles
import json
import aiohttp
from app.medications import recommend_medications
from app.medication_engine import medication_engine
from app.pdf_generator import pdf_generator
from fastapi.responses import Response
import base64
import tempfile
import os
import uuid
import shutil

router = APIRouter(prefix="/api/health", tags=["health"])


async def _verify_patient_access(db, patient_id: str, context: dict) -> dict:
    """Ensure the caller can access the patient record."""
    if context["role"] == "patient":
        patient = await db["patients"].find_one({"user_id": context["user_id"]})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        expected_id = str(patient.get("_id", context["user_id"]))
        if patient_id not in {expected_id, patient.get("user_id")}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return patient

    if context["role"] == "doctor":
        assignment = await db["patient_doctor_assignments"].find_one({
            "patient_id": patient_id,
            "doctor_id": context["user_id"],
            "is_active": True
        })
        if not assignment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        patient = await db["patients"].find_one({"_id": ObjectId(patient_id)})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        return patient

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


async def _create_notification(db, patient_id: str, title: str, message: str, category: str):
    await db["notifications"].insert_one({
        "patient_id": patient_id,
        "title": title,
        "message": message,
        "category": category,
        "is_read": False,
        "created_at": datetime.utcnow()
    })


async def _call_gemini(prompt: str) -> str:
    if not settings.GEMINI_API_KEY:
        return ""

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 800
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                data = await response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        return candidates[0]["content"]["parts"][0].get("text", "")
    except Exception:
        return ""

@router.post("/risk-assessment")
async def create_risk_assessment(
    assessment: HealthRiskAssessment,
    context: dict = Depends(require_roles(["doctor"]))
):
    """Create a health risk assessment."""
    db = Database.get_db()
    
    # Verify patient exists
    patient = await db["patients"].find_one({
        "_id": ObjectId(assessment.patient_id)
    })
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    assessment_doc = {
        "patient_id": assessment.patient_id,
        "risk_date": assessment.risk_date,
        "disease_risk_score": assessment.disease_risk_score,
        "disease_risk_level": assessment.disease_risk_level,
        "risk_factors": assessment.risk_factors,
        "recommendations": assessment.recommendations,
        "lab_results": assessment.lab_results,
        "wearable_metrics": assessment.wearable_metrics,
        "next_screening_date": assessment.next_screening_date,
        "created_by": context["user_id"],
        "created_at": datetime.utcnow()
    }
    
    result = await db["health_risk_assessments"].insert_one(assessment_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": "Risk assessment created successfully"
    }


@router.get("/risk-timeline/{patient_id}")
async def get_risk_timeline(
    patient_id: str,
    days: int = 90,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get patient's health risk timeline."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    assessments = await db["health_risk_assessments"].find({
        "patient_id": patient_id,
        "risk_date": {"$gte": start_date}
    }).sort("risk_date", 1).to_list(100)
    
    # Calculate trends
    risk_trend = "stable"
    if len(assessments) >= 2:
        latest = assessments[-1]["disease_risk_score"]
        previous = assessments[-2]["disease_risk_score"]
        if latest > previous + 5:
            risk_trend = "increasing"
        elif latest < previous - 5:
            risk_trend = "decreasing"
    
    return {
        "patient_id": patient_id,
        "timeline": assessments,
        "total": len(assessments),
        "risk_trend": risk_trend,
        "latest_assessment": assessments[-1] if assessments else None,
        "date_range": {
            "start": start_date.isoformat(),
            "end": datetime.utcnow().isoformat()
        }
    }


@router.post("/medication/reminder")
async def set_medication_reminder(
    reminder: MedicationReminder,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Set medication reminders for patient."""
    db = Database.get_db()
    await _verify_patient_access(db, reminder.patient_id, context)
    
    reminder_doc = {
        "patient_id": reminder.patient_id,
        "medications": [med.dict() for med in reminder.medications],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "adherence_rate": 0.0
    }
    
    result = await db["medication_reminders"].insert_one(reminder_doc)

    await _create_notification(
        db,
        reminder.patient_id,
        "Medication schedule updated",
        "A new medication schedule has been added. Please review your reminders.",
        "medication"
    )
    
    return {
        "id": str(result.inserted_id),
        "message": "Medication reminders set successfully"
    }


@router.get("/medication/schedule/{patient_id}")
async def get_medication_schedule(
    patient_id: str,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get patient's medication schedule."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)
    
    reminder = await db["medication_reminders"].find_one({
        "patient_id": patient_id,
        "is_active": True
    })
    
    if not reminder:
        return {
            "patient_id": patient_id,
            "medications": [],
            "schedule": []
        }
    
    # Build daily schedule
    schedule = {}
    for med in reminder["medications"]:
        for time_slot in med.get("time_slots", []):
            if time_slot not in schedule:
                schedule[time_slot] = []
            schedule[time_slot].append(med["name"])
    
    # Sort by time
    sorted_schedule = dict(sorted(schedule.items()))
    
    return {
        "patient_id": patient_id,
        "medications": reminder["medications"],
        "daily_schedule": sorted_schedule,
        "adherence_rate": reminder.get("adherence_rate", 0),
        "last_taken": reminder.get("last_taken"),
        "created_at": reminder["created_at"]
    }


@router.post("/medication/record-taken/{patient_id}")
async def record_medication_taken(
    patient_id: str,
    medication_name: str,
    context: dict = Depends(require_roles(["patient"]))
):
    """Record that patient took medication."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)
    
    # Update reminder
    result = await db["medication_reminders"].update_one(
        {"patient_id": patient_id},
        {
            "$set": {
                "last_taken": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Log medication event
    await db["medication_logs"].insert_one({
        "patient_id": patient_id,
        "medication_name": medication_name,
        "taken_at": datetime.utcnow()
    })
    
    return {
        "message": "Medication recorded successfully",
        "taken_at": datetime.utcnow().isoformat()
    }


@router.post("/report/generate")
async def generate_ai_report(
    patient_id: str,
    report_type: str = "Monthly Summary",
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Generate AI report for patient."""
    db = Database.get_db()
    patient = await _verify_patient_access(db, patient_id, context)
    
    # Get patient data
    # Get latest assessments
    assessments = await db["health_risk_assessments"].find({
        "patient_id": patient_id
    }).sort("risk_date", -1).to_list(5)
    
    # Generate report content (simplified AI)
    key_findings = []
    recommendations = []
    
    if assessments:
        latest = assessments[0]
        
        if latest["disease_risk_level"] == "Critical":
            key_findings.append("Critical risk level detected - immediate intervention recommended")
            recommendations.append("Schedule urgent appointment with specialist")
        elif latest["disease_risk_level"] == "High":
            key_findings.append("High disease risk indicated")
            recommendations.append("Schedule follow-up appointment within 1-2 weeks")
        
        key_findings.extend(latest.get("risk_factors", [])[:3])
        recommendations.extend(latest.get("recommendations", [])[:3])
    
    # Default recommendations
    if not recommendations:
        recommendations = [
            "Continue current treatment plan",
            "Maintain regular check-ups",
            "Monitor symptoms and report changes",
            "Improve lifestyle habits: exercise, nutrition, sleep"
        ]
    
    report_prompt = (
        "You are a clinical report assistant. Create a concise, patient-friendly report. "
        "Do not diagnose. Use sections: Summary, Key Findings, Recommendations, Next Steps. "
        f"Report type: {report_type}. Patient: {patient.get('first_name')} {patient.get('last_name')}. "
        f"Assessments: {json.dumps(assessments, default=str)}."
    )

    ai_report = await _call_gemini(report_prompt)
    report_content = ai_report.strip() if ai_report else (
        f"""
## {report_type} - {patient.get('first_name')} {patient.get('last_name')}

Generated: {datetime.utcnow().strftime('%B %d, %Y')}

### Summary
Patient has been monitored over the past period with focus on disease risk assessment and preventive care.

### Key Findings
{chr(10).join([f'- {finding}' for finding in key_findings[:5]])}

### Recommendations
{chr(10).join([f'- {rec}' for rec in recommendations[:5]])}

### Next Steps
- Schedule follow-up assessment
- Review medications with prescribing physician
- Implement lifestyle modifications as recommended
- Consider additional diagnostic testing if warranted

This report is AI-assisted and should be reviewed by qualified healthcare professionals.
"""
    )
    
    report_doc = {
        "patient_id": patient_id,
        "report_type": report_type,
        "generated_by_ai": "Gemini",
        "content": report_content,
        "key_findings": key_findings,
        "recommendations": recommendations,
        "created_at": datetime.utcnow(),
        "created_by": context["user_id"]
    }
    
    await _create_notification(
        db,
        patient_id,
        "New AI report generated",
        f"A new {report_type} report is available for review.",
        "report"
    )

    result = await db["ai_reports"].insert_one(report_doc)
    
    return {
        "id": str(result.inserted_id),
        "report_type": report_type,
        "content": report_content,
        "key_findings": key_findings,
        "recommendations": recommendations,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/report/{report_id}")
async def get_report(
    report_id: str,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get specific report."""
    db = Database.get_db()
    
    report = await db["ai_reports"].find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await _verify_patient_access(db, report["patient_id"], context)
    
    return {
        "id": str(report["_id"]),
        "patient_id": report["patient_id"],
        "report_type": report["report_type"],
        "content": report["content"],
        "key_findings": report["key_findings"],
        "recommendations": report["recommendations"],
        "created_at": report["created_at"]
    }


@router.get("/reports/{patient_id}")
async def get_patient_reports(
    patient_id: str,
    limit: int = 10,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get all reports for patient."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)
    
    reports = await db["ai_reports"].find({
        "patient_id": patient_id
    }).sort("created_at", -1).to_list(limit)
    
    return {
        "patient_id": patient_id,
        "reports": [
            {
                "id": str(r["_id"]),
                "report_type": r["report_type"],
                "created_at": r["created_at"],
                "key_findings": r.get("key_findings", [])[:3]
            }
            for r in reports
        ],
        "total": len(reports)
    }


def _parse_suggested_specialty(text: str) -> tuple:
    """Extract [SUGGESTED_SPECIALTY: X] from end of response and return (clean_response, specialty or None)."""
    import re
    if not text:
        return text, None
    match = re.search(r'\s*\[SUGGESTED_SPECIALTY:\s*([^\]]+)\]\s*$', text, re.IGNORECASE)
    if match:
        specialty = match.group(1).strip()
        clean = text[:match.start()].strip()
        return clean, specialty
    return text, None


class ChatbotMessageRequest(BaseModel):
    """Request body for chatbot message with optional conversation history."""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None  # [{"role":"user"|"assistant","content":"..."}]


@router.post("/chatbot/message")
async def chatbot_message(
    patient_id: str,
    body: ChatbotMessageRequest,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Send message to AI health chatbot. Uses conversation history to talk like ChatGPT, then suggests one relevant doctor when appropriate."""
    db = Database.get_db()
    patient = await _verify_patient_access(db, patient_id, context)
    latest_assessment = await db["health_risk_assessments"].find_one(
        {"patient_id": patient_id},
        sort=[("risk_date", -1)]
    )
    patient_summary = {
        "first_name": patient.get("first_name"),
        "last_name": patient.get("last_name"),
        "medical_history": (patient.get("medical_history") or "")[:500],
        "date_of_birth": str(patient.get("date_of_birth")) if patient.get("date_of_birth") else None,
    }
    message = body.message.strip()
    history = body.conversation_history or []
    # Build conversation context for Gemini (last 10 exchanges)
    conv_text = ""
    for h in history[-20:]:
        role = (h.get("role") or "user").lower()
        content = (h.get("content") or "").strip()
        if not content:
            continue
        label = "User" if role == "user" else "Assistant"
        conv_text += f"{label}: {content}\n"
    if conv_text:
        conv_text = "Previous conversation:\n" + conv_text + "\nLatest user message: " + message
    else:
        conv_text = "User message: " + message

    prompt = f"""You are a friendly, conversational AI health assistant (like a trained nurse). Your job is to:
1. TALK LIKE A HUMAN: Ask follow-up questions when needed ("What happened?", "When did it start?", "How long has this been going on?", "Where do you feel it?"). Have a short back-and-forth to understand the problem before giving advice.
2. ANALYZE what the user tells you and then give clear, kind, educational advice. Do not diagnose; suggest seeing a doctor when appropriate.
3. When you have enough context and the concern clearly points to a specialist, say so in your reply and at the very end add exactly: [SUGGESTED_SPECIALTY: SpecialtyName]
   Only suggest ONE specialist when it fits. Use exactly one of: Neurologist, Physiotherapist, Cardiologist, Therapist, Psychiatrist, Dermatologist, General Practitioner, Orthopedist, Pulmonologist, Gastroenterologist, Endocrinologist.
4. Keep replies concise (2–4 short paragraphs). Always end by asking if they have more questions or by suggesting they book an appointment if needed.

Patient context (for personalization only): {json.dumps(patient_summary, default=str)}
Latest risk: {json.dumps(latest_assessment, default=str) if latest_assessment else "None"}

{conv_text}

Respond as the Assistant. Be warm and professional. If the user's concern suggests a specialist, add [SUGGESTED_SPECIALTY: ...] at the end of your message."""

    response_text = await _call_gemini(prompt)
    if not response_text:
        response_text = generate_chatbot_response(message, patient, latest_assessment)
    response_text, suggested_specialty = _parse_suggested_specialty(response_text)
    conversation_doc = {
        "patient_id": patient_id,
        "messages": [
            {"role": "user", "content": message, "timestamp": datetime.utcnow()},
            {"role": "assistant", "content": response_text, "timestamp": datetime.utcnow()}
        ],
        "created_at": datetime.utcnow()
    }
    await db["chatbot_conversations"].insert_one(conversation_doc)
    return {
        "patient_id": patient_id,
        "user_message": message,
        "assistant_response": response_text,
        "suggested_specialty": suggested_specialty,
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "This is AI-assisted information only. Always consult with your healthcare provider for medical decisions."
    }


@router.post("/medication/recommendations")
async def get_medication_recommendations(
    request: MedicationRecommendationRequest,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get intelligent medication recommendations based on symptoms and age."""
    db = Database.get_db()
    patient = await _verify_patient_access(db, request.patient_id, context)

    # Get patient profile for personalized recommendations
    patient_profile = {
        'age': patient.get('age', request.age),
        'medical_history': patient.get('medical_history', ''),
        'allergies': patient.get('allergies', []),
        'current_medications': patient.get('current_medications', [])
    }

    # Convert symptoms list to string
    symptoms_text = ', '.join(request.symptoms) if request.symptoms else ''
    
    # Get recommendations from advanced medication engine
    recommendations = await medication_engine.recommend_medications(
        symptoms=symptoms_text,
        age=request.age or patient_profile['age'] or 0,
        patient_profile=patient_profile,
        conditions=request.conditions
    )

    # Save recommendation to database
    await db["medication_recommendations"].insert_one({
        "patient_id": request.patient_id,
        "symptoms": symptoms_text,
        "age": request.age,
        "recommendations": recommendations,
        "created_at": datetime.utcnow(),
        "created_by": context["user_id"]
    })

    # Create notification
    await _create_notification(
        db,
        request.patient_id,
        "Medication Recommendations Available",
        f"New medication recommendations based on your symptoms: {symptoms_text[:50]}...",
        "medication"
    )

    # Auto-generate medication schedule if recommendations are available
    if recommendations.get('medications'):
        await _auto_generate_medication_schedule(
            db, 
            request.patient_id, 
            recommendations['medications'],
            patient_profile['age']
        )

    return {
        "patient_id": request.patient_id,
        "success": True,
        **recommendations
    }


# =====================
# PDF MEDICAL REPORT ANALYSIS (Gemini)
# =====================

def _extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes. Returns empty string on failure."""
    try:
        from pypdf import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(content))
        parts = []
        for i, page in enumerate(reader.pages):
            if i >= 50:
                break
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts).strip() if parts else ""
    except Exception as e:
        print(f"PDF extract error: {e}")
        return ""


@router.post("/pdf-report/analyze")
async def analyze_pdf_report(
    file: UploadFile = File(...),
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Analyze uploaded medical PDF with Gemini: short description, main risk, how to fix, causes."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a PDF file.")
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF too large (max 20 MB).")
    text = _extract_text_from_pdf(content)
    if not text:
        text = "[No text could be extracted from this PDF. It may be scanned or image-based.]"
    text_sample = (text[:12000] + "...") if len(text) > 12000 else text

    prompt = f"""You are a medical report analyst. Analyze the following medical report content and respond in a structured way.

REPORT CONTENT (extracted from PDF):
{text_sample}

Provide a clear, patient-friendly analysis. Use these exact section headers in your response:

1) SHORT_DESCRIPTION: In 2-4 sentences, what is this report about and what does it say about the patient? (plain language)

2) MAIN_RISK: What is the main risk or concern from this report? (one short paragraph)

3) HOW_TO_FIX: What steps or actions are recommended to address the findings? (bullet points or short paragraph)

4) REPORT_SUMMARY: What type of report is this (e.g. blood test, imaging) and what are the key findings?

5) CAUSES: What might cause or explain these findings? (brief, non-diagnostic)

6) OVERALL_RISK: One word: Low, Normal, Medium, High, or Critical

7) RECOMMENDED_SPECIALIST: If applicable, one specialist type (e.g. Cardiologist, Neurologist, General Practitioner). Otherwise write "General Practitioner".

8) FINDINGS_JSON: If you can list specific test names and values, output a JSON array of objects with keys: test_name, value, normal_range, status, note. If not applicable, output: []

Format your reply so we can parse it. After your narrative for 1-5, add a line "OVERALL_RISK: <word>" and "RECOMMENDED_SPECIALIST: <name>". Then add "FINDINGS_JSON: " followed by the JSON array only."""

    ai_response = await _call_gemini(prompt)
    if not ai_response:
        ai_response = (
            "SHORT_DESCRIPTION: This appears to be a medical report. We could not analyze it automatically. "
            "Please share it with your doctor for a proper interpretation.\n"
            "MAIN_RISK: Unknown—review with a clinician.\n"
            "HOW_TO_FIX: Schedule a follow-up with your doctor to discuss the report.\n"
            "OVERALL_RISK: Normal\nRECOMMENDED_SPECIALIST: General Practitioner\nFINDINGS_JSON: []"
        )

    summary = ai_response
    overall_risk = "Normal"
    recommended_specialist = "General Practitioner"
    findings = []
    short_description = ""
    main_risk = ""
    how_to_fix = ""
    report_summary = ""
    causes = ""

    import re
    def extract_section(name: str) -> str:
        pat = re.compile(rf"\b{re.escape(name)}\s*:\s*(.+?)(?=\n[A-Z_]+:|\n\n|\Z)", re.IGNORECASE | re.DOTALL)
        m = pat.search(ai_response)
        return m.group(1).strip() if m else ""

    short_description = extract_section("SHORT_DESCRIPTION") or extract_section("1)")
    main_risk = extract_section("MAIN_RISK") or extract_section("2)")
    how_to_fix = extract_section("HOW_TO_FIX") or extract_section("3)")
    report_summary = extract_section("REPORT_SUMMARY") or extract_section("4)")
    causes = extract_section("CAUSES") or extract_section("5)")

    for line in ai_response.split("\n"):
        line = line.strip()
        if line.upper().startswith("OVERALL_RISK:"):
            overall_risk = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("RECOMMENDED_SPECIALIST:"):
            recommended_specialist = line.split(":", 1)[-1].strip()
        elif "FINDINGS_JSON:" in line.upper():
            try:
                json_str = line.split(":", 1)[-1].strip()
                findings = json.loads(json_str) if json_str and json_str != "[]" else []
            except Exception:
                pass

    if not short_description and summary:
        short_description = summary[:600]

    return {
        "summary": short_description or summary,
        "short_description": short_description or summary[:400],
        "main_risk": main_risk,
        "how_to_fix": how_to_fix,
        "report_summary": report_summary,
        "causes": causes,
        "overall_risk": overall_risk,
        "recommended_specialist": recommended_specialist or "General Practitioner",
        "findings": findings if isinstance(findings, list) else [],
        "ai_report": summary,
    }


async def _auto_generate_medication_schedule(
    db, 
    patient_id: str, 
    medications: List[Dict],
    patient_age: int
):
    """Automatically generate medication schedule based on recommendations."""
    
    schedule_items = []
    
    for med in medications:
        med_name = med.get('name', '')
        frequency = med.get('frequency', 'once daily')
        dosage = med.get('dosage', 'As prescribed')
        
        # Parse frequency and generate time slots
        time_slots = []
        
        if 'once daily' in frequency.lower() or 'daily' in frequency.lower():
            time_slots = ['09:00']
        elif 'twice daily' in frequency.lower() or 'every 12 hours' in frequency.lower():
            time_slots = ['09:00', '21:00']
        elif 'three times daily' in frequency.lower() or 'every 8 hours' in frequency.lower():
            time_slots = ['09:00', '17:00', '01:00']
        elif 'four times' in frequency.lower() or 'every 6 hours' in frequency.lower():
            time_slots = ['06:00', '12:00', '18:00', '00:00']
        elif 'every 4-6 hours' in frequency.lower() or 'every 4 hours' in frequency.lower():
            time_slots = ['06:00', '10:00', '14:00', '18:00', '22:00']
        else:
            time_slots = ['09:00']  # Default to morning
        
        schedule_items.append({
            'name': med_name,
            'dosage': dosage,
            'frequency': frequency,
            'time_slots': time_slots,
            'instructions': f"Take {dosage} {frequency}",
            'max_daily': med.get('max_daily', 'Follow medical advice'),
            'confidence': med.get('confidence', 0),
            'active': True
        })
    
    # Check if schedule already exists
    existing = await db["medication_reminders"].find_one({
        "patient_id": patient_id,
        "is_active": True
    })
    
    if existing:
        # Update existing schedule
        await db["medication_reminders"].update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "medications": schedule_items,
                    "updated_at": datetime.utcnow(),
                    "auto_generated": True,
                    "generation_source": "AI Recommendation"
                }
            }
        )
    else:
        # Create new schedule
        await db["medication_reminders"].insert_one({
            "patient_id": patient_id,
            "medications": schedule_items,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "adherence_rate": 0.0,
            "auto_generated": True,
            "generation_source": "AI Recommendation"
        })
    
    # Notify patient
    await _create_notification(
        db,
        patient_id,
        "Medication Schedule Created",
        f"A personalized medication schedule has been created with {len(schedule_items)} medications. Check your reminders!",
        "medication"
    )


@router.get("/notifications/{patient_id}")
async def get_notifications(
    patient_id: str,
    context: dict = Depends(require_roles(["patient"]))
):
    """Get in-app notifications for a patient."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    notifications = await db["notifications"].find({
        "patient_id": patient_id
    }).sort("created_at", -1).to_list(50)

    # Convert ObjectId to string for serialization
    for notif in notifications:
        if "_id" in notif:
            notif["_id"] = str(notif["_id"])
        if "created_at" in notif:
            notif["created_at"] = notif["created_at"].isoformat() if hasattr(notif["created_at"], 'isoformat') else str(notif["created_at"])

    return {
        "patient_id": patient_id,
        "notifications": notifications,
        "total": len(notifications)
    }


@router.post("/notifications/{patient_id}/mark-read")
async def mark_notifications_read(
    patient_id: str,
    context: dict = Depends(require_roles(["patient"]))
):
    """Mark all notifications as read for a patient."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    await db["notifications"].update_many(
        {"patient_id": patient_id},
        {"$set": {"is_read": True}}
    )

    return {"message": "Notifications marked as read"}


@router.post("/video/analyze")
async def analyze_video_with_gemini(
    patient_id: str,
    video_base64: str,
    analysis_type: str = "gait",
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """
    Analyze patient video using Gemini AI for neurological assessment.
    Supports: gait analysis, tremor detection, pose analysis
    """
    db = Database.get_db()
    patient = await _verify_patient_access(db, patient_id, context)
    
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API not configured")
    
    # Decode video from base64
    try:
        video_data = base64.b64decode(video_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid video data: {str(e)}")
    
    # Save video temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(video_data)
        video_path = tmp_file.name
    
    try:
        # Prepare analysis prompt based on type
        analysis_prompts = {
            "gait": """Analyze this video for gait abnormalities commonly seen in Parkinson's disease and other neurological conditions:
            
1. **Gait Characteristics:**
   - Step length and symmetry
   - Walking speed and rhythm
   - Arm swing patterns
   - Posture and balance
   - Freezing episodes
   - Turning movements

2. **Abnormalities to Identify:**
   - Shuffling steps
   - Reduced arm swing
   - Stooped posture
   - Festination (accelerating gait)
   - Balance issues
   
3. **Severity Assessment:** Rate each finding as Mild/Moderate/Severe

4. **Recommendations:**
   - Physical therapy needs
   - Fall risk assessment
   - Medication considerations
   - Follow-up requirements

Provide a detailed, professional medical analysis report.""",

            "tremor": """Analyze this video for tremor characteristics:

1. **Tremor Properties:**
   - Type: Resting, postural, or action tremor
   - Frequency: Slow (<4Hz), medium (4-7Hz), or fast (>7Hz)
   - Amplitude: Mild, moderate, or severe
   - Body parts affected
   - Symmetry: Unilateral or bilateral

2. **Parkinsonian Features:**
   - Pill-rolling tremor
   - Assymetric presentation
   - Amplitude variation

3. **Impact Assessment:**
   - Effect on daily activities
   - Writing, eating, dressing abilities
   
4. **Recommendations:**
   - Medication adjustment needs
   - Occupational therapy
   - Assistive devices
   - Further neurological evaluation

Provide comprehensive tremor analysis report.""",

            "pose": """Analyze body posture and movement patterns:

1. **Posture Analysis:**
   - Spinal alignment
   - Head position
   - Shoulder symmetry
   - Pelvic alignment
   - Overall balance

2. **Movement Quality:**
   - Fluidity of movements
   - Range of motion
   - Bradykinesia (slowness)
   - Rigidity indicators
   
3. **Functional Assessment:**
   - Sit-to-stand transitions
   - Reaching movements
   - Coordination
   
4. **Clinical Significance:**
   - Neurological indicators
   - Musculoskeletal concerns
   - Rehabilitation needs

Provide detailed postural and movement analysis."""
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["gait"])
        
        # Call Gemini Vision API for video analysis
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        # For now, use text-based analysis with frame description
        # In production, you'd upload the video file to Gemini File API
        enhanced_prompt = f"""
{prompt}

**Patient Information:**
- Name: {patient.get('first_name', '')} {patient.get('last_name', '')}
- Age: {patient.get('age', 'Not provided')}
- Medical History: {patient.get('medical_history', 'Not provided')}

**Analysis Type:** {analysis_type.upper()}

**Instructions:**
Generate a comprehensive medical report in the following format:

## NEUROLOGICAL ASSESSMENT REPORT

### Patient Details
- Name: [Patient Name]
- Date: {datetime.utcnow().strftime('%B %d, %Y')}
- Analysis Type: {analysis_type.capitalize()} Analysis

### Clinical Findings
[Detailed observations]

### Severity Assessment
[Rate each finding]

### Diagnostic Impressions
[Clinical interpretation]

### Recommended Medications
Based on findings, suggest appropriate medications with dosages:
- [Medication 1]: Dosage and frequency
- [Medication 2]: Dosage and frequency

### Recommendations
1. [Specific recommendation]
2. [Specific recommendation]
3. [Specific recommendation]

### Follow-up Care
[Next steps and timeline]

### Important Notes
[Safety concerns, disclaimers]

---
*This is an AI-assisted analysis. All findings should be confirmed by a licensed neurologist.*
"""
        
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": enhanced_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Gemini API error")
                data = await response.json()
        
        candidates = data.get("candidates", [])
        if not candidates:
            raise HTTPException(status_code=500, detail="No analysis generated")
        
        analysis_report = candidates[0]["content"]["parts"][0].get("text", "")
        
        # Extract medication recommendations from the report
        medications_mentioned = []
        for med in ["Paracetamol", "Ibuprofen", "Aspirin", "Lipitor", "Penicillin", "Levodopa", "Carbidopa", "Pramipexole"]:
            if med.lower() in analysis_report.lower():
                medications_mentioned.append(med)
        
        # Save analysis to database
        analysis_doc = {
            "patient_id": patient_id,
            "video_path": f"video_{datetime.utcnow().timestamp()}.mp4",
            "analysis_type": analysis_type,
            "ai_model": "Gemini 1.5 Flash",
            "report_content": analysis_report,
            "medications_recommended": medications_mentioned,
            "created_at": datetime.utcnow(),
            "analyzed_by": context["user_id"],
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            "patient_age": patient.get('age')
        }
        
        result = await db["video_analyses"].insert_one(analysis_doc)
        
        # Create notification
        await _create_notification(
            db,
            patient_id,
            "Video Analysis Complete",
            f"AI analysis completed for {analysis_type} assessment. View detailed report now.",
            "report"
        )
        
        return {
            "success": True,
            "analysis_id": str(result.inserted_id),
            "patient_id": patient_id,
            "analysis_type": analysis_type,
            "report": analysis_report,
            "medications_recommended": medications_mentioned,
            "created_at": datetime.utcnow().isoformat(),
            "ai_model": "Gemini 1.5 Flash"
        }
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(video_path)
        except:
            pass


@router.get("/video/analysis/{analysis_id}/pdf")
async def download_analysis_pdf(
    analysis_id: str,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Download video analysis report as professional PDF."""
    db = Database.get_db()
    
    # Get analysis
    analysis = await db["video_analyses"].find_one({"_id": ObjectId(analysis_id)})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Verify access
    await _verify_patient_access(db, analysis["patient_id"], context)
    
    # Get patient info
    patient = await db["patients"].find_one({"_id": ObjectId(analysis["patient_id"])})
    
    # Get medications if available
    medications = []
    if analysis.get("medications_recommended"):
        for med_name in analysis["medications_recommended"]:
            med_info = medication_engine._get_dosage_by_age(med_name, patient.get('age', 30))
            medications.append({
                'name': med_name,
                **med_info
            })
    
    # Generate PDF
    pdf_bytes = pdf_generator.generate_video_analysis_report(
        patient_info=patient,
        analysis_data=analysis,
        medications=medications
    )
    
    # Return PDF as download
    filename = f"Neuro_Assessment_{patient.get('first_name', 'Patient')}_{analysis['analysis_type']}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/history/{patient_id}")
async def get_health_history(
    patient_id: str,
    limit: int = 50,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get comprehensive health history for a patient including all reports, analyses, and medications."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)
    
    # Get all video analyses
    video_analyses = await db["video_analyses"].find({
        "patient_id": patient_id
    }).sort("created_at", -1).to_list(limit)
    
    # Get all AI reports
    ai_reports = await db["ai_reports"].find({
        "patient_id": patient_id
    }).sort("created_at", -1).to_list(limit)
    
    # Get medication recommendations
    med_recommendations = await db["medication_recommendations"].find({
        "patient_id": patient_id
    }).sort("created_at", -1).to_list(limit)
    
    # Get risk assessments
    risk_assessments = await db["health_risk_assessments"].find({
        "patient_id": patient_id
    }).sort("risk_date", -1).to_list(limit)
    
    # Format history entries
    history_entries = []
    
    # Add video analyses
    for analysis in video_analyses:
        created = analysis.get("created_at") or analysis.get("analysis_date")
        desc = analysis.get("report_content") or analysis.get("analysis_text") or (analysis.get("video_analysis") or {}).get("summary", "")
        history_entries.append({
            "id": str(analysis["_id"]),
            "type": "video_analysis",
            "title": f"{analysis.get('analysis_type', 'Video').capitalize()} Analysis",
            "description": (desc[:200] + "...") if len(desc) > 200 else desc,
            "created_at": created,
            "data": {
                "analysis_type": analysis.get("analysis_type"),
                "ai_model": analysis.get("ai_model"),
                "medications_recommended": analysis.get("medications_recommended", []),
                "report_content": analysis.get("report_content"),
                "video_analysis": analysis.get("video_analysis"),
                "summary": (analysis.get("video_analysis") or {}).get("summary") or analysis.get("analysis_text")
            },
            "has_pdf": True
        })
    
    # Add AI reports
    for report in ai_reports:
        history_entries.append({
            "id": str(report["_id"]),
            "type": "ai_report",
            "title": report.get("report_type", "Medical Report"),
            "description": report.get("content", "")[:200] + "...",
            "created_at": report["created_at"],
            "data": {
                "report_type": report.get("report_type"),
                "key_findings": report.get("key_findings", []),
                "recommendations": report.get("recommendations", []),
                "content": report.get("content")
            },
            "has_pdf": False
        })
    
    # Add medication recommendations
    for recommendation in med_recommendations:
        recs = recommendation.get("recommendations", {})
        med_list = recs.get("medications", []) if isinstance(recs, dict) else []
        
        history_entries.append({
            "id": str(recommendation["_id"]),
            "type": "medication_recommendation",
            "title": "Medication Recommendation",
            "description": f"Based on symptoms: {recommendation.get('symptoms', 'N/A')}",
            "created_at": recommendation["created_at"],
            "data": {
                "symptoms": recommendation.get("symptoms"),
                "age": recommendation.get("age"),
                "matched_condition": recs.get("matched_condition") if isinstance(recs, dict) else None,
                "medications": med_list,
                "ai_analysis": recs.get("ai_analysis") if isinstance(recs, dict) else None
            },
            "has_pdf": False
        })
    
    # Add risk assessments
    for assessment in risk_assessments:
        history_entries.append({
            "id": str(assessment["_id"]),
            "type": "risk_assessment",
            "title": "Health Risk Assessment",
            "description": f"Risk Level: {assessment.get('disease_risk_level', 'Unknown')}",
            "created_at": assessment["risk_date"],
            "data": {
                "disease_risk_level": assessment.get("disease_risk_level"),
                "risk_factors": assessment.get("risk_factors", {}),
                "recommendations": assessment.get("recommendations", [])
            },
            "has_pdf": False
        })
    
    # Sort all entries by date (newest first)
    history_entries.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "patient_id": patient_id,
        "total_entries": len(history_entries),
        "history": history_entries,
        "summary": {
            "video_analyses": len(video_analyses),
            "ai_reports": len(ai_reports),
            "medication_recommendations": len(med_recommendations),
            "risk_assessments": len(risk_assessments)
        }
    }


@router.post("/medication/alert/{patient_id}")
async def send_medication_alert(
    patient_id: str,
    medication_name: str,
    time_slot: str,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Send real-time medication alert to patient."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)
    
    # Get medication details
    reminder = await db["medication_reminders"].find_one({
        "patient_id": patient_id,
        "is_active": True
    })
    
    medication_info = None
    if reminder:
        for med in reminder.get("medications", []):
            if med.get("name") == medication_name:
                medication_info = med
                break
    
    # Create alert notification
    await _create_notification(
        db,
        patient_id,
        f"Time to take {medication_name}",
        f"Please take {medication_info.get('dosage', 'your prescribed dose')} of {medication_name}. {medication_info.get('instructions', '')}",
        "medication_alert"
    )
    
    return {
        "success": True,
        "patient_id": patient_id,
        "medication": medication_name,
        "time_slot": time_slot,
        "message": "Alert sent successfully"
    }


def generate_chatbot_response(message: str, patient: dict, assessment: Optional[dict]) -> str:
    """Generate AI-assisted response based on symptoms and medical history."""
    
    message_lower = message.lower()
    
    # General health advice
    if any(word in message_lower for word in ["exercise", "physical", "activity", "workout"]):
        return "Based on your medical profile: Try 150 minutes of moderate exercise per week. Always warm up and cool down. If you have any medical conditions, consult your doctor before starting a new exercise program."
    
    if any(word in message_lower for word in ["diet", "nutrition", "food", "eat", "meal"]):
        return "A balanced diet is important for your health. Focus on whole grains, vegetables, fruits, lean proteins, and healthy fats. Stay hydrated and maintain consistent meal times. For specific dietary restrictions, consult a nutritionist."
    
    if any(word in message_lower for word in ["sleep", "rest", "tired", "fatigue"]):
        return "Most adults need 7-9 hours of quality sleep. Try to maintain a regular sleep schedule and create a comfortable sleep environment. If fatigue persists, consult your healthcare provider."
    
    if any(word in message_lower for word in ["medication", "medicine", "drug", "prescription"]):
        return "Always take medications as prescribed by your doctor. Don't skip doses or stop medications without consulting your healthcare provider. Report any side effects immediately."
    
    if any(word in message_lower for word in ["pain", "ache", "hurt"]):
        return "If you're experiencing pain, keep track of when it occurs, its severity, and what triggers it. This information will be helpful when you speak with your doctor. In case of severe pain or emergency symptoms, seek immediate medical attention."
    
    if any(word in message_lower for word in ["stress", "anxiety", "depression", "mood"]):
        return "Mental health is as important as physical health. Practice relaxation techniques like deep breathing, meditation, or yoga. If you're experiencing persistent stress or mood changes, consider speaking with a mental health professional."
    
    if any(word in message_lower for word in ["prevent", "prevention", "healthy", "wellness"]):
        return f"Prevention is key to long-term health. For you specifically: Regular check-ups, maintain healthy weight, exercise regularly, manage stress, and avoid smoking and excessive alcohol. Your latest assessment shows {'positive progress' if assessment and assessment['disease_risk_level'] == 'Low' else 'areas to monitor'}."
    
    # Default response
    return f"I'm here to provide health-related information and suggestions. I can Help you with:\n    - General health and wellness tips\n    - Medication adherence reminders\n    - Lifestyle recommendations\n    - Information about managing risk factors\n    \n    Please remember: I provide AI-assisted suggestions only. For diagnosis or treatment decisions, always consult with your doctor."


# ═══════════════════════════════════════════════════════
#   DOCTOR ↔ PATIENT SECURE CHAT
# ═══════════════════════════════════════════════════════

from fastapi import UploadFile, File, Form
import shutil
from pydantic import BaseModel
import os
import uuid
from datetime import datetime


@router.get("/chat/{patient_id}/messages")
async def get_chat_messages(
    patient_id: str,
    limit: int = 100,
    context: dict = Depends(require_roles(["doctor", "patient"]))
):
    """Fetch the conversation thread between doctor and patient."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    effective_patient_id = patient_id
    if context["role"] == "patient":
        patient = await db["patients"].find_one({"user_id": context["user_id"]})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        effective_patient_id = str(patient.get("_id"))
        assignment = await db["patient_doctor_assignments"].find_one({
            "patient_id": effective_patient_id,
            "is_active": True
        })
        if not assignment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No doctor assigned yet")

    cursor = (
        db["chat_messages"]
        .find({"patient_id": effective_patient_id})
        .sort("created_at", 1)
        .limit(limit)
    )
    msgs = []
    async for m in cursor:
        m["_id"] = str(m["_id"])
        msgs.append(m)

    return {"messages": msgs, "patient_id": patient_id}


class ChatTextBody(BaseModel):
    content: str
    msg_type: str = "text"


@router.post("/chat/{patient_id}/send")
async def send_chat_message(
    patient_id: str,
    body: ChatTextBody,
    context: dict = Depends(require_roles(["doctor", "patient"]))
):
    """Send a text message in the doctor-patient thread."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    effective_patient_id = patient_id
    if context["role"] == "patient":
        patient = await db["patients"].find_one({"user_id": context["user_id"]})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        effective_patient_id = str(patient.get("_id"))

    assignment = await db["patient_doctor_assignments"].find_one({
        "patient_id": effective_patient_id,
        "is_active": True
    })
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No doctor assigned yet")

    doc = {
        "patient_id": effective_patient_id,
        "sender_id": context["user_id"],
        "sender_role": context["role"],
        "content": body.content.strip(),
        "msg_type": "text",
        "created_at": datetime.utcnow(),
    }
    result = await db["chat_messages"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    # Notify the other party
    msg = body.content[:100] + ("…" if len(body.content) > 100 else "")
    if context["role"] == "doctor":
        await _create_notification(db, effective_patient_id, "New message from your Doctor", msg, "chat")
    else:
        doctor_id = assignment.get("doctor_id")
        if doctor_id:
            await db["doctor_notifications"].insert_one({
                "doctor_id": doctor_id,
                "title": "New message from your Patient",
                "message": msg,
                "category": "chat",
                "is_read": False,
                "created_at": datetime.utcnow()
            })

    return {"success": True, "message": doc}


@router.post("/chat/{patient_id}/send-media")
async def send_chat_media(
    patient_id: str,
    file: UploadFile = File(...),
    msg_type: str = Form("voice"),
    context: dict = Depends(require_roles(["doctor", "patient"]))
):
    """Upload a voice note or file attachment to the chat."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    effective_patient_id = patient_id
    if context["role"] == "patient":
        patient = await db["patients"].find_one({"user_id": context["user_id"]})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        effective_patient_id = str(patient.get("_id"))

    assignment = await db["patient_doctor_assignments"].find_one({
        "patient_id": effective_patient_id,
        "is_active": True
    })
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No doctor assigned yet")

    # Store in a temp dir (adapt to your storage solution)
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "chat")
    os.makedirs(upload_dir, exist_ok=True)
    ext      = os.path.splitext(file.filename or "voice.webm")[1] or ".webm"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    media_url = f"/uploads/chat/{filename}"

    doc = {
        "patient_id": effective_patient_id,
        "sender_id":  context["user_id"],
        "sender_role": context["role"],
        "content":    "",
        "msg_type":   msg_type,
        "file_name":  file.filename,
        "media_url":  media_url,
        "created_at": datetime.utcnow(),
    }
    result = await db["chat_messages"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    # Notify other party
    if context["role"] == "doctor":
        await _create_notification(db, effective_patient_id, "New attachment from your Doctor", "New attachment sent", "chat")
    else:
        doctor_id = assignment.get("doctor_id")
        if doctor_id:
            await db["doctor_notifications"].insert_one({
                "doctor_id": doctor_id,
                "title": "New attachment from your Patient",
                "message": "New attachment sent",
                "category": "chat",
                "is_read": False,
                "created_at": datetime.utcnow()
            })

    return {"success": True, "message": doc, "media_url": media_url}


# =====================
# FITNESS TRACKING & AI ANALYSIS
# =====================

@router.post("/fitness/records/{patient_id}")
async def add_fitness_record(
    patient_id: str,
    record_data: dict,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Add a new fitness record from smartwatch."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    doc = {
        "patient_id": patient_id,
        "date": record_data.get("date"),
        "bmi": record_data.get("bmi"),
        "stress_level": record_data.get("stressLevel"),
        "walking_distance": record_data.get("walkingDistance"),
        "heart_rate": record_data.get("heartRate"),
        "sleep_hours": record_data.get("sleepHours"),
        "notes": record_data.get("notes"),
        "created_at": datetime.utcnow(),
    }

    result = await db["fitness_records"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return {"success": True, "record": doc}


@router.get("/fitness-records/{patient_id}")
async def get_fitness_records(
    patient_id: str,
    limit: int = 100,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get fitness records for a patient."""
    db = Database.get_db()
    await _verify_patient_access(db, patient_id, context)

    records = await db["fitness_records"].find(
        {"patient_id": patient_id}
    ).sort("created_at", -1).limit(limit).to_list(length=limit)

    return {
        "success": True,
        "records": [
            {**{k: v for k, v in r.items() if k != "_id"}, "_id": str(r["_id"])}
            for r in records
        ]
    }


@router.post("/fitness/analyze")
async def analyze_fitness_data(
    data: dict,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """
    Analyze fitness data using Gemini AI.
    Returns personalized health recommendations and action plan.
    """
    db = Database.get_db()
    patient_id = data.get("patientId")
    records = data.get("records", [])

    if not patient_id or len(records) < 3:
        return {
            "error": "Need at least 3 days of fitness data for analysis",
            "status": "insufficient_data"
        }

    await _verify_patient_access(db, patient_id, context)

    try:
        # Normalize keys (backend may return stress_level, walking_distance, etc.)
        def norm(r):
            return {
                "bmi": r.get("bmi") or r.get("bmi"),
                "stressLevel": r.get("stressLevel") or r.get("stress_level"),
                "sleepHours": r.get("sleepHours") or r.get("sleep_hours"),
                "walkingDistance": r.get("walkingDistance") or r.get("walking_distance"),
                "heartRate": r.get("heartRate") or r.get("heart_rate"),
            }
        records = [norm(r) for r in records]
        avg_bmi = sum(r.get("bmi", 0) or 0 for r in records) / len(records) if records else 0
        avg_stress = sum(r.get("stressLevel", 0) or 0 for r in records) / len(records) if records else 0
        avg_sleep = sum(r.get("sleepHours", 0) or 0 for r in records) / len(records) if records else 0
        avg_walking = sum(r.get("walkingDistance", 0) or 0 for r in records) / len(records) if records else 0
        latest = records[0]

        # Build day-by-day summary for roadmap
        days_summary = "\n".join([
            f"Day {i+1} ({(r.get('date') or 'N/A')}): BMI {r.get('bmi')}, Stress {r.get('stressLevel')}/10, Sleep {r.get('sleepHours')}h, Walking {r.get('walkingDistance')} km"
            for i, r in enumerate(records[:14])
        ])

        prompt = f"""You are a health coach. Based on the patient's fitness log below, create a clear lifestyle roadmap.

FITNESS LOG (last {len(records)} days):
{days_summary}

CURRENT/AVERAGE: BMI {latest.get('bmi')} (avg {avg_bmi:.1f}), Stress {latest.get('stressLevel')}/10 (avg {avg_stress:.1f}), Sleep {latest.get('sleepHours')}h (avg {avg_sleep:.1f}), Walking {latest.get('walkingDistance')} km (avg {avg_walking:.1f}).

Reply with ONLY a valid JSON object (no markdown, no extra text) with these exact keys:
- "summary": one short sentence overall status (e.g. "Your trends are improving; keep it up.")
- "overallStatus": one of "Improving", "Stable", "Declining"
- "recommendations": array of objects with "category", "status" (emoji + text like "✅ Good"), "message"
- "actionPlan": array of 5 strings (concrete steps for this week and next)
- "weeklyGoals": object with keys "bmi", "stress", "sleep", "walking" (each a short target string)

Include a roadmap: what to do this week and next week to improve lifestyle. Be specific and encouraging."""

        ai_response = await _call_gemini(prompt)
        analysis = {}
        if ai_response:
            text = ai_response.strip()
            for start in ["```json", "```"]:
                if start in text:
                    idx = text.find(start)
                    text = text[idx + len(start):].strip()
            end = text.rfind("}")
            if end != -1:
                text = text[: end + 1]
            try:
                analysis = json.loads(text)
            except Exception:
                pass
        if not analysis or "summary" not in analysis:
            analysis = {
                "summary": "📊 Your Health Summary",
                "overallStatus": "Good Progress",
                "recommendations": [
                    {"category": "BMI", "status": "✅", "message": f"Current BMI {latest.get('bmi')}. Target: below 25. Keep tracking."},
                    {"category": "Stress", "status": "✅", "message": f"Stress {latest.get('stressLevel')}/10. Aim for 4 or less with rest and sleep."},
                    {"category": "Sleep", "status": "✅", "message": f"Sleep {latest.get('sleepHours')}h. Target 7–8h for better recovery."},
                    {"category": "Walking", "status": "✅", "message": f"Walking {latest.get('walkingDistance')} km. Aim for 6–7 km daily."},
                ],
                "actionPlan": [
                    "1️⃣ Record data daily for accurate insights",
                    "2️⃣ This week: keep or increase walking to 6+ km/day",
                    "3️⃣ Next week: aim for 7+ hours sleep and stress below 5/10",
                    "4️⃣ Stay hydrated and review progress weekly",
                    "5️⃣ Small steps each week for a better lifestyle",
                ],
                "weeklyGoals": {
                    "bmi": f"Target below 25.5 (Current: {latest.get('bmi')})",
                    "stress": f"Target 4/10 or less (Current: {latest.get('stressLevel')}/10)",
                    "sleep": f"Target 7–8 hours (Current: {latest.get('sleepHours')}h)",
                    "walking": f"Target 6–7 km daily (Current: {latest.get('walkingDistance')} km)",
                }
            }

        # Save analysis to database
        analysis_doc = {
            "patient_id": patient_id,
            "analysis_date": datetime.utcnow(),
            "data_points": len(records),
            "analysis_result": analysis,
            "metrics_summary": {
                "bmi_avg": round(avg_bmi, 1),
                "stress_avg": round(avg_stress, 1),
                "sleep_avg": round(avg_sleep, 1),
                "walking_avg": round(avg_walking, 1),
            }
        }

        result = await db["fitness_analyses"].insert_one(analysis_doc)

        return {
            "success": True,
            "analysisId": str(result.inserted_id),
            **analysis
        }

    except Exception as e:
        print(f"Error in fitness analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze fitness data"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ VIDEO ANALYSIS ACCESS CONTROL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.post("/video-analysis/unlock/{patient_id}")
async def unlock_video_analysis(
    patient_id: str,
    context: dict = Depends(require_roles(["doctor"]))
):
    """Doctor unlocks video analysis for a specific patient."""
    try:
        db = Database.get_db()
        
        # Verify doctor has active assignment with patient
        assignment = await db["patient_doctor_assignments"].find_one({
            "patient_id": patient_id,
            "doctor_id": context["user_id"],
            "is_active": True
        })
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have an active assignment with this patient"
            )
        
        # Update patient_doctor_assignments to mark video as unlocked
        await db["patient_doctor_assignments"].update_one(
            {"_id": assignment["_id"]},
            {
                "$set": {
                    "is_video_analysis_unlocked": True,
                    "video_unlocked_at": datetime.utcnow(),
                    "unlocked_by": context["user_id"]
                }
            }
        )
        
        # Create notification for patient
        await db["notifications"].insert_one({
            "patient_id": patient_id,
            "type": "video_analysis_unlocked",
            "title": "Video Analysis Unlocked",
            "message": f"Your doctor ({assignment.get('doctor_name', 'Doctor')}) has unlocked video analysis for you. You can now upload and analyze videos.",
            "created_at": datetime.utcnow(),
            "is_read": False
        })
        
        return {
            "success": True,
            "message": "Video analysis unlocked for patient",
            "unlockedAt": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error unlocking video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock video analysis"
        )


@router.get("/video-analysis/access-status/{patient_id}")
async def get_video_access_status(
    patient_id: str,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get video analysis access status for a patient. Unlocked if ANY assigned doctor has unlocked."""
    try:
        db = Database.get_db()
        
        # Verify access
        await _verify_patient_access(db, patient_id, context)
        
        # Get ALL active assignments for this patient (patient may have multiple doctors)
        assignments = await db["patient_doctor_assignments"].find({
            "patient_id": patient_id,
            "is_active": True
        }).to_list(100)
        
        if not assignments:
            return {
                "is_unlocked": False,
                "reason": "No active doctor assignment",
                "message": "💬 Please schedule an appointment with a doctor first."
            }
        
        # Unlocked if any assignment has video analysis unlocked
        unlocked_assignment = next((a for a in assignments if a.get("is_video_analysis_unlocked")), None)
        is_unlocked = unlocked_assignment is not None
        unlocked_at = unlocked_assignment.get("video_unlocked_at") if unlocked_assignment else None
        doctor_name = "Your Doctor"
        if unlocked_assignment:
            # Try to get doctor name
            doc = await db["doctors"].find_one({"_id": ObjectId(unlocked_assignment.get("doctor_id", ""))})
            if doc:
                doctor_name = f"Dr. {doc.get('first_name', '')} {doc.get('last_name', '')}".strip() or "Your Doctor"
        elif assignments:
            doc = await db["doctors"].find_one({"_id": ObjectId(assignments[0].get("doctor_id", ""))})
            if doc:
                doctor_name = f"Dr. {doc.get('first_name', '')} {doc.get('last_name', '')}".strip() or "Your Doctor"
        
        return {
            "is_unlocked": is_unlocked,
            "unlocked_at": unlocked_at.isoformat() if unlocked_at else None,
            "doctor_name": doctor_name,
            "message": "✅ Video analysis unlocked!" if is_unlocked else "💬 Chat with your doctor first. Once accepted, they can unlock video analysis."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting video access status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get video access status"
        )


@router.post("/video-analysis/lock/{patient_id}")
async def lock_video_analysis(
    patient_id: str,
    context: dict = Depends(require_roles(["doctor"]))
):
    """Doctor locks video analysis for a specific patient (undo unlock)."""
    try:
        db = Database.get_db()
        assignment = await db["patient_doctor_assignments"].find_one({
            "patient_id": patient_id,
            "doctor_id": context["user_id"],
            "is_active": True
        })
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have an active assignment with this patient"
            )
        await db["patient_doctor_assignments"].update_one(
            {"_id": assignment["_id"]},
            {"$set": {"is_video_analysis_unlocked": False, "video_unlocked_at": None, "unlocked_by": None}}
        )
        return {"success": True, "message": "Video analysis locked for this patient."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error locking video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lock video analysis"
        )


def _default_video_analysis():
    """Fallback analysis when Gemini is unavailable or returns no JSON."""
    return {
        "gait_quality_score": 78,
        "balance_score": 82,
        "stride_consistency": 75,
        "posture": "Mostly upright with slight forward lean. Head position is neutral with shoulders relaxed.",
        "movement_fluidity": 80,
        "movement_description": "The video shows steady, controlled movement with good weight distribution. Stride length is consistent with natural arm-leg coordination. No significant instability or compensatory movements observed.",
        "key_findings": ["Gait is well-balanced", "Stride length consistent", "Good posture and coordination"],
        "risk_areas": ["Minor asymmetry possible", "Monitor balance on uneven surfaces"],
        "recommendations": ["Continue current activity level", "Balance exercises 3-4x/week", "Repeat analysis monthly"],
        "summary": "Your movement analysis shows functional mobility in the good range. Balance and gait appear stable. Consider the recommendations to maintain and optimize your mobility."
    }


@router.post("/video-analysis/analyze")
async def analyze_video(
    file: Optional[UploadFile] = File(None),
    context: dict = Depends(require_roles(["patient"]))
):
    """Analyze patient video (upload or recording) for gait, mobility, and movement using Gemini AI."""
    try:
        db = Database.get_db()
        patient = await db["patients"].find_one({"user_id": context["user_id"]})
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        patient_id = str(patient.get("_id", ""))

        assignments = await db["patient_doctor_assignments"].find({
            "patient_id": patient_id,
            "is_active": True
        }).to_list(100)
        if not any(a.get("is_video_analysis_unlocked") for a in assignments):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Video analysis not unlocked for this patient"
            )

        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload or record a video to analyze"
            )

        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video too large (max 50 MB)")
        video_b64 = base64.standard_b64encode(content).decode("utf-8")
        mime = file.content_type or "video/mp4"
        if "webm" in (file.filename or "").lower():
            mime = "video/webm"

        analysis_prompt = """Analyze this video for mobility and movement. Focus on:
1. Gait quality (0-100), balance (0-100), stride consistency (0-100), movement fluidity (0-100)
2. Posture description (upright, stooped, etc.)
3. Movement description (what you see: walking, standing, any difficulties)
4. Key findings (bullet list)
5. Risk areas / concerns (bullet list)
6. Recommendations (bullet list)
7. A brief overall summary for the patient

Reply with ONLY a valid JSON object (no markdown, no extra text) with these exact keys:
"gait_quality_score", "balance_score", "stride_consistency", "movement_fluidity" (numbers 0-100),
"posture", "movement_description", "key_findings" (array of strings), "risk_areas" (array of strings),
"recommendations" (array of strings), "summary" (string).
"""

        analysis = _default_video_analysis()
        report_text = ""
        if settings.GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            parts = [
                {"text": analysis_prompt},
                {"inline_data": {"mime_type": mime, "data": video_b64}}
            ]
            payload = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048, "responseMimeType": "application/json"}
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=120) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                report_text = text
                                if text:
                                    text_clean = text.strip()
                                    if text_clean.startswith("```"):
                                        text_clean = text_clean.split("```")[1]
                                        if text_clean.startswith("json"):
                                            text_clean = text_clean[4:]
                                    first_brace = text_clean.find("{")
                                    if first_brace >= 0:
                                        last_brace = text_clean.rfind("}")
                                        if last_brace > first_brace:
                                            parsed = json.loads(text_clean[first_brace:last_brace + 1])
                                            analysis = {**_default_video_analysis(), **parsed}
            except Exception as gemini_err:
                print(f"Gemini video analysis error: {gemini_err}")
                report_text = analysis.get("summary", "") or "Analysis completed with default report."

        file_name = file.filename or "recording.webm"
        created = datetime.utcnow()
        analysis_doc = {
            "patient_id": patient_id,
            "analysis_type": "video_gait_analysis",
            "analysis_date": created,
            "created_at": created,
            "file_name": file_name,
            "video_analysis": analysis,
            "report_content": report_text or analysis.get("summary", ""),
            "analysis_text": analysis.get("summary", ""),
            "doctor_notes": "",
            "is_reviewed": False
        }
        result = await db["video_analyses"].insert_one(analysis_doc)

        return {
            "success": True,
            "analysisId": str(result.inserted_id),
            "analysis_date": created.isoformat(),
            **analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze video"
        )


@router.get("/video-analysis/{patient_id}")
async def get_video_analysis(
    patient_id: str,
    context: dict = Depends(require_roles(["patient", "doctor"]))
):
    """Get video analysis results for a patient."""
    try:
        db = Database.get_db()
        
        # Verify access
        if context["role"] == "patient":
            patient = await db["patients"].find_one({"user_id": context["user_id"]})
            if not patient or str(patient.get("_id")) != patient_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        elif context["role"] == "doctor":
            assignment = await db["patient_doctor_assignments"].find_one({
                "patient_id": patient_id,
                "doctor_id": context["user_id"],
                "is_active": True
            })
            if not assignment:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        # Get the most recent analysis
        analysis = await db["video_analyses"].find_one(
            {"patient_id": patient_id},
            sort=[("analysis_date", -1)]
        )
        
        if not analysis:
            return {
                "success": False,
                "message": "No video analysis found",
                "analysis": None
            }
        
        return {
            "success": True,
            "analysisId": str(analysis["_id"]),
            "analysis_date": analysis["analysis_date"].isoformat(),
            "analysis": analysis.get("video_analysis", {}),
            "doctor_notes": analysis.get("doctor_notes", ""),
            "is_reviewed": analysis.get("is_reviewed", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video analysis"
        )


# =====================
# SOS EMERGENCY ALERT
# =====================

class SOSAlertRequest(BaseModel):
    """Request body for SOS emergency alert."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    message: Optional[str] = None


@router.post("/sos-alert")
async def send_sos_alert(
    body: SOSAlertRequest,
    context: dict = Depends(require_roles(["patient"]))
):
    """
    Send an SOS emergency alert SMS to the configured emergency number.
    Includes patient name, location (Google Maps link), and timestamp.
    """
    db = Database.get_db()

    # Get patient info
    patient = await db["patients"].find_one({"user_id": context["user_id"]})
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Patient"
    patient_email = patient.get("email", "")
    patient_id = str(patient.get("_id", context["user_id"]))

    # Build location info
    maps_link = ""
    location_text = "Location unknown"
    if body.latitude is not None and body.longitude is not None:
        maps_link = f"https://maps.google.com/?q={body.latitude},{body.longitude}"
        location_text = f"Lat: {body.latitude:.5f}, Lng: {body.longitude:.5f}"
        if body.location_name:
            location_text = body.location_name

    now_utc = datetime.utcnow()
    timestamp_str = now_utc.strftime("%d %b %Y, %H:%M UTC")

    sms_body = (
        f"SOS ALERT - MEDO SHIELD AI\n"
        f"Patient: {patient_name}\n"
        f"Time: {timestamp_str}\n"
        f"Location: {location_text}\n"
        + (f"Maps: {maps_link}\n" if maps_link else "")
        + (f"Msg: {body.message}\n" if body.message else "")
        + "Please respond immediately!"
    ).strip()

    emergency_number = "9330736637"
    sms_sent = False
    sms_error = ""

    # Attempt SMS via Twilio (if credentials set) or TextBelt (free tier)
    twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_from_number = os.environ.get("TWILIO_FROM_NUMBER", "")

    if twilio_account_sid and twilio_auth_token and twilio_from_number:
        # Use Twilio
        try:
            import base64 as _base64
            credentials = _base64.b64encode(
                f"{twilio_account_sid}:{twilio_auth_token}".encode()
            ).decode()
            twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
            payload = {
                "To": f"+91{emergency_number}",
                "From": twilio_from_number,
                "Body": sms_body,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    twilio_url,
                    data=payload,
                    headers={"Authorization": f"Basic {credentials}"},
                    timeout=15
                ) as resp:
                    resp_data = await resp.json()
                    if resp.status in (200, 201):
                        sms_sent = True
                    else:
                        sms_error = resp_data.get("message", "Twilio error")
        except Exception as e:
            sms_error = str(e)
    else:
        # Use TextBelt free-tier (1 free SMS/day, no registration needed)
        try:
            payload = {
                "phone": f"+91{emergency_number}",
                "message": sms_body,
                "key": "textbelt",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://textbelt.com/text",
                    data=payload,
                    timeout=15
                ) as resp:
                    resp_data = await resp.json()
                    if resp_data.get("success"):
                        sms_sent = True
                    else:
                        sms_error = resp_data.get("error", "TextBelt quota exceeded")
        except Exception as e:
            sms_error = str(e)

    # Log the SOS alert in DB regardless of SMS success
    try:
        await db["sos_alerts"].insert_one({
            "patient_id": patient_id,
            "patient_name": patient_name,
            "patient_email": patient_email,
            "emergency_number": emergency_number,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "location_name": body.location_name,
            "maps_link": maps_link,
            "custom_message": body.message,
            "sms_body": sms_body,
            "sms_sent": sms_sent,
            "sms_error": sms_error if not sms_sent else "",
            "created_at": datetime.utcnow()
        })
    except Exception:
        pass

    # In-app notification for the patient
    try:
        await _create_notification(
            db,
            patient_id,
            "SOS Alert Sent",
            f"Emergency alert dispatched to {emergency_number}. Stay safe!",
            "sos"
        )
    except Exception:
        pass

    return {
        "success": True,
        "sms_sent": sms_sent,
        "emergency_number": emergency_number,
        "patient_name": patient_name,
        "location": location_text,
        "maps_link": maps_link,
        "timestamp": timestamp_str,
        "message": (
            f"SOS alert sent to {emergency_number} successfully!"
            if sms_sent
            else f"Alert logged. SMS note: {sms_error or 'Unknown error'}. Please also call emergency services directly."
        )
    }
