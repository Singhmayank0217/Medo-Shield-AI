# NEURO-SHIELD AI - API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 🔐 Authentication Endpoints

### 1. Register Patient
Create a new patient account.

**Endpoint**: `POST /api/patients/register`

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "password": "SecurePassword123!",
  "user_id": "patient_20240219_001",
  "date_of_birth": "1960-05-15",
  "gender": "M",
  "medical_history": "No significant history"
}
```

**Response** (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `400 Bad Request`: Email already registered or invalid data
- `422 Unprocessable Entity`: Validation error

---

### 2. Login Patient
Authenticate and receive access token.

**Endpoint**: `POST /api/patients/login`

**Request Body**:
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account inactive

---

### 3. Get Current Patient Profile
Retrieve authenticated patient's profile.

**Endpoint**: `GET /api/patients/me`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "patient_20240219_001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "created_at": "2024-02-19T10:30:00Z"
}
```

---

## 📊 Patient Endpoints

### 4. Get Patient Trends
Retrieve 30-day trend data with risk classifications.

**Endpoint**: `GET /api/patients/trends`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "patient_id": "507f1f77bcf86cd799439011",
  "baseline_calibrated": true,
  "trend_data": [
    {
      "date": "2024-02-19T10:30:00Z",
      "gait_symmetry": 0.78,
      "tremor_frequency": 5.2,
      "bradykinesia_score": 0.45,
      "risk_level": "LOW"
    },
    {
      "date": "2024-02-18T09:15:00Z",
      "gait_symmetry": 0.75,
      "tremor_frequency": 5.5,
      "bradykinesia_score": 0.48,
      "risk_level": "LOW"
    }
  ],
  "current_status": {
    "last_session": "2024-02-19T10:30:00Z",
    "latest_risk_level": "LOW",
    "sessions_count": 12
  }
}
```

---

## 🎥 Analysis Endpoints

### 5. Upload Analysis Session
Process video and store pose features for risk assessment.

**Endpoint**: `POST /api/analysis/upload-session`

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "patient_id": "507f1f77bcf86cd799439011",
  "video_duration": 10.5,
  "frame_count": 315,
  "pose_frames": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "keypoints": [
        [0.512, 0.234, 0.001],
        [0.520, 0.210, 0.002],
        [0.530, 0.198, 0.001],
        [0.542, 0.187, 0.000],
        [0.555, 0.178, 0.001],
        [0.568, 0.172, 0.000],
        [0.582, 0.168, 0.001],
        [0.597, 0.165, 0.000],
        [0.612, 0.165, 0.001],
        [0.628, 0.168, 0.000],
        [0.644, 0.174, 0.001],
        [0.402, 0.245, 0.001],
        [0.598, 0.245, 0.001],
        [0.385, 0.398, 0.001],
        [0.615, 0.398, 0.001],
        [0.372, 0.552, 0.001],
        [0.628, 0.552, 0.001],
        [0.360, 0.698, 0.001],
        [0.640, 0.698, 0.001],
        [0.355, 0.745, 0.001],
        [0.645, 0.745, 0.001],
        [0.358, 0.775, 0.001],
        [0.642, 0.775, 0.001],
        [0.395, 0.825, 0.001],
        [0.605, 0.825, 0.001],
        [0.382, 0.898, 0.001],
        [0.618, 0.898, 0.001],
        [0.375, 0.965, 0.001],
        [0.625, 0.965, 0.001],
        [0.372, 0.992, 0.001],
        [0.628, 0.992, 0.001],
        [0.368, 0.998, 0.001],
        [0.632, 0.998, 0.001]
      ],
      "confidence": 0.87
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "patient_id": "507f1f77bcf86cd799439011",
  "features": {
    "stride_length": 0.65,
    "cadence": 95.3,
    "gait_symmetry": 0.78,
    "tremor_frequency": 5.2,
    "tremor_amplitude": 0.12,
    "bradykinesia_score": 0.45,
    "deviation_from_baseline": 1.2
  },
  "created_at": "2024-02-19T10:30:00Z",
  "risk_classification": "LOW"
}
```

**Keypoint Mapping** (33 landmarks):
```
Index  0: nose
Index  1: left_eye_inner
Index  2: left_eye
Index  3: left_eye_outer
Index  4: right_eye_inner
Index  5: right_eye
Index  6: right_eye_outer
Index  7: left_ear
Index  8: right_ear
Index  9: mouth_left
Index 10: mouth_right
Index 11: left_shoulder
Index 12: right_shoulder
Index 13: left_elbow
Index 14: right_elbow
Index 15: left_wrist
Index 16: right_wrist
Index 17: left_pinky
Index 18: right_pinky
Index 19: left_index
Index 20: right_index
Index 21: left_thumb
Index 22: right_thumb
Index 23: left_hip
Index 24: right_hip
Index 25: left_knee
Index 26: right_knee
Index 27: left_ankle
Index 28: right_ankle
Index 29: left_heel
Index 30: right_heel
Index 31: left_foot_index
Index 32: right_foot_index
```

---

### 6. Get Baseline Status
Check if patient baseline is calibrated and view baseline metrics.

