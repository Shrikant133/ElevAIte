#!/bin/bash

# Backup script for Student CRM
set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="student_crm_backup_${DATE}.tar.gz"

echo "💾 Creating backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
echo "📊 Backing up database..."
docker-compose exec -T postgres pg_dump -U postgres student_crm > "$BACKUP_DIR/db_${DATE}.sql"

# Create files backup
echo "📁 Backing up uploaded files..."
tar -czf "$BACKUP_DIR/uploads_${DATE}.tar.gz" -C ./volumes uploads/

# Create configuration backup
echo "⚙️ Backing up configuration..."
cp .env "$BACKUP_DIR/env_${DATE}.backup"

# Create combined backup
echo "📦 Creating combined backup..."
cd $BACKUP_DIR
tar -czf $BACKUP_FILE db_${DATE}.sql uploads_${DATE}.tar.gz env_${DATE}.backup
rm db_${DATE}.sql uploads_${DATE}.tar.gz env_${DATE}.backup
cd ..

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_FILE"

# Optional: Upload to Azure Blob Storage
if [ ! -z "$AZURE_STORAGE_CONNECTION_STRING" ]; then
    echo "☁️ Uploading to Azure Blob Storage..."
    az storage blob upload \
        --connection-string "$AZURE_STORAGE_CONNECTION_STRING" \
        --container-name "$AZURE_CONTAINER_NAME" \
        --file "$BACKUP_DIR/$BACKUP_FILE" \
        --name "backups/$BACKUP_FILE"
    echo "✅ Uploaded to Azure Blob Storage"
fi

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "student_crm_backup_*.tar.gz" -mtime +7 -delete

echo "🧹 Cleaned up old backups"