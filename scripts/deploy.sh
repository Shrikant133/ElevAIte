#!/bin/bash

# Deployment script for Student CRM
set -e

echo "🚀 Deploying Student CRM..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure."
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec api alembic upgrade head

# Setup search indexes
echo "🔍 Setting up search indexes..."
docker-compose exec worker celery -A app.worker call app.tasks.search_indexing.setup_search_indexes

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Access your Student CRM at: http://localhost"
echo "📚 API Documentation: http://localhost/api/docs"
echo "🔍 Search Dashboard: http://localhost:7700"
echo ""
echo "🔧 To check service status:"
echo "   docker-compose ps"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f [service_name]"