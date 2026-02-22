# NEURO-SHIELD AI - Development Setup Guide

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 2GB free
- **Internet**: Required for dependencies and MongoDB Atlas

### Required Software

#### 1. Git
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Windows
# Download from https://git-scm.com/download/win
```

#### 2. Python 3.11+
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# Windows
# Download from https://www.python.org/downloads/
```

#### 3. Node.js 18+
```bash
# macOS
brew install node@18

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from https://nodejs.org/
```

#### 4. MongoDB (Local - Optional)
```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community@7.0

# Ubuntu
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
sudo apt-get install -y mongodb-org

# Windows
# Download from https://www.mongodb.com/try/download/community
```

#### 5. Docker (Optional - for containerized development)
```bash
# macOS/Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop

# Ubuntu
sudo apt-get install docker.io docker-compose
```

---

## Project Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/neuro-shield-ai.git
cd neuro-shield-ai
```

---

## Backend Development

### Setup Backend Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# For local development, you can use:
MONGODB_URL=mongodb://localhost:27017/neuro_shield
# or MongoDB Atlas:
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/neuro_shield
```

### Run Backend Locally

```bash
# From backend/ directory with virtual environment activated

# Run with automatic reload
uvicorn app.main:app --reload --port 8000

# Run without reload
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs` (Swagger UI)

Alternative docs: `http://localhost:8000/redoc` (ReDoc)

### Backend Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py              # MongoDB connection & config
│   ├── auth.py                  # JWT authentication logic
│   ├── models.py                # Pydantic data models
│   ├── ai_engine/               # AI/ML modules
│   │   ├── __init__.py
│   │   ├── pose.py              # MediaPipe pose extraction
│   │   ├── gait_analysis.py     # Gait metrics calculation
│   │   ├── tremor_analysis.py   # FFT tremor detection
│   │   └── baseline.py          # Baseline learning algorithm
│   └── routers/                 # API endpoints
│       ├── __init__.py
│       ├── patients.py          # Patient auth/management
│       └── analysis.py          # Analysis/risk assessment
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container image
├── .env                         # Environment variables
└── .env.example                 # Example env file
```

### Testing Backend

```bash
# (Optional) Install testing dependencies
pip install pytest pytest-asyncio pytest-cov

# Create tests directory
mkdir tests

# Run tests
pytest tests/ -v
```

### Common Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Ensure you're running from the project root with the virtual environment activated

**Issue**: `Cannot connect to MongoDB`
- **Solution**: Check `MONGODB_URL` in `.env` and ensure MongoDB is running locally or accessible remotely

**Issue**: `Port 8000 already in use`
- **Solution**: `uvicorn app.main:app --reload --port 8001` (use different port)

---

## Frontend Development

### Setup Frontend Environment

```bash
cd frontend

# Install dependencies
npm install

# Verify Node version
node --version  # Should be v18+
npm --version   # Should be v9+
```

### Configure Environment Variables

```bash
# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=NEURO-SHIELD AI
VITE_APP_VERSION=1.0.0
EOF
```

### Run Frontend Locally

```bash
# From frontend/ directory

# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

Frontend will be available at: `http://localhost:5173`

### Frontend Project Structure

```
frontend/
├── src/
│   ├── components/              # Reusable React components
│   │   ├── Navbar.jsx
│   │   └── BrainVisualization.jsx
│   ├── pages/                   # Page components
│   │   ├── Home.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   └── Analysis.jsx
│   ├── services/                # API communication
│   │   └── api.js               # Axios instance & methods
│   ├── store/                   # State management
│   │   └── store.js             # Zustand stores
│   ├── App.jsx                  # Main app component
│   ├── main.jsx                 # Vite entry point
│   └── index.css                # Global styles
├── index.html                   # HTML template
├── package.json                 # npm dependencies
├── vite.config.js               # Vite configuration
├── tailwind.config.js           # Tailwind CSS config
├── postcss.config.js            # PostCSS config
└── .env                         # Environment variables
```

### Frontend Development Tips

#### Hot Module Replacement (HMR)
- Changes to `.jsx` files automatically refresh in browser
- No need to manually reload

#### Debugging
- Open browser DevTools (F12)
- React DevTools browser extension recommended
- Zustand DevTools for state management

#### Performance
- Use React DevTools Profiler to identify slow components
- Check Network tab for API call performance
- Lighthouse audit: `npm run build` then test

### Common Frontend Issues

**Issue**: `Cannot GET /`
- **Solution**: Ensure Vite dev server is running (`npm run dev`)

**Issue**: `API calls return 404`
- **Solution**: Verify `VITE_API_URL` points to running backend

**Issue**: `Three.js not rendering`
- **Solution**: Clear browser cache, restart dev server

---

## Database Setup

### Option A: Local MongoDB

#### macOS
```bash
# Start MongoDB service
brew services start mongodb-community

# Stop MongoDB
brew services stop mongodb-community

# View logs
tail -f /usr/local/var/log/mongodb/mongo.log
```