**Endpoint**: `GET /api/analysis/baseline-status/{patient_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "is_calibrated": true,
  "session_count": 7,
  "required_sessions": 7,
  "baseline_metrics": {
    "stride_length_mean": 0.64,
    "stride_length_std": 0.02,
    "cadence_mean": 94.5,
    "cadence_std": 2.3,
    "gait_symmetry_mean": 0.77,
    "gait_symmetry_std": 0.03,
    "tremor_frequency_mean": 5.1,
    "tremor_amplitude_mean": 0.11,
    "bradykinesia_mean": 0.46,
    "bradykinesia_std": 0.05,
    "session_count": 7,
    "last_updated": "2024-02-19T10:30:00Z",
    "is_calibrated": true
  }
}
```

---

### 7. Get Risk History
Retrieve historical risk assessments for a patient.

**Endpoint**: `GET /api/analysis/risk-history/{patient_id}?limit=50`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `limit` (integer, default: 50): Maximum number of assessments to return

**Response** (200 OK):
```json
{
  "patient_id": "507f1f77bcf86cd799439011",
  "assessments": [
    {
      "id": "507f1f77bcf86cd799439012",
      "session_id": "507f1f77bcf86cd799439013",
      "risk_classification": "LOW",
      "risk_score": 1.2,
      "confidence": 0.95,
      "flagged": false,
      "created_at": "2024-02-19T10:30:00Z"
    },
    {
      "id": "507f1f77bcf86cd799439014",
      "session_id": "507f1f77bcf86cd799439015",
      "risk_classification": "LOW",
      "risk_score": 1.5,
      "confidence": 0.92,
      "flagged": false,
      "created_at": "2024-02-18T09:15:00Z"
    },
    {
      "id": "507f1f77bcf86cd799439016",
      "session_id": "507f1f77bcf86cd799439017",
      "risk_classification": "MEDIUM",
      "risk_score": 2.8,
      "confidence": 0.88,
      "flagged": true,
      "created_at": "2024-02-17T14:45:00Z"
    }
  ]
}
```

---

## 🏥 Health & Status Endpoints

### 8. Health Check
Verify API and database connectivity.

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-02-19T10:30:00Z"
}
```

---

### 9. API Info
Get API information and documentation links.

**Endpoint**: `GET /`

**Response** (200 OK):
```json
{
  "name": "NEURO-SHIELD AI",
  "version": "1.0.0",
  "description": "Privacy-first AI-powered longitudinal neurodegenerative monitoring platform",
  "status": "operational",
  "docs": "/docs",
  "health": "/health"
}
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

#### 403 Forbidden
```json
{
  "detail": "Not authorized to access this resource"
}
```

#### 404 Not Found
```json
{
  "detail": "Patient not found"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred"
}
```

---

## Rate Limiting

- **Default Limit**: 100 requests per minute per IP
- **Auth Endpoints**: 5 attempts per minute per IP (for security)
- **Headers**: 
  - `X-RateLimit-Limit`: Total allowed requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp of reset

---

## CORS Configuration

Allowed origins (configurable):
```
http://localhost:5173
https://yourdomain.com
```

Allowed methods: `GET, POST, PUT, DELETE, OPTIONS`

Allowed headers: `Content-Type, Authorization`

---

## Data Models

### Patient
```typescript
{
  _id: ObjectId,
  user_id: string (unique),
  first_name: string,
  last_name: string,
  email: string (unique),
  date_of_birth: string (ISO date),
  gender: string ("M" | "F" | "O"),
  medical_history: string (optional),
  hashed_password: string,
  is_active: boolean,
  created_at: datetime,
  updated_at: datetime
}
```

### Analysis Session
```typescript
{
  _id: ObjectId,
  patient_id: string,
  video_duration: float (seconds),
  frame_count: integer,
  pose_frames: [
    {
      frame_number: integer,
      timestamp: float,
      keypoints: [[x, y, z], ...33],
      confidence: float (0-1)
    }
  ],
  extracted_features: {
    stride_length: float | null,
    cadence: float | null,
    gait_symmetry: float (0-1),
    tremor_frequency: float | null,
    tremor_amplitude: float | null,
    bradykinesia_score: float (0-1),
    deviation_from_baseline: float | null
  },
  created_at: datetime,
  updated_at: datetime
}
```

### Risk Assessment
```typescript
{
  _id: ObjectId,
  patient_id: string,
  session_id: string,
  risk_score: {
    score: float (0-10),
    classification: "LOW" | "MEDIUM" | "HIGH" | "BASELINE_LEARNING",
    confidence: float (0-1),
    components: {
      gait_symmetry: float,
      bradykinesia: float,
      tremor_amplitude: float | null
    }
  },
  clinical_notes: string (optional),
  flagged_for_review: boolean,
  created_at: datetime
}
```

---

## Example Workflows

### Workflow 1: New Patient Registration & First Session

```bash
# 1. Register
curl -X POST http://localhost:8000/api/patients/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "user_id": "patient_20240219"
  }'

# Response includes access_token

# 2. Get Profile
curl -X GET http://localhost:8000/api/patients/me \
  -H "Authorization: Bearer <access_token>"

# 3. Upload First Session
curl -X POST http://localhost:8000/api/analysis/upload-session \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{ "patient_id": "...", "video_duration": 10, "frame_count": 300, "pose_frames": [...] }'

# 4. Check Baseline Status
curl -X GET http://localhost:8000/api/analysis/baseline-status/{patient_id} \
  -H "Authorization: Bearer <access_token>"
```

---

## Webhook Events (Future)

Planned webhook events for external integrations:
- `baseline.calibrated` - When patient baseline is ready
- `risk.high` - High-risk session detected
- `patient.created` - New patient registered
- `session.completed` - Analysis session finished

---

**Last Updated**: February 2024
**API Version**: 1.0.0
