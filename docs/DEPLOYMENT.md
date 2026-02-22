# NEURO-SHIELD AI - Deployment Guide

## Quick Start (Local Docker Compose)

### Prerequisites
- Docker Desktop or Docker Engine
- Docker Compose

### Steps

```bash
# 1. Clone repository
git clone https://github.com/yourusername/neuro-shield-ai.git
cd neuro-shield-ai

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 4. Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MongoDB: localhost:27017 (admin:neuroshield2024)
```

### Stop Services
```bash
docker-compose down
```

---

## Production Deployment

### Architecture

```
┌─────────────────────────────────────┐
│     Vercel (Frontend)               │
│  - React App                        │
│  - Static Site Generation           │
│  - Automatic SSL/TLS                │
│  - CDN Distribution                 │
└────────────┬────────────────────────┘
             │ HTTPS
┌────────────┴────────────────────────┐
│     Render (Backend API)            │
│  - FastAPI + Uvicorn                │
│  - Auto-scaling                     │
│  - Environment Variables            │
│  - Health Checks                    │
└────────────┬────────────────────────┘
             │
┌────────────┴────────────────────────┐
│  MongoDB Atlas (Database)           │
│  - Cloud-hosted                     │
│  - Automated backups                │
│  - Replica Sets                     │
└─────────────────────────────────────┘
```

---

## 1. MongoDB Atlas Setup

### Create Database

1. Go to [mongodb.com/cloud](https://www.mongodb.com/cloud/atlas)
2. Sign up for free tier account
3. Create a new cluster (AWS, region: us-east-1)
4. Wait for cluster to be ready (5-10 minutes)
5. Create database user:
   - Username: `neuro_admin`
   - Password: (generate secure password)
   - Save credentials

### Network Access

1. Go to "Security" → "Network Access"
2. Click "Add IP Address"
3. Select "Allow access from anywhere" (for production, restrict to your IP)
4. Click "Confirm"

### Connection String

1. Click "Connect" on cluster
2. Choose "Connect your application"
3. Select "Python" driver
4. Copy connection string
5. Replace `<username>`, `<password>`, `<database>`

Example:
```
mongodb+srv://neuro_admin:SecurePassword123@cluster0.abc.mongodb.net/neuro_shield?retryWrites=true&w=majority
```

---

## 2. Backend Deployment on Render

### Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up (free tier available)
3. Connect GitHub account

### Deploy Backend

1. Click "New+" → "Web Service"
2. Select your GitHub repository
3. Configure:
   - **Name**: `neuro-shield-backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - **Region**: (closest to users)

### Environment Variables

Add in Render dashboard:

```
MONGODB_URL=mongodb+srv://neuro_admin:PASSWORD@cluster0.abc.mongodb.net/neuro_shield?retryWrites=true&w=majority
MONGODB_DB=neuro_shield
SECRET_KEY=your-very-secret-key-min-32-chars-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://yourdomain.vercel.app
FFT_SAMPLE_RATE=30
BASELINE_SESSIONS=7
DEVIATION_THRESHOLD=2.5
```

### Deploy

1. Click "Create Web Service"
2. Render auto-deploys on GitHub push
3. Monitor deployment in dashboard
4. Access API at `https://neuro-shield-backend.onrender.com`

---

## 3. Frontend Deployment on Vercel

### Setup

1. Go to [vercel.com](https://vercel.com)
2. Sign up (GitHub integration)
3. Click "Import Project"
4. Select your GitHub repository
5. Configure:
   - **Framework**: Vite
   - **Root Directory**: `./frontend`

### Environment Variables

Add in Vercel dashboard:

```
VITE_API_URL=https://neuro-shield-backend.onrender.com
VITE_APP_NAME=NEURO-SHIELD AI
VITE_APP_VERSION=1.0.0
```

### Deploy

1. Click "Deploy"
2. Vercel auto-deploys on GitHub push
3. Access app at auto-generated URL
4. (Optional) Connect custom domain

---

## 4. Domain Setup

### Connect Custom Domain

#### For Vercel Frontend
1. In Vercel dashboard → Settings → Domains
2. Enter domain (e.g., `app.neuro-shield.com`)
3. Update DNS records:
   ```
   Type: CNAME
   Name: app
   Value: cname.vercel.com
   ```
4. Wait for DNS propagation (up to 48 hours)

#### For Render Backend API
1. In Render dashboard → Environment
2. Add custom domain (e.g., `api.neuro-shield.com`)
3. Update DNS records:
   ```
   Type: CNAME
   Name: api
   Value: onrender.com
   ```

---

## 5. SSL/TLS Certificates

### Automatic (Recommended)
- **Vercel**: Automatic free SSL
- **Render**: Automatic free SSL via Let's Encrypt
- **MongoDB Atlas**: Always HTTPS

### Manual (if needed)
Use AWS ACM or Let's Encrypt certbot

---

## 6. Monitoring & Logging

### Render Logs
```bash
# View logs in Render dashboard
# Settings → Logs
```

### Vercel Analytics
```bash
# Automatic Web Analytics in Vercel dashboard
```

### MongoDB Atlas Monitoring
- Go to "Monitoring" in Atlas dashboard
- View database performance metrics
- Set up alerts for high CPU/memory

---

## 7. Backup & Recovery

### MongoDB Atlas Automatic Backups
- Enabled by default (daily snapshots)
- Retained for 7-35 days
- Configurable in cluster settings

### Manual Backup
```bash
# Export data locally
mongodump --uri "mongodb+srv://neuro_admin:PASSWORD@cluster0.abc.mongodb.net/neuro_shield"

# Restore
mongorestore --uri "mongodb+srv://neuro_admin:PASSWORD@cluster0.abc.mongodb.net/neuro_shield" ./dump
```

---

## 8. Performance Optimization

### Frontend (Vercel)

```javascript
// vercel.json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "env": {
    "VITE_API_URL": "@vite_api_url"
  }
}
```

### Backend (Render)

- Use `gunicorn` with multiple workers:
```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

- Enable caching:
```python
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend
```

### Database (MongoDB)

- Create indexes (done automatically on startup)
- Monitor slow queries in Atlas dashboard
- Use connection pooling

---

## 9. Security Best Practices

### Secrets Management
- Never commit `.env` files
- Use environment variables for all secrets
- Rotate `SECRET_KEY` periodically

### Rate Limiting
```python
# Add to FastAPI app
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### CORS Configuration
```python
# Only allow your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### HTTPS Enforcement
- Both Vercel and Render enforce HTTPS
- Add security headers:
```
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

---

## 10. CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy NEURO-SHIELD

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Lint backend
        run: cd backend && flake8 app/
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: cd frontend && npm install
      
      - name: Build frontend
        run: cd frontend && npm run build
        env:
          VITE_API_URL: https://api.neuro-shield.com

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_API_KEY }}
      
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          vercel --prod
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
```

---

## 11. Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - MongoDB connection string wrong
# - Port already in use
# - Missing environment variables
```

