# 🌍 CleanJo: GPS-Based Garbage Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, full-stack application designed for reporting, tracking, and managing community garbage cleanup efforts using GPS-based detection.

---

## 🏗️ Architecture Overview

```text
├── 🐍 backend/         # FastAPI backend (Python) with Kafka integration
├── 📱 mobile/          # Flutter mobile application (iOS & Android)
├── 🌐 web/             # React web dashboard for admins
└── 🐳 docker-compose.yml
```

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Mobile App** | Flutter 3.x, Dart |
| **Web Dashboard** | React, Tailwind CSS |
| **Backend API** | Python, FastAPI |
| **Database** | PostgreSQL, PostGIS |
| **Event Streaming** | Apache Kafka |
| **File Storage** | Cloudinary / AWS S3 |
| **Auth** | JWT |
| **Mapping** | Google Maps (mobile: google_maps_flutter, web: @react-google-maps/api) |

---

## ✨ Key Features

### 📱 Mobile App
- **User Auth:** Phone number registration and secure sign-in via OTP.
- **Reporting:** GPS-tagged garbage reports with photo uploads.
- **Syncing:** Offline queue system with automatic synchronization.
- **Maps:** Interactive map view with marker clustering.
- **Tracking:** Real-time report status updates.
- **Roles:** Dynamic UI for citizens vs. inspectors.

### 🌐 Web Dashboard
- **Analytics:** Dashboard featuring performance statistics and charts.
- **Management:** Full control over reports (filter, view, update status).
- **Administration:** User management with role-based access control.
- **Visuals:** Interactive heatmap-based map view.
- **Real-time:** Live status updates via WebSocket integration.

### 🐍 Backend Services
- **API:** RESTful interface with JWT security.
- **Events:** Asynchronous processing using Kafka event streaming.
- **Notifications:** Automated system for status changes.
- **Geospatial:** Advanced spatial queries with PostGIS.

---

## 🚀 Getting Started

### 1. Infrastructure
Ensure Docker is installed and run:
```bash
docker-compose up -d
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Web Dashboard
```bash
cd web
npm install
npm run dev
```

### 4. Mobile App
```bash
cd mobile
flutter pub get
flutter run
```

---

## 🔑 Admin Management
Create admin users via CLI from the backend:
```bash
python -m app.cli create-admin
```

---

## 📁 Project Structure
```text
backend/          # API, Services, Models, Workers
mobile/           # Core Logic, Feature Modules, UI
web/              # Pages, Components, Hooks, API Client
```

---

## ⚖️ License
Distributed under the **MIT License**.
