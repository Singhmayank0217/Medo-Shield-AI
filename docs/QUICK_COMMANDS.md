# NEURO-SHIELD AI - Quick Command Reference

## ⚡ Start Here (Copy & Paste)

### Option 1: Docker Compose (Recommended - Fastest)

```bash
# Change to project directory
cd "d:\VS Code\Working Codes\Web Projects\NEURO-SHIELD AI"

# Start all services
docker-compose up -d

# Wait 30 seconds, then open in browser
Start-Sleep -Seconds 30

# Open frontend
Start-Process "http://localhost:5173"
```

**Stop everything**:
```bash
docker-compose down
```

---

### Option 2: Local Development (Windows PowerShell)

#### Terminal 1: Backend

```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate
.\venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --port 8000

# Should show: "Uvicorn running on http://0.0.0.0:8000"
```

#### Terminal 2: Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev

# Should show: "Local:   http://localhost:5173/"
```

---

## 🧪 Quick Test Commands

### Test Account Creation

```powershell
# PowerShell command to register
$body = @{
    first_name = "Test"
    last_name = "Patient"
    email = "test.patient@neuroshield.ai"
    password = "TestPass123"
    date_of_birth = "1980-05-15"
    gender = "Male"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/patients/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Test Login

```powershell
$body = @{
    email = "test.patient@neuroshield.ai"
    password = "TestPass123"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/patients/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$token = ($response.Content | ConvertFrom-Json).access_token
echo "Token: $token"
```

### Test Get Profile

```powershell
# Replace YOUR_TOKEN with actual token from login
$token = "YOUR_TOKEN_HERE"

Invoke-WebRequest -Uri "http://localhost:8000/api/patients/me" `
    -Method GET `
    -Headers @{Authorization = "Bearer $token"}
```

---

## 📊 Check System Status

### Backend Health

```bash
# PowerShell
curl.exe http://localhost:8000/health

# View API docs
Start-Process "http://localhost:8000/docs"
```

### Frontend

```bash
# PowerShell
curl.exe http://localhost:5173
```

### Docker Status

```bash
# List running containers
docker ps

# View logs
docker logs neuro-shield-backend
docker logs neuro-shield-frontend

# View specific container
docker compose logs backend
docker compose logs frontend
```

---

## 🔧 Useful Commands

### Clean Everything

```bash
# Stop and remove all containers
docker-compose down -v

# Remove all images
docker image prune -a

# Clean Python cache
cd backend
Remove-Item -Recurse -Force __pycache__
Remove-Item -Recurse -Force .pytest_cache
Remove-Item -Recurse -Force venv
```

### Rebuild Docker Images

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Update Dependencies

```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Frontend
cd frontend
npm update
npm audit fix
```

### View Database

```bash
# Connect to MongoDB locally (if installed)
mongosh

# Or use MongoDB Atlas interface in browser
# https://cloud.mongodb.com
```

---

## 🚀 Development Workflow

### Adding New Endpoint

1. Create router function in `backend/app/routers/your_router.py`
2. Add schema in `backend/app/schemas.py`
3. Register in `backend/app/main.py`
4. Test with Swagger UI at `/docs`

### Adding New Frontend Page

1. Create file in `frontend/src/pages/YourPage.jsx`
2. Import in `frontend/src/App.jsx`
3. Add route in Routes
4. Import in navigation component

### Running Tests

```bash
# Backend (install pytest first)
cd backend
pip install pytest pytest-asyncio
pytest

# Frontend
cd frontend
npm test
```

---

## 🐛 Troubleshooting Commands

### Port Already in Use

```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000

# Kill process (replace PID)
Stop-Process -Id [PID] -Force

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Database Connection Failed

```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Or check MongoDB Atlas connection string
# Verify IP whitelist at mongodb.com/atlas
```

### Clear Frontend Cache

```bash
# Delete node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

### Backend Module Errors

```bash
# Activate venv
cd backend
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Documentation Links

| Document | Purpose |
|----------|---------|
| [STARTUP_GUIDE.md](STARTUP_GUIDE.md) | Complete startup instructions |
| [README.md](README.md) | Project overview |
| [SETUP.md](SETUP.md) | Development environment setup |
| [API_DOCS.md](API_DOCS.md) | API endpoint reference |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | What's been completed |

---

## 🎯 Common Workflows

### Develop Backend Feature

```bash
cd backend
.\venv\Scripts\activate
# Edit code
# Uvicorn reloads automatically
# Test at http://localhost:8000/docs
```

### Develop Frontend Feature

```bash
cd frontend
npm run dev
# Edit code
# Vite HMR reloads automatically
# View at http://localhost:5173
```

### Deploy to Production

```bash
# Create production build
cd frontend
npm run build
# Output in dist/ folder

# Push to GitHub
git add .
git commit -m "Production ready"
git push origin main

# Deploy to Vercel (frontend) and Render (backend)
# See DEPLOYMENT.md for details
```

---

## ✅ Daily Commands

```bash
# Start development
docker-compose up -d  # or manual terminals

# Check health
curl http://localhost:8000/health

# Access frontend
Start-Process "http://localhost:5173"

# View API docs
Start-Process "http://localhost:8000/docs"

# Create test user
# Use registration form or curl command above

# Stop everything
docker-compose down
```

---

## 📱 Technology Quick Links

| Tech | Purpose | Version |
|------|---------|---------|
| Python | Backend | 3.11 |
| FastAPI | API Framework | 0.104.1 |
| MongoDB | Database | 7.0 |
| React | Frontend | 18.2.0 |
| Node.js | Runtime | 18+ |
| Docker | Containers | Latest |
| Tailwind | Styling | 3.3.6 |
| Vite | Build Tool | 5.0.8 |

---

## 💡 Tips

1. **Keep two terminals open** - one for backend, one for frontend
2. **Use Swagger UI** (`/docs`) to test API endpoints
3. **Check logs** if something fails - they're very helpful
4. **Modify .env** to change database or port
5. **Git commit often** - helps track progress
6. **Use Ctrl+C** to stop servers gracefully

---

## 🎉 You're Ready!

Choose your startup method above and run the code. Everything is configured and ready to go.

**Most Important Command**:
```bash
cd "d:\VS Code\Working Codes\Web Projects\NEURO-SHIELD AI"
docker-compose up -d
```

Then visit: **http://localhost:5173** 🚀
