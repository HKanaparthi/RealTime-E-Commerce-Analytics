#!/bin/bash

# ShopStream Production Deployment Script
# Built by Harsha Kanaparthi

set -e

echo "🚀 ShopStream Production Deployment"
echo "===================================="
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found"
    echo "Please copy .env.production.example to .env.production and configure it"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

echo "📋 Deployment Configuration:"
echo "  - Database: ${DB_NAME}"
echo "  - Kafka Topic: ${KAFKA_TOPIC}"
echo "  - API Port: ${API_PORT}"
echo "  - Frontend Port: ${FRONTEND_PORT}"
echo ""

# Ask for confirmation
read -p "Deploy to production? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo ""
echo "🔄 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

echo ""
echo "🗄️  Starting database services..."
docker-compose -f docker-compose.prod.yml up -d zookeeper kafka timescaledb

echo "⏳ Waiting for services to be healthy (30 seconds)..."
sleep 30

echo ""
echo "🚀 Starting application services..."
docker-compose -f docker-compose.prod.yml up -d backend kafka-consumer frontend

echo ""
echo "⏳ Waiting for application to start (10 seconds)..."
sleep 10

echo ""
echo "✅ Deployment Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔍 Verifying deployment..."

# Check backend health
if curl -f -s http://localhost:${API_PORT}/api/metrics/health > /dev/null; then
    echo "  ✅ Backend API is healthy"
else
    echo "  ❌ Backend API health check failed"
fi

# Check frontend
if curl -f -s http://localhost:${FRONTEND_PORT} > /dev/null; then
    echo "  ✅ Frontend is accessible"
else
    echo "  ❌ Frontend is not accessible"
fi

# Check Kafka consumer
if docker logs shopstream-kafka-consumer-prod 2>&1 | grep -q "Connected to Kafka"; then
    echo "  ✅ Kafka consumer is running"
else
    echo "  ⚠️  Kafka consumer might have issues - check logs"
fi

echo ""
echo "📊 Service URLs:"
echo "  - Frontend: http://localhost:${FRONTEND_PORT}"
echo "  - Backend API: http://localhost:${API_PORT}"
echo "  - API Health: http://localhost:${API_PORT}/api/metrics/health"
echo "  - WebSocket: ws://localhost:${API_PORT}/ws/metrics"

echo ""
echo "📝 Next Steps:"
echo "  1. Configure your domain DNS to point to this server"
echo "  2. Set up SSL/TLS certificates (Let's Encrypt)"
echo "  3. Configure nginx reverse proxy for HTTPS"
echo "  4. Set up monitoring and alerts"
echo "  5. Configure automated backups"

echo ""
echo "🔧 Useful Commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "  - Restart service: docker-compose -f docker-compose.prod.yml restart [service]"
echo "  - Stop all: docker-compose -f docker-compose.prod.yml down"
echo "  - View stats: docker stats"

echo ""
echo "✅ Deployment complete!"
echo "Built by Harsha Kanaparthi"
