# Quick Deployment Guide

Choose the deployment method that best fits your needs.

## 🚀 Option 1: Deploy to a VPS (Recommended for Beginners)

**Platforms:** DigitalOcean, Linode, AWS EC2, Google Compute Engine

**Time:** 15 minutes | **Cost:** ~$20-40/month

### Steps:

1. **Create a server**
   - Ubuntu 22.04 LTS
   - Minimum: 4GB RAM, 2 CPUs, 50GB storage
   - Recommended: 8GB RAM, 4 CPUs, 100GB storage

2. **SSH into your server**
   ```bash
   ssh root@your-server-ip
   ```

3. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Clone your repository**
   ```bash
   git clone YOUR_REPO_URL
   cd Real\ time\ e-commerece\ analytics
   ```

5. **Configure environment**
   ```bash
   cp .env.production.example .env.production
   nano .env.production  # Edit with your settings
   ```

6. **Deploy**
   ```bash
   ./deploy.sh
   ```

7. **Access your application**
   - Frontend: `http://your-server-ip`
   - Backend API: `http://your-server-ip:8000`

**Done! 🎉**

---

## ☁️ Option 2: Deploy to Railway (Easiest)

**Time:** 5 minutes | **Cost:** ~$5-20/month (with free tier available)

### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Choose "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect and deploy

3. **Add services via Railway dashboard:**
   - Add PostgreSQL plugin (Railway will install TimescaleDB)
   - Add Kafka plugin
   - Configure environment variables in dashboard

4. **Access your app**
   - Railway provides a URL like `shopstream.railway.app`

**Done! 🎉**

---

## 🐳 Option 3: Deploy with Docker on Your Own Machine

**Time:** 10 minutes | **Cost:** Free (uses your hardware)

### Steps:

1. **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)

2. **Configure environment**
   ```bash
   cp .env.production.example .env.production
   # Edit .env.production with your settings
   ```

3. **Deploy**
   ```bash
   ./deploy.sh
   ```

4. **Access locally**
   - Frontend: `http://localhost`
   - Backend: `http://localhost:8000`

**Done! 🎉**

---

## 🌐 Option 4: Deploy to Render (Simple Cloud)

**Time:** 10 minutes | **Cost:** ~$15-30/month (free tier available)

### Steps:

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Create services on Render:**

   **Database:**
   - Go to [render.com](https://render.com)
   - New → PostgreSQL
   - Name: `shopstream-db`
   - Plan: Starter ($7/month) or Free
   - After creation, install TimescaleDB extension via Render shell

   **Backend:**
   - New → Web Service
   - Connect your GitHub repo
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables (from .env.production)

   **Frontend:**
   - New → Static Site
   - Connect your GitHub repo
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`

3. **Access your app**
   - Render provides URLs like `shopstream.onrender.com`

**Done! 🎉**

---

## 🎯 Which Option Should You Choose?

| Option | Best For | Pros | Cons |
|--------|----------|------|------|
| **VPS** | Full control, learning | Complete control, cheaper at scale | Requires server management |
| **Railway** | Quick MVP, startups | Fastest setup, auto-scaling | More expensive at scale |
| **Local Docker** | Development, testing | Free, full control | Not accessible publicly |
| **Render** | Small projects, MVPs | Simple, good free tier | Limited customization |

---

## 📊 Recommended Setup by Project Stage

### 🌱 MVP / Prototype
- **Platform:** Railway or Render
- **Why:** Fast setup, free tier available
- **Cost:** $0-10/month

### 🚀 Early Stage Startup
- **Platform:** DigitalOcean VPS or Render
- **Why:** Good balance of cost and features
- **Cost:** $20-50/month

### 💼 Growing Company
- **Platform:** AWS ECS or DigitalOcean Kubernetes
- **Why:** Scalable, professional features
- **Cost:** $100-300/month

### 🏢 Enterprise
- **Platform:** AWS EKS or Google GKE
- **Why:** High availability, auto-scaling, compliance
- **Cost:** $500+/month

---

## 🔒 Important: Secure Your Deployment

After deploying, immediately:

1. **Change default passwords**
   ```bash
   # In .env.production
   DB_PASSWORD=your_strong_random_password
   ```

2. **Enable firewall**
   ```bash
   # On Ubuntu/Debian
   ufw allow 22    # SSH
   ufw allow 80    # HTTP
   ufw allow 443   # HTTPS
   ufw enable
   ```

3. **Set up SSL/TLS (HTTPS)**
   ```bash
   # Using Certbot (Let's Encrypt)
   sudo apt install certbot
   sudo certbot --nginx -d yourdomain.com
   ```

4. **Configure CORS**
   ```bash
   # In .env.production
   CORS_ORIGINS=https://yourdomain.com
   ```

5. **Set up backups**
   ```bash
   # Database backup script
   pg_dump -h localhost -U postgres shopstream > backup.sql
   ```

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check logs
docker logs shopstream-backend-prod

# Common issue: Database not ready
# Solution: Wait 30 seconds after starting database
```

### Frontend shows blank page
```bash
# Check if API URL is correct in .env.production
VITE_API_URL=http://your-server-ip:8000

# Rebuild frontend
docker-compose -f docker-compose.prod.yml up -d --build frontend
```

### Kafka consumer not processing
```bash
# Check Kafka is running
docker logs shopstream-kafka-prod

# Check consumer logs
docker logs shopstream-kafka-consumer-prod

# Restart consumer
docker restart shopstream-kafka-consumer-prod
```

### Out of memory errors
```bash
# Increase Docker memory limit or upgrade server
# Minimum recommended: 4GB RAM
```

---

## 📞 Need Help?

1. Check the full [DEPLOYMENT.md](DEPLOYMENT.md) guide
2. Review logs: `docker-compose -f docker-compose.prod.yml logs`
3. Open an issue on GitHub
4. Email: harsha@example.com

---

## 🎓 Next Steps After Deployment

1. ✅ **Monitor your app**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure error tracking (Sentry)

2. ✅ **Add custom domain**
   - Register domain (Namecheap, Google Domains)
   - Point DNS to your server IP
   - Set up SSL certificate

3. ✅ **Optimize performance**
   - Enable CDN (CloudFlare)
   - Set up Redis caching
   - Configure database indexes

4. ✅ **Set up CI/CD**
   - GitHub Actions for automated deployment
   - Automated testing on pull requests

5. ✅ **Scale as needed**
   - Add more consumer instances
   - Scale database vertically
   - Add load balancer

---

Built with ❤️ by Harsha Kanaparthi
