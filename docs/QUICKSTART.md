# NEURO-SHIELD AI - Quick Start Guide

## 60-Second Setup

### Option 1: Docker (Fastest)

```bash
# Clone and run
git clone https://github.com/yourusername/neuro-shield-ai.git
cd neuro-shield-ai
docker-compose up -d

# Access:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

---

## Project Structure at a Glance

```
neuro-shield-ai/
├── backend/                    # FastAPI + AI Engine
│   ├── app/
│   │   ├── ai_engine/         # MediaPipe, FFT, baseline learning
│   │   ├── routers/           # API endpoints
│   │   ├── main.py            # FastAPI app
│   │   └── database.py        # MongoDB config
│   └── requirements.txt
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── pages/             # Login, Dashboard, Analysis
│   │   ├── components/        # Navbar, BrainVisualization
│   │   ├── store/             # Zustand state
│   │   └── App.jsx
│   └── package.json
│
├── docker-compose.yml         # Multi-service orchestration
├── README.md                  # Full documentation
├── SETUP.md                   # Development setup
├── API_DOCS.md               # API reference
└── DEPLOYMENT.md             # Production deployment
```

---

## Key Features

### 1. Video Analysis
- Record 10-second video
- Extract 33 pose keypoints (MediaPipe)
- Calculate gait metrics
- Detect tremor via FFT
- Generate risk score

### 2. Personalized Baseline
- First 7 sessions create baseline
- Deviation-based risk classification
- Adaptive learning

### 3. 3D Visualization
- Interactive brain model (Three.js)
- Real-time animations
- Dashboard charts

### 4. Privacy-First
- No raw video storage
- Only numerical features saved
- Secure JWT authentication

---

## API Quickstart

### Register & Login

```bash
# Register
curl -X POST http://localhost:8000/api/patients/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name":"John","last_name":"Doe",
    "email":"john@test.com","password":"Test123!",
    "user_id":"patient_001"
  }'

# Login
curl -X POST http://localhost:8000/api/patients/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@test.com","password":"Test123!"}'
```

### Upload Analysis

```bash
curl -X POST http://localhost:8000/api/analysis/upload-session \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id":"507f1f77bcf86cd799439011",
    "video_duration":10.5,
    "frame_count":315,
    "pose_frames":[...]
  }'
```

**Full API docs**: http://localhost:8000/docs

---

## File Modifications

### Backend Changes
- **AI Pipeline**: Edit `backend/app/ai_engine/` modules
- **API Endpoints**: Edit `backend/app/routers/` files
- **Database**: Edit `backend/app/database.py` for indexes/config
- **Auth**: Edit `backend/app/auth.py` for security rules

### Frontend Changes
- **Pages**: Edit `frontend/src/pages/` for layouts
- **Components**: Edit `frontend/src/components/` for reusables
- **State**: Edit `frontend/src/store/store.js` for global state
- **Styling**: Edit `frontend/tailwind.config.js` for theme colors

### Configuration
- **Backend env**: `backend/.env`
- **Frontend env**: `frontend/.env`
- **Docker**: `docker-compose.yml`
- **Nginx**: `nginx.conf`

---

## Common Tasks

### Add New API Endpoint

1. Create route in `backend/app/routers/`
2. Add endpoint function with FastAPI decorators
3. Add Pydantic models in `backend/app/models.py`
4. Include router in `backend/app/main.py`

### Add Frontend Page

1. Create component in `frontend/src/pages/`
2. Import in `frontend/src/App.jsx`
3. Add route in Router
4. Update Navbar with link

### Connect to MongoDB Atlas

1. Get connection string from MongoDB Atlas dashboard
2. Add to `.env`: `MONGODB_URL=mongodb+srv://user:pass@cluster...`
3. Restart backend

### Deploy to Production

1. Follow `DEPLOYMENT.md`
2. Set up Render account
3. Set up Vercel account
4. Deploy backend to Render
5. Deploy frontend to Vercel

---

## Troubleshooting

