# Deployment Guide - Autonomous Wall Finisher

## Overview
This guide covers deploying the FastAPI backend + static frontend for production use.

---

## Option 1: Docker Deployment (Recommended for Production)

### Step 1: Create Dockerfile for Backend
Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY trajectories.sqlite3 ./trajectories.sqlite3 2>/dev/null || true
COPY pytest.ini .

# Create directory for DB if it doesn't exist
RUN mkdir -p /app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./trajectories.sqlite3:/app/trajectories.sqlite3
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    restart: unless-stopped
```

### Step 3: Create nginx.conf for Frontend
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://backend:8000/health;
    }
}
```

### Step 4: Update frontend BASE_URL
In `frontend/app.js`, change:
```javascript
const BASE_URL = "http://localhost:8000";
```
to:
```javascript
const BASE_URL = window.location.origin; // Uses same origin as frontend
```

### Step 5: Deploy with Docker
```powershell
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Access at: http://localhost

---

## Option 2: Cloud Platform Deployment

### A. Render.com (Free Tier Available)

#### Backend (Web Service)
1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Configure:
   - **Name**: wall-finisher-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Add environment variable:
   - `PORT`: 10000 (Render assigns this)
6. Deploy

#### Frontend (Static Site)
1. Render → New Static Site
2. Connect repo
3. Configure:
   - **Name**: wall-finisher-ui
   - **Build Command**: (leave empty)
   - **Publish Directory**: `frontend`
4. Update `frontend/app.js`:
   ```javascript
   const BASE_URL = "https://wall-finisher-api.onrender.com";
   ```
5. Deploy

### B. Railway.app

1. Install Railway CLI:
   ```powershell
   npm install -g @railway/cli
   ```

2. Login and initialize:
   ```powershell
   railway login
   railway init
   ```

3. Create `railway.json`:
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE"
     }
   }
   ```

4. Deploy:
   ```powershell
   railway up
   ```

5. Frontend: Deploy to Vercel or Netlify (see below)

### C. Heroku

1. Create `Procfile`:
   ```
   web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

2. Create `runtime.txt`:
   ```
   python-3.11
   ```

3. Deploy:
   ```powershell
   heroku login
   heroku create wall-finisher-api
   git push heroku main
   ```

4. Frontend on Netlify:
   - Drag & drop `frontend` folder to [netlify.com](https://netlify.com)
   - Update BASE_URL to Heroku backend URL

---

## Option 3: VPS Deployment (DigitalOcean, Linode, AWS EC2)

### Step 1: Provision Server
- Ubuntu 22.04 LTS
- 1GB RAM minimum
- Open ports: 80, 443, 22

### Step 2: SSH and Setup
```bash
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv nginx supervisor git

# Create application user
adduser wallfinisher
su - wallfinisher
```

### Step 3: Deploy Application
```bash
# Clone repo
cd ~
git clone https://github.com/Anisha-Maan/Autonomous-wall-finisher.git
cd Autonomous-wall-finisher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Ctrl+C to stop
```

### Step 4: Configure Supervisor (Keep Backend Running)
Create `/etc/supervisor/conf.d/wallfinisher.conf`:
```ini
[program:wallfinisher]
command=/home/wallfinisher/Autonomous-wall-finisher/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
directory=/home/wallfinisher/Autonomous-wall-finisher
user=wallfinisher
autostart=true
autorestart=true
stderr_logfile=/var/log/wallfinisher.err.log
stdout_logfile=/var/log/wallfinisher.out.log
```

```bash
# Start service
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start wallfinisher
```

### Step 5: Configure Nginx
Create `/etc/nginx/sites-available/wallfinisher`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /home/wallfinisher/Autonomous-wall-finisher/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/wallfinisher /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Option 4: Serverless Deployment

### Vercel (Frontend + API Routes)

1. Install Vercel CLI:
   ```powershell
   npm i -g vercel
   ```

2. Create `vercel.json`:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "backend/main.py",
         "use": "@vercel/python"
       },
       {
         "src": "frontend/**",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "backend/main.py"
       },
       {
         "src": "/(.*)",
         "dest": "frontend/$1"
       }
     ]
   }
   ```

3. Deploy:
   ```powershell
   vercel --prod
   ```

---

## Production Considerations

### 1. Database
- **Current**: SQLite (single file)
- **For production**: Consider PostgreSQL or MySQL for better concurrency
- **Migration**: Update `backend/db.py` to use SQLAlchemy with PostgreSQL connection string

### 2. Environment Variables
Create `.env` file (don't commit to git):
```env
DATABASE_URL=sqlite:///./trajectories.sqlite3
ALLOWED_ORIGINS=https://yourdomain.com
SECRET_KEY=your-secret-key-here
```

Update `backend/main.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Security Checklist
- [ ] Remove `allow_origins=["*"]` and specify exact frontend domain
- [ ] Add rate limiting (use `slowapi` package)
- [ ] Add authentication if needed (JWT tokens)
- [ ] Use HTTPS (SSL certificate)
- [ ] Set proper CORS headers
- [ ] Add input validation and sanitization
- [ ] Use environment variables for secrets

### 4. Performance Optimization
```python
# Add to requirements.txt
gunicorn==21.2.0

# Run with Gunicorn instead of uvicorn for production
gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Update Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "backend.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 5. Monitoring & Logging
Add to `requirements.txt`:
```
sentry-sdk[fastapi]==1.40.0
prometheus-fastapi-instrumentator==6.1.0
```

In `backend/main.py`:
```python
import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator

# Sentry error tracking
sentry_sdk.init(dsn="your-sentry-dsn")

# Prometheus metrics
Instrumentator().instrument(app).expose(app)
```

---

## Quick Deploy Commands Summary

### Docker (Local or Server):
```powershell
docker-compose up -d
```

### Render.com:
- Push to GitHub → Connect on Render → Deploy

### Railway:
```powershell
railway up
```

### VPS:
```bash
git pull && supervisorctl restart wallfinisher
```

---

## Troubleshooting

### CORS Errors
- Ensure BASE_URL in frontend matches backend URL
- Check `allow_origins` in backend CORS middleware

### Database Locked
- SQLite doesn't handle high concurrency well
- Switch to PostgreSQL for production

### 502 Bad Gateway
- Check backend is running: `supervisorctl status`
- Check logs: `tail -f /var/log/wallfinisher.err.log`

### Static Files Not Loading
- Verify nginx configuration
- Check file permissions: `ls -la frontend/`

---

## Cost Estimates

| Platform | Backend | Frontend | Database | Total/Month |
|----------|---------|----------|----------|-------------|
| Render Free | Free | Free | SQLite | $0 |
| Railway | $5 | Free (Vercel) | $5 | $10 |
| DigitalOcean | $6 | Included | Included | $6 |
| AWS EC2 | $8-10 | S3 ($1) | RDS ($15) | $24-26 |

**Recommendation**: Start with Render.com free tier or Railway, then scale to VPS when needed.

---

## Next Steps After Deployment

1. Set up CI/CD (GitHub Actions for auto-deploy on push)
2. Configure backups for database
3. Add monitoring (Sentry, Datadog, or CloudWatch)
4. Set up alerts for downtime
5. Document API endpoints (add `/docs` route via FastAPI auto-docs)

---

**Need help?** Choose your deployment method and I can provide detailed setup for that specific option.