#### Ubuntu/Linux
```bash
# Start MongoDB
sudo systemctl start mongod

# Check status
sudo systemctl status mongod

# Stop MongoDB
sudo systemctl stop mongod
```

#### Using MongoDB Compass (GUI)
1. Download MongoDB Compass: https://www.mongodb.com/try/download/compass
2. Connect to `mongodb://localhost:27017`
3. Create database: `neuro_shield`
4. Browse and manage collections visually

### Option B: MongoDB Atlas Cloud

1. Sign up: https://www.mongodb.com/cloud/atlas
2. Create free cluster (AWS, us-east-1 region)
3. Create database user
4. Whitelist your IP
5. Copy connection string: `mongodb+srv://username:password@cluster.mongodb.net/database`
6. Add to `.env` as `MONGODB_URL`

---

## Running Full Stack Locally

### Using Terminal Tabs/Panes

```bash
# Tab 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Tab 2: Frontend
cd frontend
npm run dev

# Tab 3: MongoDB (if using local)
# macOS
brew services start mongodb-community
# or manually: mongod

# Application is now running:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

### Using Docker Compose

```bash
# From project root
docker-compose up

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Development Workflow

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test locally

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add amazing feature for user authentication"

# Push to remote
git push origin feature/amazing-feature

# Create Pull Request on GitHub
```

### Code Style & Linting

#### Backend (Python)
```bash
# Format code
pip install black
black app/

# Lint code
pip install flake8
flake8 app/

# Type checking
pip install mypy
mypy app/
```

#### Frontend (JavaScript)
```bash
# Format code
npm run lint

# Fix automatically
npm run lint -- --fix

# Or use Prettier
npm install --save-dev prettier
npx prettier --write src/
```

### Testing Workflow

```bash
# Backend
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm test
```

---

## API Testing

### Using curl

```bash
# Register patient
curl -X POST http://localhost:8000/api/patients/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@test.com",
    "password": "TestPass123!",
    "user_id": "test_patient_001"
  }'

# Login
curl -X POST http://localhost:8000/api/patients/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@test.com",
    "password": "TestPass123!"
  }'

# Get current patient (replace with actual token)
curl -X GET http://localhost:8000/api/patients/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using Postman

1. Download Postman: https://www.postman.com/downloads/
2. Import collection from `API_DOCS.md`
3. Set variables for `BASE_URL` and `TOKEN`
4. Test endpoints interactively

### Using API Documentation

1. Navigate to `http://localhost:8000/docs`
2. Interactive Swagger UI with try-it-out feature
3. Automatically generated from FastAPI code

---

## Debugging Tips

### Backend Debugging

```python
# Add debug prints
print(f"[DEBUG] Variable value: {my_var}")

# Use Python debugger
import pdb
pdb.set_trace()  # Execution pauses here

# Or use VS Code debugger with launch config
```

### Frontend Debugging

```javascript
// Console logging
console.log("Debug:", variable);
console.error("Error:", error);

// Debugger statement
debugger;  // Pauses in browser DevTools

// React DevTools inspection
// Install React DevTools extension
```

### Database Debugging

```bash
# MongoDB CLI
mongosh

# List databases
show databases

# Use database
use neuro_shield

# List collections
show collections

# View documents
db.patients.find()
db.patients.findOne()
```

---

## Useful Commands Reference

### Backend
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install new dependency
pip install package_name
pip freeze > requirements.txt

# Run migrations (when available)
python -m alembic upgrade head

# Run with specific port
uvicorn app.main:app --port 8001
```

### Frontend
```bash
# Install new dependency
npm install package_name

# Remove dependency
npm uninstall package_name

# Update dependencies
npm update

# Clear cache
npm cache clean --force

# Install exact versions from lock file
npm ci
```

### Docker
```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes (careful!)
docker-compose down -v
```

---

## Environment Variables Reference

### Backend Required
- `MONGODB_URL`: MongoDB connection string
- `MONGODB_DB`: Database name
- `SECRET_KEY`: JWT signing key (min 32 chars)

### Backend Optional (have defaults)
- `API_HOST`: Default 0.0.0.0
- `API_PORT`: Default 8000
- `DEBUG`: Default False
- `ENVIRONMENT`: Default production

### Frontend Required
- `VITE_API_URL`: Backend API base URL

---

## Performance Optimization

### Backend
```python
# Add caching
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

# Add connection pooling
motor_client = AsyncClient(
    MONGODB_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000
)
```

### Frontend
```javascript
// Code splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'))

// Image optimization
import { WebPImage } from '@react-three/drei'

// Bundle analysis
npm install --save-dev webpack-bundle-analyzer
```

---

## Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev
- **MongoDB Docs**: https://docs.mongodb.com/
- **Three.js Docs**: https://threejs.org/docs/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Zustand**: https://github.com/pmndrs/zustand

---

## Getting Help

- Check existing issues on GitHub
- Create new GitHub issue with:
  - Detailed error message
  - Steps to reproduce
  - System info (OS, Node version, Python version)
  - Relevant code snippets

---

**Setup Guide Version**: 1.0
**Last Updated**: February 2024
