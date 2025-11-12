# Multi-stage Dockerfile for O Conselho Marketing Advisory Platform
# Optimized for Dokploy deployment with Python backend + Node server

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY client/package*.json ./client/

# Install ALL dependencies (including devDependencies for build)
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

# Build frontend AND server (esbuild compiles server to dist/)
RUN npm run build

# ============================================
# Stage 2: Python Backend Dependencies
# ============================================
FROM python:3.11-slim AS python-builder

WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY pyproject.toml ./

# Install Python dependencies using pip directly from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    anthropic>=0.71.0 \
    asyncpg>=0.30.0 \
    bcrypt>=5.0.0 \
    crewai>=1.1.0 \
    crewai-tools>=1.1.0 \
    fastapi>=0.119.1 \
    google-generativeai>=0.8.5 \
    httpx>=0.28.1 \
    loguru>=0.7.0 \
    pillow>=12.0.0 \
    pydantic>=2.12.3 \
    python-dotenv>=1.1.1 \
    redis>=5.0.0 \
    requests>=2.32.5 \
    resend>=2.19.0 \
    tenacity>=8.0.0 \
    uvicorn>=0.38.0 \
    youtube-transcript-api>=1.2.3

# ============================================
# Stage 3: Runtime
# ============================================
FROM node:22-slim

WORKDIR /app

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy Node.js production dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy built frontend and server from builder
COPY --from=frontend-builder /app/dist ./dist

# Copy server source (needed for imports in dist/index.js)
COPY server/ ./server/
COPY shared/ ./shared/

# Copy Python backend
COPY python_backend/ ./python_backend/

# Copy additional files
COPY pyproject.toml ./
COPY backup_db.sh ./
COPY add_soft_delete.sql ./
COPY ENV_VARIABLES.md ./

# Create necessary directories with proper permissions
RUN mkdir -p attached_assets/avatars \
    attached_assets/custom_experts \
    logs \
    backups && \
    chmod -R 755 attached_assets logs backups

# Expose ports (Node: 3001, Python: 5002)
EXPOSE 3001 5002

# Health check on Node server
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3001/api/health || exit 1

# Set environment
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Copy and prepare startup script
COPY start.sh ./
RUN chmod +x start.sh

# Start application (both Node and Python)
CMD ["./start.sh"]
