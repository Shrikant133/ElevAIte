# Student CRM System

A comprehensive CRM system for students to track internships, jobs, and research opportunities.

## Features

- **Opportunity Tracking**: Track internships, jobs, and research opportunities with custom pipelines
- **Networking**: Manage contacts with relationship tracking and interaction logging
- **Document Management**: Version control for resumes and cover letters with full-text search
- **Smart Matching**: AI-powered opportunity scoring and recommendations
- **Automation**: Rules engine for follow-ups, reminders, and notifications
- **Analytics**: Funnel analysis, success rates, and performance tracking
- **Self-hosted**: Everything runs locally or on a single VM

## Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd student-crm

   ```

2. **Set up environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the system**

   ```bash
   docker-compose up -d
   ```

4. **Access the application**

   - **Frontend**: [http://localhost](http://localhost)
   - **API Documentation**: [http://localhost/api/docs](http://localhost/api/docs)
   - **Meilisearch Dashboard**: [http://localhost:7700](http://localhost:7700)

## Architecture

- **API**: FastAPI with PostgreSQL
- **Worker**: Celery with Redis for background jobs
- **Search**: Meilisearch for full-text search
- **Frontend**: Next.js React application
- **Reverse Proxy**: Nginx
- All services containerized with Docker

## Development

### API Development

```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Worker Development

```bash
cd worker
pip install -r requirements.txt
celery -A app.worker worker --loglevel=info
```

## Production Deployment

### Local VM

```bash
# Production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Azure VM (Optional)

```bash
# Create Azure VM
az vm create --resource-group myResourceGroup --name student-crm-vm --image Ubuntu2004

# SSH and setup
ssh user@vm-ip
git clone <repository-url>
cd student-crm
docker-compose up -d
```

## Configuration

### Environment Variables

- **JWT_SECRET**: Secret key for JWT tokens
- **DATABASE_URL**: PostgreSQL connection string
- **REDIS_URL**: Redis connection string
- **SMTP\_**\*: Email configuration for notifications
- **AZURE\_**\*: Optional Azure Blob Storage for backups

### Initial Setup

- Create admin user via API
- Configure SMTP for email notifications
- Set up backup schedule
- Configure search indexes

## API Documentation

The API provides RESTful endpoints for:

- **Authentication** (`/auth/*`)
- **Opportunities** (`/opportunities/*`)
- **Applications** (`/applications/*`)
- **Contacts** (`/contacts/*`)
- **Documents** (`/documents/*`)
- **Tasks** (`/tasks/*`)
- **Rules** (`/rules/*`)
- **Analytics** (`/analytics/*`)

Full API documentation available at `/api/docs`
