# GPS-Based Garbage Detection System

A full-stack application for reporting, tracking, and managing garbage cleanup efforts using GPS-based detection.

## Architecture

```
├── backend/          # FastAPI backend with Kafka integration
├── mobile/           # Flutter mobile app (iOS & Android)
├── web/              # React web dashboard (Admin)
├── docker-compose.yml
└── README.md
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Mobile App | Flutter 3.x / Dart |
| Web Dashboard | React + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + PostGIS |
| Event Streaming | Apache Kafka |
| Image Storage | Cloudinary / AWS S3 |
| Auth | JWT |
| Mapping | OpenStreetMap (mobile: flutter_map, web: Leaflet) |

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, Kafka, and Zookeeper.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`

### 3. Web Dashboard Setup

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

Dashboard will be available at `http://localhost:3000`

### 4. Mobile App Setup

```bash
cd mobile

# Install dependencies
flutter pub get

# Run on device/emulator
flutter run
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Default Admin User

Create an admin user via the API:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

## Features

### Mobile App
- User authentication (citizen/inspector roles)
- GPS-based garbage reporting with photo upload
- Offline queue with automatic sync
- Interactive map with marker clustering
- Report status tracking
- Role-based UI (citizen vs inspector views)

### Web Dashboard
- Dashboard with analytics charts
- Reports management (filter, view, update status)
- User management (change roles)
- Interactive map with heatmap view
- Real-time status updates

### Backend
- RESTful API with JWT authentication
- Kafka event streaming for async processing
- ML worker for garbage classification (placeholder)
- Notification worker for status updates
- Image upload to Cloudinary/S3
- Geo-queries with PostGIS support

## Development

### Run Workers

```bash
# ML Worker (garbage classification)
python -m app.workers.ml_worker

# Notification Worker
python -m app.workers.notification_worker
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql+asyncpg://... |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | localhost:9092 |
| `JWT_SECRET_KEY` | JWT signing key | (change in production) |
| `CLOUDINARY_*` | Cloudinary credentials | (optional) |

## Project Structure

```
backend/
├── app/
│   ├── api/          # Routes and schemas
│   ├── core/         # Config, database, security
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Business logic (Kafka, images)
│   ├── workers/      # Background workers
│   └── main.py       # FastAPI app entry point
├── alembic/          # Database migrations
└── requirements.txt

mobile/
├── lib/
│   ├── core/         # Auth, network, DI
│   ├── features/     # Feature modules
│   └── main.dart
└── pubspec.yaml

web/
├── src/
│   ├── components/   # Reusable components
│   ├── pages/        # Page components
│   ├── hooks/         # Custom hooks
│   └── services/     # API client
└── package.json
```

## License

MIT