### Frontend Can't Connect to Backend
```bash
# Check CORS headers in browser DevTools
# Verify VITE_API_URL environment variable
# Ensure backend is running and accessible
```

### High Database Latency
```bash
# Check MongoDB Atlas metrics
# Add database indexes (done on startup)
# Consider upgrading cluster tier
```

### SSL Certificate Issues
- Vercel/Render handle automatically
- If custom domain issues, check DNS propagation

---

## 12. Scaling Strategy

### Vertical Scaling
- Render: Increase instance tier (Pro, Business, Premium)
- MongoDB: Increase server size

### Horizontal Scaling
- Render: Enable auto-scaling (Pro plan+)
- Frontend: Vercel handles automatically with CDN

### Load Balancing
- Vercel: Automatic (multi-region)
- Render: Use multiple instances + load balancer

---

## Cost Estimation

### Free Tier (Development)
- Vercel: 1 deployment, 100GB bandwidth
- Render: 750 hours/month
- MongoDB: 512MB storage, shared cluster

### Production Tier (Recommended)
- Vercel: Pro ($20/month)
- Render: Pro ($7+/month per dyno)
- MongoDB: M10 ($57/month)

**Total**: ~$100-150/month for full production setup

---

## Next Steps

1. Create accounts on all platforms
2. Set up MongoDB Atlas cluster
3. Deploy backend to Render
4. Deploy frontend to Vercel
5. Connect custom domain
6. Monitor logs and performance
7. Set up automated backups
8. Enable monitoring and alerts

---

**Deployment Guide Version**: 1.0
**Last Updated**: February 2024
