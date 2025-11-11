# Multi-stage Dockerfile for O Conselho Marketing Advisory Platform
# Optimized for Dokploy deployment

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY client/package*.json ./client/

# Install dependencies
RUN npm ci

# Copy frontend source
COPY client/ ./client/
COPY shared/ ./shared/
COPY server/ ./server/
COPY tsconfig.json ./
COPY vite.config.ts ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./
COPY components.json ./

# Build frontend
RUN npm run build

# ============================================
# Stage 2: Python Backend Dependencies
# ============================================
FROM python:3.11-slim AS python-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install --system -r pyproject.toml

# ============================================
# Stage 3: Runtime
# ============================================
FROM node:22-slim

WORKDIR /app

# Install Python 3.11 and PostgreSQL client
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Node.js dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy built frontend from builder
COPY --from=frontend-builder /app/dist ./dist
COPY --from=frontend-builder /app/dist/public ./dist/public

# Copy server files
COPY server/ ./server/
COPY shared/ ./shared/

# Copy Python backend
COPY python_backend/ ./python_backend/

# Copy Python dependencies from builder
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy additional files
COPY pyproject.toml ./
COPY backup_db.sh ./
COPY add_soft_delete.sql ./
COPY ENV_VARIABLES.md ./

# Create necessary directories
RUN mkdir -p attached_assets/avatars \
    attached_assets/custom_experts \
    logs \
    backups

# Expose ports
EXPOSE 3001 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3001/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Set environment
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Start application
CMD ["npm", "start"]

