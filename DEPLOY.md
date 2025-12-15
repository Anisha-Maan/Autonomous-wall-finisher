# Quick Deployment Guide

## Fastest Option: Docker (5 minutes)

### Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Deploy in 3 Commands
```powershell
# 1. Build and start containers
docker-compose up -d

# 2. Check logs
docker-compose logs -f

# 3. Open browser
# Navigate to: http://localhost
```

**That's it!** The application is now running.

### Stop/Remove
```powershell
docker-compose down
```

---

## Free Cloud Deployment: Render.com (10 minutes)

### Backend
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → Sign up/Login
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - **Name**: `wall-finisher-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"
7. Copy the URL (e.g., `https://wall-finisher-api.onrender.com`)

### Frontend
1. On Render → "New +" → "Static Site"
2. Connect same repo
3. Configure:
   - **Name**: `wall-finisher-ui`
   - **Build Command**: (leave empty)
   - **Publish Directory**: `frontend`
4. Add Environment Variable:
   - Key: `API_URL`
   - Value: (paste backend URL from step 7)
5. Click "Create Static Site"

**Done!** Access your app at the frontend URL.

---

## Production VPS (30 minutes)

### For DigitalOcean/Linode/AWS EC2

```bash
# 1. SSH into server
ssh root@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone repo
git clone https://github.com/Anisha-Maan/Autonomous-wall-finisher.git
cd Autonomous-wall-finisher

# 4. Start application
docker-compose up -d

# 5. Setup domain (optional)
# Point your domain's A record to: your-server-ip
# Install SSL: sudo certbot --nginx -d yourdomain.com
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Update CORS origins in `backend/main.py` (remove `*`)
- [ ] Set environment variables (see `.env.example`)
- [ ] Enable HTTPS/SSL
- [ ] Add rate limiting
- [ ] Setup monitoring (Sentry, etc.)
- [ ] Configure backups for database
- [ ] Test with production data

---

## Troubleshooting

### Docker Issues
```powershell
# Rebuild containers
docker-compose up -d --build

# View logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart
```

### Can't Access Frontend
- Ensure port 80 is not in use
- On Windows: stop IIS if installed
- Change port in docker-compose.yml: `"8080:80"`

### Backend Not Responding
```powershell
# Check if backend is running
docker-compose ps

# Enter backend container
docker-compose exec backend bash

# Test endpoint
curl http://localhost:8000/health
```

---

## Cost Comparison

| Platform | Cost | Setup Time | Scaling |
|----------|------|------------|---------|
| **Local Docker** | Free | 5 min | Manual |
| **Render.com** | Free tier | 10 min | Auto |
| **Railway** | $5/mo | 5 min | Auto |
| **VPS (DO)** | $6/mo | 30 min | Manual |
| **AWS** | $20-30/mo | 60 min | Auto |

**Recommendation**: 
- Development: Local Docker
- Demo/Testing: Render.com (free)
- Production: VPS or Railway

---

## Next Steps

1. **Deploy**: Choose method above and deploy
2. **Secure**: Setup HTTPS and restrict CORS
3. **Monitor**: Add Sentry or logging
4. **Backup**: Schedule database backups
5. **Scale**: Add load balancer if needed

**Need help?** See full guide in [DEPLOYMENT.md](./DEPLOYMENT.md)
