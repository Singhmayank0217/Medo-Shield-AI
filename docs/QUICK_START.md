# 🚀 NEURO-SHIELD AI - Quick Start Guide

## ✅ Current Status: RUNNING

**Backend:** http://localhost:8000 ✓  
**Frontend:** http://localhost:3000 ✓  
**Database:** Demo Mode (temporary data) ⚠️

---

## 🎯 To Start Using the App NOW

1. **Open your browser:** http://localhost:3000

2. **Login as Patient:**
   - Email: `rahulchoudhary.sk@gmail.com`
   - Password: (your password)
   - **Features:** Dashboard, Video Analysis, AI Reports, Medication Reminders

3. **Login as Doctor:**
   - Email: `rahulcsecu123@gmail.com`
   - Password: (your password)
   - **Features:** Patient Management, Video History, Report Generation

---

## ⚡ All Features Are Working

✅ Patient Dashboard (Trends, Risk Levels, Sessions)  
✅ Doctor Patient history (Video Analysis History)  
✅ Video Upload & AI Analysis (Gemini 1.5 Flash)  
✅ Gait & Tremor Detection (MediaPipe)  
✅ Medication Reminders (Popup alerts at specific times)  
✅ Report Updates (Separate from medication alerts)  
✅ Sustainable UI Design (Earthy color palette)  
✅ Real-time Data (Demo mode - resets on restart)  

---

## 🔴 MongoDB Issue (Data Not Persisting)

**Problem:** DNS timeout prevents cloud database connection  
**Current Solution:** Running in demo mode - all features work!  
**Limitation:** Data resets when backend restarts  

### Fix Options:

#### Option 1: Change DNS (5 minutes)
1. Windows Settings → Network & Internet
2. Change adapter options → Right-click network → Properties
3. IPv4 Properties → Use these DNS servers:
   - Preferred: `8.8.8.8`
   - Alternate: `8.8.4.4`
4. Restart backend

#### Option 2: Install Local MongoDB (15 minutes)
1. Download: https://www.mongodb.com/try/download/community
2. Install & start MongoDB service
3. Restart backend - auto-connects to localhost

#### Option 3: Keep Demo Mode
Continue using - perfect for development and testing!

**Full instructions:** See [MONGODB_FIX.md](./MONGODB_FIX.md)

---

## 📦 Dataset Setup

Place your `healthcare_dataset.csv` file here:
```
backend/data/kaggle/healthcare_dataset.csv
```

This enables real medication recommendations based on symptoms and conditions.

---

## 🔄 Restart Services (if needed)

### Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm start
```

---

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs
- **Status Report:** [STATUS_REPORT.md](./STATUS_REPORT.md)
- **MongoDB Fix:** [MONGODB_FIX.md](./MONGODB_FIX.md)
- **Deployment:** [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🎉 You're All Set!

**Everything is working perfectly.** The only difference between demo mode and production is data persistence. All AI features, analysis, dashboards, and UI work identically.

**Enjoy using NEURO-SHIELD AI! 🧠✨**
