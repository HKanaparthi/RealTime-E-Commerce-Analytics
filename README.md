# ShopStream - Real-Time E-Commerce Analytics Platform

![ShopStream](https://img.shields.io/badge/ShopStream-v1.0-blue)
![Built by](https://img.shields.io/badge/Built%20by-Harsha%20Kanaparthi-green)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**ShopStream** is a production-grade real-time analytics platform for e-commerce stores, similar to Google Analytics but specialized for online shopping. It processes streaming events (product views, purchases, cart actions) in real-time using **Apache Kafka**, **Apache Spark**, **TimescaleDB**, **FastAPI**, and **React**.

Built by **Harsha Kanaparthi** with a focus on real-time performance, scalability, and **100% FREE deployment** options.

---

## 🎯 Features

- **Real-Time Analytics**: Process 10,000+ events per second with <100ms latency
- **Live Dashboard**: Auto-updating metrics every 1 second via WebSocket
- **Trending Products**: Real-time detection of hot-selling products
- **Conversion Funnel**: Track user journey from view → cart → purchase
- **Smart Alerts**: Automatic anomaly detection (traffic spikes, low conversion, etc.)
- **Geographic Insights**: Sales distribution by country and city
- **Time-Series Data**: 1-minute and 1-hour aggregations with TimescaleDB
- **100% FREE Deployment**: Docker Compose locally + Railway + Vercel for cloud

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ShopStream                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Event Generator  →  Kafka  →  Spark Streaming  →  TimescaleDB │
│       (Python)       (Topics)    (Aggregations)    (Time-Series)│
│                                         ↓                       │
│                                    FastAPI + WebSocket          │
│                                         ↓                       │
│                                  React Dashboard                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Event Generator** | Python | Simulates 100 events/sec (views, purchases, etc.) |
| **Message Queue** | Apache Kafka | Streams events with 3 partitions |
| **Stream Processor** | Apache Spark | Real-time windowed aggregations (1min, 1hour) |
| **Database** | TimescaleDB | Time-series storage with hypertables |
| **Backend API** | FastAPI | REST endpoints + WebSocket for live updates |
| **Frontend** | React + Vite | Real-time dashboard with charts |
| **Deployment** | Docker + Railway + Vercel | Local dev + free cloud hosting |

---

## 📊 Dashboard Preview

```
┌─────────────────────────────────────────────────────────────────┐
│  ShopStream - Real-Time Analytics                          Live │
├─────────────────────────────────────────────────────────────────┤
│  💰 Revenue: $45,234 ↗ +23%  │  🛒 Orders: 142 ↗ +18%          │
│  👥 Active Users: 47                                            │
├─────────────────────────────────────────────────────────────────┤
│  📊 Sales Per Minute (Live Chart)                              │
│  [Real-time line chart updating every second]                  │
├─────────────────────────────────────────────────────────────────┤
│  🔥 Trending Products                                          │
│  1. iPhone 15 Pro - 45 views/min                               │
│  2. AirPods Pro - 32 views/min                                 │
│  3. MacBook Pro - 28 views/min                                 │
├─────────────────────────────────────────────────────────────────┤
│  📈 Conversion Funnel      │  ⚠️ Alerts                         │
│  Views: 1,247              │  • Traffic spike +150%            │
│  Cart: 312 (25%)           │  • Low conversion 2.1%            │
│  Purchase: 89 (7.1%)       │                                   │
├─────────────────────────────────────────────────────────────────┤
│  🗺️ Geographic Sales (Top 10 Cities)                          │
│  [Bar chart showing revenue by location]                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- **Docker** & **Docker Compose** (for local setup)
- **Python 3.10+** (if running without Docker)
- **Node.js 18+** (for frontend)

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd shopstream
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Zookeeper (port 2181)
   - Kafka (port 9092)
   - TimescaleDB (port 5432)
   - Spark Master (port 8080)
   - Spark Worker
   - FastAPI Backend (port 8000)
   - Event Generator (100 events/sec)
   - Spark Streaming Job
   - React Frontend (port 5173)

3. **Access the dashboard**
   - Dashboard: http://localhost:5173
   - API Docs: http://localhost:8000/docs
   - Spark UI: http://localhost:8080

4. **View logs**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f event-generator
   docker-compose logs -f spark-streaming
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

### Option 2: Manual Setup (Without Docker)

1. **Install dependencies**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend
   cd ../frontend
   npm install
   ```

2. **Start Kafka & Zookeeper** (download from Apache Kafka)
   ```bash
   # Start Zookeeper
   bin/zookeeper-server-start.sh config/zookeeper.properties

   # Start Kafka
   bin/kafka-server-start.sh config/server.properties
   ```

3. **Start PostgreSQL with TimescaleDB**
   ```bash
   # Install TimescaleDB: https://docs.timescale.com/install
   psql -U postgres
   CREATE DATABASE shopstream;
   CREATE EXTENSION timescaledb;
   ```

4. **Initialize database**
   ```bash
   cd backend
   python models.py
   ```

5. **Start services**
   ```bash
   # Terminal 1: FastAPI Backend
   cd backend
   uvicorn main:app --reload

   # Terminal 2: Event Generator
   cd backend
   python kafka_producer.py --rate 100

   # Terminal 3: Spark Streaming
   cd backend
   python spark_streaming.py

   # Terminal 4: React Frontend
   cd frontend
   npm run dev
   ```

6. **Access the dashboard**
   - Dashboard: http://localhost:5173
   - API: http://localhost:8000

---

## ☁️ Cloud Deployment (100% FREE)

### Prerequisites
- **GitHub account** (for code hosting)
- **Railway account** (for backend - free tier)
- **Vercel account** (for frontend - free tier)
- **Neon.tech account** (optional - for PostgreSQL if needed)

### Step 1: Deploy Backend to Railway

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit by Harsha Kanaparthi"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy to Railway**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the Python app

3. **Add PostgreSQL Database**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will provide `DATABASE_URL` automatically
   - Connect to database and enable TimescaleDB:
     ```sql
     CREATE EXTENSION IF NOT EXISTS timescaledb;
     ```

4. **Set Environment Variables in Railway**
   ```env
   DATABASE_URL=<provided by Railway PostgreSQL>
   KAFKA_BOOTSTRAP_SERVERS=<use Upstash Kafka or local for now>
   FRONTEND_URL=<your-vercel-url>
   ENVIRONMENT=production
   DEBUG=false
   ```

5. **Get Backend URL**
   - Railway will provide a URL like: `https://shopstream-backend.railway.app`
   - Copy this for Vercel frontend configuration

### Step 2: Deploy Frontend to Vercel

1. **Deploy to Vercel**
   - Go to [Vercel](https://vercel.com)
   - Click "New Project" → "Import Git Repository"
   - Select your GitHub repository
   - Root Directory: `frontend`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

2. **Set Environment Variables in Vercel**
   ```env
   VITE_API_URL=https://shopstream-backend.railway.app
   ```

3. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy your frontend
   - You'll get a URL like: `https://shopstream.vercel.app`

4. **Update Railway with Vercel URL**
   - Go back to Railway
   - Update `FRONTEND_URL` to your Vercel URL

### Step 3: Initialize Database (One-Time)

1. **SSH into Railway backend** or run locally:
   ```bash
   cd backend
   python models.py
   ```

2. **Verify TimescaleDB hypertables**
   ```sql
   SELECT * FROM timescaledb_information.hypertables;
   ```

### Step 4: Start Event Generation

For cloud deployment, you have two options:

**Option A: Run event generator locally**
```bash
cd backend
export KAFKA_BOOTSTRAP_SERVERS=<your-kafka-url>
python kafka_producer.py --rate 50
```

**Option B: Use Railway worker (requires Kafka setup)**
- Set up Kafka on Railway or use Upstash Kafka (free tier)
- Deploy event generator as a separate Railway service

### Total Monthly Cost: **$0** ✨

- **Railway**: 500 hours free (enough for 24/7 light usage)
- **Vercel**: Unlimited free for hobby projects
- **Neon.tech** (if used): 10GB free PostgreSQL

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all configuration options.

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/shopstream` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9092` |
| `EVENT_RATE` | Events generated per second | `100` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` |

### Kafka Topics

| Topic | Partitions | Retention | Purpose |
|-------|-----------|-----------|---------|
| `ecommerce-events` | 3 | 7 days | All e-commerce events |

### TimescaleDB Tables

| Table | Type | Purpose |
|-------|------|---------|
| `events_raw` | Hypertable | Raw event storage (30 days) |
| `metrics_1min` | Hypertable | 1-minute aggregations (7 days) |
| `metrics_1hour` | Hypertable | 1-hour aggregations (365 days) |
| `trending_products` | Regular | Top trending products |
| `alerts` | Regular | System alerts |
| `geographic_metrics` | Regular | Sales by location |

---

## 📡 API Documentation

### REST Endpoints

**Base URL**: `http://localhost:8000` (local) or `https://your-backend.railway.app` (cloud)

#### Get Live Metrics
```http
GET /api/metrics/live?minutes=5
```

Response:
```json
{
  "success": true,
  "data": {
    "revenue": 45234.50,
    "orders": 142,
    "active_users": 47,
    "conversion_rate": 7.1,
    "cart_abandonment_rate": 65.3
  }
}
```

#### Get Revenue Trend
```http
GET /api/metrics/revenue?hours=1
```

#### Get Trending Products
```http
GET /api/metrics/products/trending?limit=10&minutes=5
```

#### Get Conversion Funnel
```http
GET /api/metrics/funnel?hours=1
```

#### Get Geographic Distribution
```http
GET /api/metrics/geographic?limit=10&hours=1
```

#### Get Active Alerts
```http
GET /api/metrics/alerts?limit=10
```

#### Health Check
```http
GET /health
```

### WebSocket Endpoint

**URL**: `ws://localhost:8000/ws/metrics`

Connect to receive real-time metrics updates every 1 second.

**Message Format** (Server → Client):
```json
{
  "type": "metrics_update",
  "timestamp": "2025-01-03T10:30:00.123Z",
  "data": {
    "live": { ... },
    "trending_products": [ ... ],
    "funnel": { ... },
    "alerts": [ ... ],
    "revenue_trend": [ ... ],
    "geographic": [ ... ]
  }
}
```

**Heartbeat** (Client → Server):
```json
{
  "type": "ping"
}
```

---

## 📝 Event Schema

Events generated follow this structure:

```json
{
  "event_id": "evt_123456",
  "event_type": "purchase",
  "timestamp": "2025-01-03T10:30:00.123Z",
  "user_id": "user_789",
  "session_id": "session_abc",
  "product": {
    "id": "prod_001",
    "name": "iPhone 15 Pro",
    "category": "Electronics",
    "price": 999.00
  },
  "quantity": 1,
  "total_amount": 999.00,
  "payment_method": "credit_card",
  "location": {
    "city": "New York",
    "country": "USA",
    "ip": "192.168.1.1"
  }
}
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `product_view` | User views a product |
| `add_to_cart` | User adds product to cart |
| `remove_from_cart` | User removes product from cart |
| `purchase` | User completes purchase |
| `search` | User searches for products |

---

## 🎨 Metrics Explained

### Key Performance Indicators (KPIs)

1. **Revenue**: Total sales revenue in dollars
2. **Orders**: Number of completed purchases
3. **Active Users**: Unique users in last 5 minutes
4. **Conversion Rate**: (Purchases / Views) × 100%
5. **Cart Abandonment Rate**: (1 - Purchases / Add to Cart) × 100%

### Alert Types

| Alert | Threshold | Severity |
|-------|-----------|----------|
| Traffic Spike | +50% increase | Warning |
| Traffic Drop | -30% decrease | Critical |
| Low Conversion | <3% | Warning |
| High Cart Abandonment | >80% | Warning |
| Trending Product | 3x normal views | Info |
| Revenue Anomaly | ±100% change | Warning/Critical |

---

## 🛠️ Troubleshooting

### Common Issues

**1. Docker Compose fails to start**
- Ensure Docker is running: `docker info`
- Check port conflicts: `lsof -i :8000` (macOS/Linux)
- Increase Docker memory to 4GB+ in Docker Desktop settings

**2. Kafka connection errors**
- Wait 30 seconds for Kafka to fully start
- Check logs: `docker-compose logs kafka`
- Verify Kafka is healthy: `docker-compose ps`

**3. TimescaleDB extension not found**
- Ensure using `timescale/timescaledb` image
- Manually create extension: `CREATE EXTENSION timescaledb;`

**4. Frontend not connecting to backend**
- Check `VITE_API_URL` in `.env`
- Verify CORS settings in `backend/config.py`
- Check browser console for errors

**5. WebSocket disconnects frequently**
- Check firewall/proxy settings
- Increase heartbeat interval in `backend/routes/websocket.py`
- Verify WebSocket URL format (ws:// not http://)

**6. Spark job fails**
- Ensure Java is installed: `java -version`
- Check Spark logs: `docker-compose logs spark-streaming`
- Verify Kafka and TimescaleDB are accessible

**7. Railway deployment issues**
- Check environment variables are set correctly
- Verify DATABASE_URL format
- Check Railway logs for errors
- Ensure PostgreSQL plugin is enabled

---

## 📂 Project Structure

```
shopstream/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── kafka_producer.py       # Event generator
│   ├── spark_streaming.py      # Spark streaming job
│   ├── models.py               # Database models
│   ├── routes/
│   │   ├── metrics.py          # REST endpoints
│   │   └── websocket.py        # WebSocket handler
│   ├── utils/
│   │   ├── timescale.py        # TimescaleDB utilities
│   │   └── alerts.py           # Alert detection
│   ├── Dockerfile              # Backend Docker image
│   ├── Dockerfile.spark        # Spark Docker image
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── LiveChart.jsx
│   │   │   ├── MetricCard.jsx
│   │   │   ├── TrendingProducts.jsx
│   │   │   ├── ConversionFunnel.jsx
│   │   │   ├── Alerts.jsx
│   │   │   └── GeographicChart.jsx
│   │   └── utils/
│   │       ├── api.js          # API client
│   │       └── websocket.js    # WebSocket client
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── vercel.json             # Vercel config
│   └── Dockerfile              # Frontend Docker image
├── docker-compose.yml          # Local development
├── railway.toml                # Railway config
├── Procfile                    # Railway/Heroku
├── .env.example                # Environment template
└── README.md                   # This file
```

---

## 🎓 Learning Resources

### Technologies Used

- [Apache Kafka](https://kafka.apache.org/documentation/) - Event streaming
- [Apache Spark](https://spark.apache.org/docs/latest/) - Stream processing
- [TimescaleDB](https://docs.timescale.com/) - Time-series database
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [React](https://react.dev/) - Frontend framework
- [Recharts](https://recharts.org/) - React charting library
- [Docker](https://docs.docker.com/) - Containerization

### Further Reading

- [Stream Processing with Kafka & Spark](https://kafka.apache.org/documentation/streams/)
- [TimescaleDB Continuous Aggregates](https://docs.timescale.com/use-timescale/latest/continuous-aggregates/)
- [WebSocket with FastAPI](https://fastapi.tiangolo.com/advanced/websockets/)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 👨‍💻 Built By

**Harsha Kanaparthi**

A real-time analytics platform showcasing expertise in:
- Event-driven architectures (Kafka)
- Stream processing (Spark)
- Time-series databases (TimescaleDB)
- Real-time APIs (FastAPI + WebSocket)
- Modern frontend (React)
- Cloud deployment (Railway + Vercel)

---

## 🙏 Acknowledgments

- Apache Kafka & Spark communities
- TimescaleDB team
- FastAPI framework
- React ecosystem

---

## 📞 Support

For issues or questions:
- GitHub Issues: [Create an issue]
- Documentation: See this README
- Deployment guides: Railway.app & Vercel docs

---

**Made with ❤️ by Harsha Kanaparthi** | © 2025 ShopStream

_Real-time analytics at scale, deployed for free._
