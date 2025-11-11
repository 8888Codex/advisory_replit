#!/bin/bash
#
# Database Backup Script
# Backs up PostgreSQL database with compression and retention policy
#
# Usage:
#   ./backup_db.sh [backup_dir]
#
# Environment Variables Required:
#   DATABASE_URL - PostgreSQL connection string
#   BACKUP_RETENTION_DAYS - Number of days to keep backups (default: 30)
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${1:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "🗄️  Database Backup Script"
echo "=============================================="
echo

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL environment variable not set${NC}"
    echo "   Please set DATABASE_URL in .env file"
    exit 1
fi

# Parse DATABASE_URL to extract components
# Format: postgresql://user:password@host:port/database
DB_USER=$(echo "$DATABASE_URL" | sed -n 's|^postgresql://\([^:]*\):.*|\1|p')
DB_PASS=$(echo "$DATABASE_URL" | sed -n 's|^postgresql://[^:]*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|^postgresql://[^@]*@\([^:]*\):.*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|^postgresql://[^@]*@[^:]*:\([^/]*\)/.*|\1|p')
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|^postgresql://[^/]*/\(.*\)$|\1|p')

echo "📊 Configuration:"
echo "   Database: $DB_NAME"
echo "   Host: $DB_HOST:$DB_PORT"
echo "   User: $DB_USER"
echo "   Backup Dir: $BACKUP_DIR"
echo "   Retention: $RETENTION_DAYS days"
echo

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create temporary directory for backup process
TMP_DIR="${BACKUP_DIR}/.tmp"
mkdir -p "$TMP_DIR"

# Set PostgreSQL password for pg_dump
export PGPASSWORD="$DB_PASS"

echo "🔄 Starting backup..."
echo

# Run pg_dump
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    > "${TMP_DIR}/${BACKUP_FILE}"; then
    
    echo -e "${GREEN}✅ Database dump created${NC}"
    
    # Compress the backup
    echo "🗜️  Compressing backup..."
    gzip -9 "${TMP_DIR}/${BACKUP_FILE}"
    
    # Move to backup directory
    mv "${TMP_DIR}/${COMPRESSED_FILE}" "${BACKUP_DIR}/${COMPRESSED_FILE}"
    
    # Get file size
    FILE_SIZE=$(du -h "${BACKUP_DIR}/${COMPRESSED_FILE}" | cut -f1)
    
    echo -e "${GREEN}✅ Backup compressed and saved${NC}"
    echo "   File: ${COMPRESSED_FILE}"
    echo "   Size: ${FILE_SIZE}"
    echo
    
else
    echo -e "${RED}❌ ERROR: pg_dump failed${NC}"
    rm -rf "$TMP_DIR"
    exit 1
fi

# Clean up temporary directory
rm -rf "$TMP_DIR"

# Remove old backups (retention policy)
echo "🧹 Cleaning old backups (keeping last $RETENTION_DAYS days)..."

DELETED_COUNT=0
while IFS= read -r -d '' old_backup; do
    rm -f "$old_backup"
    DELETED_COUNT=$((DELETED_COUNT + 1))
    echo "   Deleted: $(basename "$old_backup")"
done < <(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0)

if [ $DELETED_COUNT -eq 0 ]; then
    echo "   No old backups to delete"
else
    echo -e "${GREEN}   Deleted $DELETED_COUNT old backup(s)${NC}"
fi

echo

# List current backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f | wc -l)
echo "📁 Current backups: $BACKUP_COUNT file(s)"

# Calculate total size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "💾 Total size: $TOTAL_SIZE"

echo
echo "=============================================="
echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo "=============================================="
echo "   Latest backup: ${COMPRESSED_FILE}"
echo "   Location: ${BACKUP_DIR}/"
echo

# Restore instructions
echo "📖 To restore this backup:"
echo "   gunzip -c ${BACKUP_DIR}/${COMPRESSED_FILE} | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo

# Unset password
unset PGPASSWORD

exit 0

