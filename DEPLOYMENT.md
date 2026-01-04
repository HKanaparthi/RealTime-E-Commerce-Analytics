
# ShopStream Deployment Guide

This guide covers deploying ShopStream to production environments.

## Architecture Overview

ShopStream consists of 7 services:
- **Zookeeper** - Kafka coordination
- **Kafka** - Event streaming
- **TimescaleDB** - Time-series database
- **Event Generator** - Simulates e-commerce events
- **Kafka Consumer** - Processes events and calculates metrics
- **Backend API** - FastAPI REST + WebSocket server
- **Frontend** - React dashboard

## Deployment Options

### Option 1: AWS (Recommended for Production)

**Services Needed:**
- **ECS/EKS** - Container orchestration
- **Amazon MSK** - Managed Kafka
- **RDS for PostgreSQL with TimescaleDB** - Database
- **Application Load Balancer** - Traffic routing
- **CloudFront** - CDN for frontend
- **S3** - Static frontend hosting

**Estimated Monthly Cost:** $300-500

**Steps:**

#### 1. Set up Amazon MSK (Managed Kafka)
```bash
# Create MSK cluster
aws kafka create-cluster \
  --cluster-name shopstream-kafka \
  --broker-node-group-info file://broker-config.json \
  --kafka-version 3.5.1
```

#### 2. Set up RDS TimescaleDB
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier shopstream-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.1 \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 50

# After creation, install TimescaleDB extension
psql -h your-db.rds.amazonaws.com -U postgres -d shopstream \
  -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

#### 3. Deploy Backend to ECS
```bash
# Build and push Docker image
docker build -t shopstream-backend ./backend
docker tag shopstream-backend:latest YOUR_ECR_REPO/shopstream-backend:latest
docker push YOUR_ECR_REPO/shopstream-backend:latest

# Create ECS task definition and service
aws ecs create-service \
  --cluster shopstream \
  --service-name backend \
  --task-definition shopstream-backend \
  --desired-count 2 \
  --launch-type FARGATE
```

#### 4. Deploy Frontend to S3 + CloudFront
```bash
# Build frontend
cd frontend
npm run build

# Upload to S3
aws s3 sync dist/ s3://shopstream-frontend/

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name shopstream-frontend.s3.amazonaws.com
```

#### 5. Environment Variables (Backend)
```bash
DATABASE_URL=postgresql://postgres:PASSWORD@your-db.rds.amazonaws.com/shopstream
KAFKA_BOOTSTRAP_SERVERS=b-1.shopstream.kafka.us-east-1.amazonaws.com:9092
REDIS_URL=redis://your-elasticache.amazonaws.com:6379
CORS_ORIGINS=https://your-cloudfront-domain.cloudfront.net
```

---

### Option 2: DigitalOcean (Simpler, Budget-Friendly)

**Services Needed:**
- **Droplets** - VMs for services
- **Managed Kafka** - DigitalOcean Kafka
- **Managed PostgreSQL** - Database
- **App Platform** - Frontend hosting
- **Load Balancer** - Traffic distribution

**Estimated Monthly Cost:** $150-250

**Steps:**

#### 1. Create Managed Database
```bash
# Create PostgreSQL cluster with TimescaleDB
doctl databases create shopstream-db \
  --engine pg \
  --version 16 \
  --size db-s-2vcpu-4gb \
  --region nyc1

# Install TimescaleDB extension
psql -h your-db.ondigitalocean.com -U doadmin -d shopstream \
  -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

#### 2. Create Managed Kafka
```bash
doctl databases create shopstream-kafka \
  --engine kafka \
  --size db-s-2vcpu-4gb \
  --region nyc1
```

#### 3. Deploy Backend to Droplet
```bash
# Create droplet
doctl compute droplet create shopstream-backend \
  --image docker-20-04 \
  --size s-2vcpu-4gb \
  --region nyc1

# SSH and deploy
ssh root@your-droplet-ip

# Clone repo and start services
git clone YOUR_REPO
cd Real\ time\ e-commerece\ analytics
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. Deploy Frontend to App Platform
```bash
# Push to GitHub
git push origin main

# Create app via DigitalOcean console:
# - Connect GitHub repo
# - Set build command: npm run build
# - Set output directory: dist
```

---

### Option 3: Railway (Fastest Deployment)

**Services Needed:**
- Railway projects for each service

**Estimated Monthly Cost:** $100-200

**Steps:**

#### 1. Deploy to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init

# Deploy backend
cd backend
railway up

# Deploy frontend
cd ../frontend
railway up
```

#### 2. Add Kafka and PostgreSQL
```bash
# Via Railway dashboard:
# - Add Kafka plugin
# - Add PostgreSQL plugin with TimescaleDB
```

#### 3. Configure Environment Variables
```bash
railway variables set DATABASE_URL=postgresql://...
railway variables set KAFKA_BOOTSTRAP_SERVERS=...
```

---

### Option 4: Kubernetes (Advanced)

**For high-scale production deployments**

#### Prerequisites
- Kubernetes cluster (EKS, GKE, or AKS)
- kubectl installed
- Helm installed

#### Steps

1. **Create namespace**
```bash
kubectl create namespace shopstream
```

2. **Deploy Kafka using Strimzi**
```bash
# Install Strimzi operator
kubectl create -f 'https://strimzi.io/install/latest?namespace=shopstream'

# Deploy Kafka cluster
kubectl apply -f k8s/kafka-cluster.yaml
```

3. **Deploy TimescaleDB**
```bash
helm repo add timescale https://charts.timescale.com
helm install shopstream-db timescale/timescaledb-single \
  --namespace shopstream \
  --set persistentVolume.size=50Gi
