# ElevAIte
Search-Optimized Workflow Management System
---

# Student CRM System

A lightweight, self-hosted CRM tailored for students to track **internships, job applications, and research opportunities** — all in one place.

---

## 📑 Table of Contents

* [Features](#-features)
* [Architecture](#-architecture)
* [Quick Start](#-quick-start)
* [Development](#-development)
* [Deployment](#-deployment)
* [Configuration](#-configuration)
* [Initial Setup](#-initial-setup)
* [API Documentation](#-api-documentation)
* [Contributing](#-contributing)

---

## ✨ Features

* **Opportunity Management** – Track internships, jobs, and research openings with customizable pipelines.
* **Networking CRM** – Manage recruiter/mentor contacts, track relationships and interactions.
* **Resume & Document Hub** – Version control with search across resumes, cover letters, and notes.
* **AI-powered Matching** – Smart scoring and recommendations for opportunities.
* **Automation Engine** – Set up reminders, notifications, and follow-up tasks.
* **Analytics Dashboard** – Funnel analysis, conversion rates, and performance insights.
* **Self-Hosted** – Runs locally or on a single VM with Docker.

---

## 🏗 Architecture

* **API** – FastAPI + PostgreSQL
* **Worker** – Celery + Redis (background jobs)
* **Search** – Meilisearch (fast full-text search)
* **Frontend** – Next.js (React)
* **Reverse Proxy** – Nginx
* **Containerization** – Docker Compose for all services

---

## ⚡ Quick Start

1. **Clone repository**

   ```bash
   git clone <repository-url>
   cd student-crm
   ```

2. **Set up environment**

   ```bash
   cp .env.example .env
   # Edit .env with your config
   ```

3. **Run with Docker**

   ```bash
   docker-compose up -d
   ```

4. **Access services**

   * App → [http://localhost](http://localhost)
   * API Docs → [http://localhost/api/docs](http://localhost/api/docs)
   * Meilisearch → [http://localhost:7700](http://localhost:7700)

---

## 🔧 Development

### API

```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Worker

```bash
cd worker
pip install -r requirements.txt
celery -A app.worker worker --loglevel=info
```

---

## 🚀 Deployment

### Local VM

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Azure VM (optional)

```bash
az vm create --resource-group myResourceGroup --name student-crm-vm --image Ubuntu2004
ssh user@vm-ip
git clone <repository-url>
cd student-crm
docker-compose up -d
```

---

## ⚙️ Configuration

| Variable       | Description                             |
| -------------- | --------------------------------------- |
| `JWT_SECRET`   | Secret key for JWT tokens               |
| `DATABASE_URL` | PostgreSQL connection string            |
| `REDIS_URL`    | Redis connection string                 |
| `SMTP_*`       | SMTP config for email notifications     |
| `AZURE_*`      | Azure Blob Storage for optional backups |

---

## 🛠 Initial Setup

* Create an **admin user** via API
* Configure **SMTP** for emails
* Schedule **backups**
* Build **search indexes**

---

## 📖 API Documentation

REST endpoints:

* `/auth/*` – Authentication
* `/opportunities/*` – Opportunities
* `/applications/*` – Applications
* `/contacts/*` – Contacts
* `/documents/*` – Documents
* `/tasks/*` – Tasks & reminders
* `/rules/*` – Automation rules
* `/analytics/*` – Analytics

📍 Full API reference: [http://localhost/api/docs](http://localhost/api/docs)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Open a Pull Request

---
