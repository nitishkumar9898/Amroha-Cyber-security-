# CyberThreatForge (Amroha01)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

An advanced cybersecurity training, threat modeling, and defensive intelligence simulation platform. This project integrates machine learning algorithms for predictive threat analytics, quantum-safe cryptographical integrations, and a live training arena for simulated cyber warfare drills.

---

## 🚀 Features

- **AI Threat Predictor**: ML-driven engine (`ai_layer`) that forecasts cyber threats and analyzes potential vector vulnerabilities.
- **Quantum Security Integration**: Post-quantum cryptographic simulation and secure integration modules.
- **Interactive Training Arena**: Real-time playground to simulate, monitor, and defend against security incidents.
- **Supply Chain Analytics**: Built-in tracking and modeling for software supply chain attack surfaces.
- **Modern Dashboard**: Visually rich frontend built with React, Tailwind/CSS, and TypeScript for real-time visualization of network health, alert management, and attack logs.
- **Dockerized Architecture**: Simplified orchestration using Docker Compose and Kubernetes configurations.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Modern Vanilla CSS / TailwindCSS
- **Build Tool**: Vite

### Backend
- **Framework**: Python (FastAPI/Flask)
- **Database**: SQLite / SQLX migrations supported with Alembic
- **AI/ML Layer**: Custom Python-based predictive algorithms

### Infrastructure & Deployment
- **Containers**: Docker (`Dockerfile.backend`, `Dockerfile.frontend`)
- **Orchestration**: Docker Compose (`docker-compose.yml`) & Kubernetes (`k8s-deployment.yml`)
- **Monitoring**: Prometheus integration

---

## 📂 Project Structure

```text
Amroha01/
├── ai_layer/          # AI predictive models and algorithms
├── backend/           # API routes, database schemas, and migration scripts
├── frontend/          # React + TSX dashboard codebase
├── k8s/               # Kubernetes configuration manifests
├── Dockerfile.backend # Docker config for backend
├── Dockerfile.frontend# Docker config for frontend
└── docker-compose.yml # Main compose configuration
```

---

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (Optional, for containerized run)

### Running Locally

#### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install dependencies and run the server:
   ```bash
   pip install -r requirements.txt
   python -m app.main
   ```

#### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

---

## 🐳 Docker Deployment

To spin up the entire application (Frontend, Backend, and Databases) in one command:

```bash
docker-compose up --build
```
The services will be available at:
- **Frontend**: `http://localhost:3000` (or as configured in `docker-compose.yml`)
- **Backend API**: `http://localhost:8000`

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