```

4. **Deploy application services**
```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/consumer-deployment.yaml
```

---

## Production Configuration Checklist

### 1. Security
- [ ] Enable SSL/TLS for all services
- [ ] Use secrets management (AWS Secrets Manager, Vault)
- [ ] Set up VPC and security groups
- [ ] Enable authentication on Kafka
- [ ] Use strong database passwords
- [ ] Enable CORS only for your domain
- [ ] Set up API rate limiting

### 2. Monitoring
- [ ] Set up application metrics (Prometheus + Grafana)
- [ ] Configure logging (ELK stack or CloudWatch)
- [ ] Set up alerts (PagerDuty, Slack)
- [ ] Monitor Kafka lag
- [ ] Track database performance

### 3. Scalability
- [ ] Configure auto-scaling for backend
- [ ] Set up Kafka partitions (3-5 recommended)
- [ ] Enable database replication
- [ ] Use connection pooling
- [ ] Set up Redis for caching

### 4. Backup & Recovery
- [ ] Enable automated database backups
- [ ] Set up point-in-time recovery
- [ ] Document disaster recovery procedure
- [ ] Test backup restoration

### 5. Performance
- [ ] Enable CDN for frontend
- [ ] Optimize database indexes
- [ ] Configure Kafka retention policies
- [ ] Set up database connection pooling
- [ ] Enable gzip compression

---

## Quick Deploy Script

Create `deploy.sh`:

```bash
#!/bin/bash

echo "🚀 ShopStream Production Deployment"
echo "===================================="

# Build all images
docker-compose build

# Tag for registry
docker tag shopstream-backend:latest YOUR_REGISTRY/shopstream-backend:latest
docker tag shopstream-frontend:latest YOUR_REGISTRY/shopstream-frontend:latest
docker tag shopstream-consumer:latest YOUR_REGISTRY/shopstream-consumer:latest

# Push to registry
docker push YOUR_REGISTRY/shopstream-backend:latest
docker push YOUR_REGISTRY/shopstream-frontend:latest
docker push YOUR_REGISTRY/shopstream-consumer:latest

# Deploy to production
kubectl set image deployment/backend backend=YOUR_REGISTRY/shopstream-backend:latest
kubectl set image deployment/frontend frontend=YOUR_REGISTRY/shopstream-frontend:latest
kubectl set image deployment/consumer consumer=YOUR_REGISTRY/shopstream-consumer:latest

echo "✅ Deployment complete!"
```

---

## Environment Variables for Production

Create `.env.production`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/shopstream
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka1:9092,kafka2:9092,kafka3:9092
KAFKA_TOPIC=ecommerce-events
KAFKA_CONSUMER_GROUP=shopstream-prod

# Redis (optional, for caching)
REDIS_URL=redis://redis:6379/0

# Backend
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# Feature flags
ENABLE_EVENT_GENERATOR=false  # Disable in production
ENABLE_METRICS=true
ENABLE_ALERTS=true
```

---

## Cost Comparison

| Platform | Monthly Cost | Complexity | Best For |
|----------|-------------|------------|----------|
| **AWS** | $300-500 | High | Enterprise, high-scale |
| **DigitalOcean** | $150-250 | Medium | Growing startups |
| **Railway** | $100-200 | Low | MVP, small teams |
| **Render** | $100-180 | Low | Quick prototypes |
| **Kubernetes** | $200-400 | Very High | Multi-cloud, custom needs |

---

## Recommended Deployment for Different Scales

### Small Scale (< 1000 users)
- **Platform:** Railway or Render
- **Database:** Managed PostgreSQL (smallest tier)
- **Kafka:** Railway Kafka plugin
- **Cost:** ~$100/month

### Medium Scale (1000-10,000 users)
- **Platform:** DigitalOcean
- **Database:** Managed PostgreSQL (2vCPU, 4GB)
- **Kafka:** Managed Kafka (3 brokers)
- **Cost:** ~$200/month

### Large Scale (10,000+ users)
- **Platform:** AWS with EKS
- **Database:** RDS Multi-AZ
- **Kafka:** Amazon MSK (3 brokers)
- **Cost:** $400+/month

---

## Post-Deployment

### 1. Verify Deployment
```bash
# Check backend health
curl https://api.yourdomain.com/api/metrics/health

# Check frontend
curl https://yourdomain.com

# Check Kafka consumer logs
kubectl logs -f deployment/consumer
```

### 2. Set up Monitoring
```bash
# Install Prometheus
helm install prometheus prometheus-community/prometheus

# Install Grafana
helm install grafana grafana/grafana
```

### 3. Configure Alerts
```bash
# Set up Slack alerts
kubectl apply -f k8s/alertmanager-config.yaml
```

---

## Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka brokers
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Check consumer lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group shopstream-consumer-group --describe
```

### Database Connection Issues
```bash
# Test connection
psql -h your-db-host -U postgres -d shopstream -c "SELECT version();"

# Check connections
psql -h your-db-host -U postgres -d shopstream \
  -c "SELECT * FROM pg_stat_activity;"
```

### Backend Issues
```bash
# Check logs
docker logs shopstream-backend -f

# Check metrics
curl localhost:8000/api/metrics/health
```

---

## Support

For deployment support:
- Email: harsha@example.com
- GitHub Issues: YOUR_REPO/issues
- Documentation: docs.shopstream.io

Built by Harsha Kanaparthi