### Backend Issues

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `uvicorn app.main:app --port 8001` |
| MongoDB connection fails | Check `MONGODB_URL` in `.env` |
| Circular imports | Reorganize imports or use TYPE_CHECKING |
| Async errors | Ensure all DB calls use `await` |

### Frontend Issues

| Issue | Solution |
|-------|----------|
| API returns 404 | Check `VITE_API_URL` environment variable |
| Three.js not rendering | Clear cache, restart dev server |
| Styles not applying | Run `npm run build`, restart dev |
| State not updating | Check Zustand store in browser DevTools |

### Docker Issues

| Issue | Solution |
|-------|----------|
| Services won't start | `docker-compose down -v && docker-compose up` |
| Port conflicts | Change ports in `docker-compose.yml` |
| Memory issues | Increase Docker memory in settings |

---

## Performance Tips

### Backend
- Add caching for frequent queries
- Create MongoDB indexes
- Use connection pooling
- Profile with APM tools

### Frontend
- Code-split large components
- Lazy-load routes
- Optimize images (WebP)
- Monitor bundle size

### Database
- Run index setup on startup (done)
- Monitor slow queries
- Archive old data periodically

---

## Security Checklist

- [ ] Change `SECRET_KEY` before production
- [ ] Set `DEBUG=False` in production
- [ ] Use HTTPS everywhere
- [ ] Validate all inputs (Pydantic does this)
- [ ] Enable CORS only for your domain
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Set secure password requirements

---

## Testing

### Backend Unit Tests
```bash
cd backend
pip install pytest
pytest tests/ -v
```

### Frontend Component Tests
```bash
cd frontend
npm install --save-dev @testing-library/react
npm test
```

### API Integration Tests
```bash
# Use Postman or curl to test endpoints
# Or create Python script with requests library
```

---

## Environment Variables Cheat Sheet

### Backend (Required)
```
MONGODB_URL=mongodb://localhost:27017/neuro_shield
SECRET_KEY=your-secret-key-min-32-chars
```

### Backend (Optional)
```
DEBUG=False
ENVIRONMENT=production
API_PORT=8000
FFT_SAMPLE_RATE=30
BASELINE_SESSIONS=7
```

### Frontend (Optional)
```
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=NEURO-SHIELD AI
```

---

## Useful Commands

```bash
# Backend
python -m venv venv              # Create virtual env
source venv/bin/activate        # Activate (macOS/Linux)
pip install -r requirements.txt # Install dependencies
uvicorn app.main:app --reload   # Run with hot reload
pip freeze > requirements.txt   # Update requirements

# Frontend
npm install                      # Install dependencies
npm run dev                      # Start dev server
npm run build                    # Production build
npm run preview                  # Preview build
npm run lint                     # Lint code

# Docker
docker-compose up -d             # Start services
docker-compose logs -f           # View logs
docker-compose down              # Stop services
docker-compose exec backend bash # Shell in container

# Git
git status                       # Check status
git add .                        # Stage changes
git commit -m "message"          # Commit
git push origin branch-name      # Push to remote
```

---

## Documentation Map

| Document | Purpose |
|----------|---------|
| README.md | Full project overview & features |
| SETUP.md | Development environment setup |
| QUICKSTART.md | This file - quick reference |
| API_DOCS.md | Complete API documentation |
| DEPLOYMENT.md | Production deployment guide |

---

## Next Steps

1. **Quick Start**: Follow "60-Second Setup" above
2. **Explore**: Visit http://localhost:5173 and http://localhost:8000/docs
3. **Register**: Create test patient account
4. **Test**: Record video and analyze
5. **Develop**: Modify code and test locally
6. **Deploy**: Follow DEPLOYMENT.md for production

---

## Support Resources

- GitHub Issues: Report bugs or request features
- API Documentation: http://localhost:8000/docs (interactive)
- Code Comments: Extensive comments in source files
- Examples: See `API_DOCS.md` for request/response examples

---

**Quick Start Guide Version**: 1.0
**Last Updated**: February 2024
**Status**: Production Ready
