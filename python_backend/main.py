from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Body, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from PIL import Image
import io
import json
import asyncio
import asyncpg
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Validate environment variables before proceeding
from env_validator import validate_env, EnvValidationError
try:
    validate_env()
except EnvValidationError as e:
    print(str(e))
    import sys
    sys.exit(1)

# Import structured logger
from logger import logger, log_with_context

# Import database pool
from db_pool import db_pool

# Import file validator
from file_validator import validate_image_file, sanitize_filename, FileValidationError

# Import cache manager
from cache import cache_manager

from models import (
    Expert, ExpertCreate, ExpertType, CategoryType, CategoryInfo,
    Conversation, ConversationCreate,
    Message, MessageCreate, MessageSend, MessageResponse,
    BusinessProfile, BusinessProfileCreate,
    CouncilAnalysis, CouncilAnalysisCreate, AgentContribution,
    RecommendExpertsRequest, RecommendExpertsResponse, ExpertRecommendation,
    AutoCloneRequest,
    UserPersona, UserPersonaCreate, PersonaEnrichmentRequest
)
import uuid
from datetime import datetime
from storage import storage
from crew_agent import LegendAgentFactory
from seed import seed_legends
from crew_council import council_orchestrator
from llm_router import llm_router, LLMTask
from analytics import AnalyticsEngine
from seed_analytics import seed_analytics_data, clear_analytics_data
from clones.registry import CloneRegistry
import bcrypt
import secrets

app = FastAPI(title="O Conselho - Marketing Legends API")

# CORS middleware for frontend integration
# Environment-based origins for security
def get_allowed_origins():
    """Get allowed CORS origins based on environment"""
    env = os.getenv("NODE_ENV", "development")
    
    # Priority 1: Use ALLOWED_ORIGINS if explicitly set (for Dokploy/custom domains)
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
        if origins:
            return origins
    
    # Priority 2: Replit-specific (if REPL_SLUG and REPL_OWNER are set)
    if env == "production":
        replit_domain = os.getenv("REPL_SLUG", "")
        replit_owner = os.getenv("REPL_OWNER", "")
        if replit_domain and replit_owner:
            return [
                f"https://{replit_domain}-{replit_owner}.replit.app",
                f"https://{replit_domain}.{replit_owner}.repl.co",
            ]
    
    # Priority 3: Default - allow localhost (Node server proxies from localhost:3001)
    # This works for Docker/Dokploy where Node and Python run in same container
    if env == "production":
        # In production with Docker, Node server runs on localhost:3001 and proxies to Python
        return ["http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:5000", "http://127.0.0.1:5000"]
    else:
        # Development: allow localhost on ports 3000 and 5000
        return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000"]

allowed_origins = get_allowed_origins()
print(f"[CORS] Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Analytics Engine
analytics_engine = AnalyticsEngine(storage)

# Initialize with seeded legends
@app.on_event("startup")
async def startup_event():
    # Initialize database connection pool
    logger.info("Initializing database connection pool")
    await db_pool.initialize()
    logger.info("Database pool initialized successfully")
    
    # Initialize cache manager
    logger.info("Initializing cache manager")
    await cache_manager.initialize()
    logger.info("Cache manager initialized successfully")
    
    # Initialize PostgreSQL storage
    logger.info("Initializing PostgreSQL storage")
    await storage.initialize()
    logger.info("PostgreSQL storage initialized successfully")
    
    # NOTE: Seed experts are now served from CloneRegistry (18 HIGH_FIDELITY experts with avatars)
    # PostgreSQL only stores CUSTOM experts created by users via /api/experts/auto-clone
    # Seeding disabled to prevent duplicates
    # await seed_legends(storage)
    print("[Startup] Seed experts loaded from CloneRegistry. PostgreSQL ready for custom experts.")

@app.on_event("shutdown")
async def shutdown_event():
    # Close PostgreSQL storage
    logger.info("Closing PostgreSQL storage")
    await storage.close()
    logger.info("PostgreSQL storage closed successfully")
    
    # Close cache manager
    logger.info("Closing cache manager")
    await cache_manager.close()
    logger.info("Cache manager closed successfully")
    
    # Close database connection pool
    logger.info("Closing database connection pool")
    await db_pool.close()
    logger.info("Database pool closed successfully")

# Health check
@app.get("/")
async def root():
    return {"message": "O Conselho Marketing Legends API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Checks database connectivity and pool status.
    """
    try:
        # Check database health
        db_healthy = await db_pool.health_check()
        
        # Get pool stats
        pool_stats = await db_pool.get_pool_stats()
        
        if db_healthy:
            return {
                "status": "healthy",
                "database": "connected",
                "pool": pool_stats,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "pool": pool_stats,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }

# ============================================
# AUTHENTICATION MODELS
# ============================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    inviteCode: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    availableInvites: int
    role: str
    createdAt: datetime
    activePersonaId: Optional[str] = None

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
async def register_user(data: RegisterRequest):
    """Register new user with invite code"""
    
    try:
        logger.debug("Starting registration for {data.email}")
        
        # Validate invite code
        logger.debug("Validating invite code: {data.inviteCode}")
        invite = await storage.get_invite(data.inviteCode)
        if not invite:
            raise HTTPException(status_code=400, detail="Código de convite inválido")
        logger.debug("Invite valid, creator: {invite['creatorId']}")
        
        if invite["usedBy"]:
            raise HTTPException(status_code=400, detail="Este código de convite já foi utilizado")
        
        # Check if email already exists
        logger.debug("Checking if email exists...")
        existing_user = await storage.get_user_by_email(data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        logger.debug("Email is available")
        
        # Hash password
        logger.debug("Hashing password...")
        password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        logger.debug("Creating user...")
        user = await storage.create_user(data.username, data.email, password_hash)
        logger.debug("User created: {user['id']}")
        
        # Mark invite as used
        logger.debug("Marking invite as used...")
        await storage.use_invite(data.inviteCode, user["id"])
        
        # Decrement creator's available invites (skip if creator is system)
        if invite["creatorId"] != "system":
            logger.debug("Decrementing creator invites...")
            creator = await storage.get_user_by_id(invite["creatorId"])
            if creator and creator["availableInvites"] > 0:
                await storage.update_user_invites(invite["creatorId"], creator["availableInvites"] - 1)
        else:
            logger.debug("Skipping decrement for system invite")
        
        logger.debug("Registration successful!")
        
        # Return user with default role (backward compatibility)
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            availableInvites=user["availableInvites"],
            role=user.get("role", "user"),
            createdAt=user["createdAt"],
            activePersonaId=user.get("activePersonaId")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed: {str(e)}")
        logger.error("Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao registrar usuário: {str(e)}")

@app.post("/api/auth/login", response_model=UserResponse)
async def login_user(data: LoginRequest):
    """Login user with email and password"""
    
    # Get user by email
    user = await storage.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    # Verify password
    if not bcrypt.checkpw(data.password.encode('utf-8'), user["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    # Return user without password
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        availableInvites=user["availableInvites"],
        role=user.get("role", "user"),  # Default to 'user' for backward compatibility
        createdAt=user["createdAt"],
        activePersonaId=user.get("activePersonaId")
    )

@app.post("/api/auth/logout")
async def logout_user():
    """Logout user (session management handled by Express)"""
    return {"message": "Logout successful"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(user_id: str):
    """Get current authenticated user (user_id passed from Express session)"""
    user = await storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        availableInvites=user["availableInvites"],
        role=user.get("role", "user"),  # Default to 'user' for backward compatibility
        createdAt=user["createdAt"],
        activePersonaId=user.get("activePersonaId"),
        avatarUrl=user.get("avatarUrl")
    )

# ============================================
# PASSWORD RESET ENDPOINTS
# ============================================

class RequestPasswordResetRequest(BaseModel):
    email: str

class VerifyResetTokenRequest(BaseModel):
    token: str

class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str

@app.post("/api/auth/request-reset")
async def request_password_reset(data: RequestPasswordResetRequest):
    """Request password reset - generates token and sends email"""
    import hashlib
    from datetime import timedelta
    import resend
    
    # Get user by email
    user = await storage.get_user_by_email(data.email)
    if not user:
        # Security: Don't reveal if email exists or not
        return {"message": "Se o email existir, você receberá instruções para redefinir sua senha"}
    
    # Generate secure random token (32 bytes = 64 hex chars)
    token = secrets.token_urlsafe(32)
    
    # Hash token for database storage (SHA-256)
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    
    # Token expires in 1 hour
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store hashed token in database
    await storage.create_password_reset_token(user["id"], hashed_token, expires_at)
    
    # Send email with reset link
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")
    
    if not resend_api_key or not from_email:
        raise HTTPException(status_code=500, detail="Serviço de email não configurado")
    
    resend.api_key = resend_api_key
    
    # Create reset URL (token will be sent as query param)
    reset_url = f"{os.getenv('REPLIT_DOMAINS', 'http://localhost:5000').split(',')[0]}/reset-password?token={token}"
    
    try:
        resend.Emails.send({
            "from": from_email,
            "to": data.email,
            "subject": "O Conselho - Redefinir Senha",
            "html": f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                    <div style="text-align: center; margin-bottom: 40px;">
                        <h1 style="color: #1a1a1a; font-size: 32px; font-weight: 600; margin: 0;">O Conselho</h1>
                        <p style="color: #666; font-size: 16px; margin-top: 8px;">Redefinição de Senha</p>
                    </div>
                    
                    <div style="background: #f9f9f9; border-radius: 16px; padding: 32px; margin-bottom: 24px;">
                        <p style="color: #1a1a1a; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
                            Olá, <strong>{user["username"]}</strong>!
                        </p>
                        <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 24px 0;">
                            Recebemos uma solicitação para redefinir a senha da sua conta. Clique no botão abaixo para criar uma nova senha:
                        </p>
                        <div style="text-align: center; margin: 32px 0;">
                            <a href="{reset_url}" style="display: inline-block; background: #FF6B6B; color: white; text-decoration: none; padding: 16px 32px; border-radius: 12px; font-weight: 600; font-size: 16px;">
                                Redefinir Senha
                            </a>
                        </div>
                        <p style="color: #999; font-size: 14px; line-height: 1.6; margin: 24px 0 0 0;">
                            Este link expira em 1 hora. Se você não solicitou esta redefinição, ignore este email.
                        </p>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                        © 2025 O Conselho. Todos os direitos reservados.
                    </p>
                </div>
            """
        })
    except Exception as e:
        print(f"[Email Error] Failed to send reset email: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar email")
    
    return {"message": "Se o email existir, você receberá instruções para redefinir sua senha"}

@app.post("/api/auth/verify-reset-token")
async def verify_reset_token(data: VerifyResetTokenRequest):
    """Verify if reset token is valid and not expired"""
    import hashlib
    
    # Hash the provided token
    hashed_token = hashlib.sha256(data.token.encode()).hexdigest()
    
    # Get token from database
    token_data = await storage.get_password_reset_token(hashed_token)
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    # Check if token was already used
    if token_data["usedAt"]:
        raise HTTPException(status_code=400, detail="Este link já foi utilizado")
    
    # Check if token is expired
    if token_data["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Este link expirou. Solicite um novo")
    
    # Get user info for display
    user = await storage.get_user_by_id(token_data["userId"])
    
    return {
        "valid": True,
        "email": user["email"] if user else None
    }

@app.post("/api/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using valid token"""
    import hashlib
    
    # Validate new password
    if len(data.newPassword) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")
    
    # Hash the provided token
    hashed_token = hashlib.sha256(data.token.encode()).hexdigest()
    
    # Get token from database
    token_data = await storage.get_password_reset_token(hashed_token)
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    # Check if token was already used
    if token_data["usedAt"]:
        raise HTTPException(status_code=400, detail="Este link já foi utilizado")
    
    # Check if token is expired
    if token_data["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Este link expirou. Solicite um novo")
    
    # Hash new password
    password_hash = bcrypt.hashpw(data.newPassword.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update user password
    success = await storage.update_user_password(token_data["userId"], password_hash)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atualizar senha")
    
    # Mark token as used
    await storage.mark_token_as_used(hashed_token)
    
    return {"message": "Senha redefinida com sucesso"}


class ChangePasswordRequest(BaseModel):
    """Request model for changing password"""
    currentPassword: str
    newPassword: str
    user_id: str  # Injected by Express middleware


@app.post("/api/auth/change-password")
async def change_password(data: ChangePasswordRequest):
    """
    Change password for authenticated user.
    Requires current password for verification.
    """
    import bcrypt
    
    if not data.currentPassword or not data.newPassword:
        raise HTTPException(status_code=400, detail="Senha atual e nova senha são obrigatórias")
    
    if len(data.newPassword) < 6:
        raise HTTPException(status_code=400, detail="Nova senha deve ter pelo menos 6 caracteres")
    
    # Get database connection
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    
    try:
        # Get user from database
        user = await conn.fetchrow(
            'SELECT id, password FROM users WHERE id = $1',
            data.user_id
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Verify current password
        if not bcrypt.checkpw(data.currentPassword.encode('utf-8'), user['password'].encode('utf-8')):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(data.newPassword.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        await conn.execute(
            'UPDATE users SET password = $1 WHERE id = $2',
            new_password_hash, data.user_id
        )
        
        logger.info(f"[AUTH] Password changed for user {data.user_id}")
        
        # Log password change
        await log_audit(
            action="password_change",
            user_id=data.user_id,
            success=True,
            conn=conn
        )
        
        return {"success": True, "message": "Senha atualizada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AUTH] Error changing password: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar senha")
    finally:
        await conn.close()


# ============================================
# SUPERADMIN ENDPOINTS
# ============================================

async def require_superadmin(user_id: str = Query(...)):
    """Dependency to verify superadmin role"""
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        user = await conn.fetchrow("SELECT role FROM users WHERE id = $1", user_id)
        if not user or user['role'] != 'superadmin':
            raise HTTPException(status_code=403, detail="Acesso negado: apenas superadmins")
        return user_id
    finally:
        await conn.close()

@app.get("/api/superadmin/metrics")
async def get_global_metrics(user_id: str = Depends(require_superadmin)):
    """Get global system metrics"""
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
        total_admins = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')") or 0
        total_superadmins = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'superadmin'") or 0
        total_personas = await conn.fetchval("SELECT COUNT(*) FROM user_personas") or 0
        total_experts = await conn.fetchval("SELECT COUNT(*) FROM experts WHERE expert_type = 'custom'") or 0
        total_conversations = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
        total_councils = await conn.fetchval("SELECT COUNT(*) FROM council_analyses") or 0
        total_council_messages = await conn.fetchval("SELECT COUNT(*) FROM council_messages") or 0
        
        # Calculate system health (simple metric)
        system_health = 95
        
        # Average enrichment level
        avg_enrichment_row = await conn.fetchrow("""
            SELECT enrichment_level, COUNT(*) as count
            FROM user_personas
            GROUP BY enrichment_level
            ORDER BY count DESC
            LIMIT 1
        """)
        avg_enrichment = avg_enrichment_row['enrichment_level'] if avg_enrichment_row else "quick"
        
        return {
            "totalUsers": total_users,
            "totalAdmins": total_admins,
            "totalSuperAdmins": total_superadmins,
            "totalPersonas": total_personas,
            "totalExperts": total_experts,
            "totalConversations": total_conversations,
            "totalCouncilAnalyses": total_councils,
            "totalCouncilMessages": total_council_messages,
            "systemHealthScore": system_health,
            "avgEnrichmentLevel": avg_enrichment
        }
    except Exception as e:
        logger.error(f"[SUPERADMIN] Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar métricas")
    finally:
        await conn.close()

@app.get("/api/superadmin/personas")
async def get_all_personas(
    user_id: str = Depends(require_superadmin),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Get all personas in the system (paginated)"""
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        rows = await conn.fetch("""
            SELECT 
                up.id, up.user_id, up.company_name, up.industry,
                up.enrichment_level, up.created_at,
                u.username, u.email
            FROM user_personas up
            LEFT JOIN users u ON up.user_id = u.id
            ORDER BY up.created_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"[SUPERADMIN] Error fetching personas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar personas")
    finally:
        await conn.close()

@app.delete("/api/superadmin/personas/{persona_id}")
async def delete_persona_admin(
    persona_id: str,
    user_id: str = Depends(require_superadmin)
):
    """Delete any persona (soft delete)"""
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        await conn.execute("""
            UPDATE user_personas
            SET deleted_at = NOW()
            WHERE id = $1
        """, persona_id)
        
        logger.info(f"[SUPERADMIN] Persona {persona_id} soft deleted by {user_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"[SUPERADMIN] Error deleting persona: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar persona")
    finally:
        await conn.close()

@app.get("/api/superadmin/analytics/top-experts")
async def get_global_top_experts(
    user_id: str = Depends(require_superadmin),
    limit: int = Query(20)
):
    """Get most consulted experts across ALL users"""
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        rows = await conn.fetch("""
            SELECT 
                ua.metadata->>'expertName' as expert_name,
                COUNT(*) as consultations,
                MAX(ua.created_at) as last_consulted
            FROM user_activity ua
            WHERE ua.metadata->>'expertName' IS NOT NULL
            GROUP BY ua.metadata->>'expertName'
            ORDER BY consultations DESC
            LIMIT $1
        """, limit)
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"[SUPERADMIN] Error fetching top experts: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar experts")
    finally:
        await conn.close()

@app.get("/api/superadmin/export/user/{userId}")
async def export_user_data(
    userId: str,
    admin_user_id: str = Depends(require_superadmin)
):
    """Export all data for a specific user (GDPR compliance)"""
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        # Get user
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", userId)
        
        # Get personas
        personas = await conn.fetch("SELECT * FROM user_personas WHERE user_id = $1", userId)
        
        # Get conversations
        conversations = await conn.fetch("SELECT * FROM conversations WHERE user_id = $1", userId)
        
        # Get council analyses
        councils = await conn.fetch("SELECT * FROM council_analyses WHERE user_id = $1", userId)
        
        export_data = {
            "user": dict(user) if user else None,
            "personas": [dict(p) for p in personas],
            "conversations": [dict(c) for c in conversations],
            "councilAnalyses": [dict(ca) for ca in councils],
            "exportedAt": datetime.utcnow().isoformat(),
            "exportedBy": admin_user_id
        }
        
        logger.info(f"[SUPERADMIN] Data export for user {userId} by {admin_user_id}")
        
        return export_data
    except Exception as e:
        logger.error(f"[SUPERADMIN] Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail="Erro ao exportar dados")
    finally:
        await conn.close()

@app.post("/api/superadmin/invites/add")
async def add_invites_to_user(
    data: dict,
    user_id: str = Depends(require_superadmin)
):
    """Add invite credits to specific user"""
    target_user_id = data.get("userId")
    amount = data.get("amount", 0)
    
    if not target_user_id or amount <= 0:
        raise HTTPException(status_code=400, detail="userId e amount são obrigatórios")
    
    conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
    try:
        await conn.execute("""
            UPDATE users
            SET available_invites = available_invites + $1
            WHERE id = $2
        """, amount, target_user_id)
        
        logger.info(f"[SUPERADMIN] Added {amount} invites to user {target_user_id}")
        
        return {"success": True, "added": amount}
    except Exception as e:
        logger.error(f"[SUPERADMIN] Error adding invites: {e}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar convites")
    finally:
        await conn.close()


# ============================================
# AUDIT LOGGING
# ============================================

class AuditLogRequest(BaseModel):
    action: str
    success: bool
    userId: Optional[str] = None
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    metadata: Optional[dict] = None

@app.post("/api/audit/log")
async def create_audit_log(data: AuditLogRequest):
    """Create an audit log entry (called by Express middleware)"""
    log_id = await storage.create_audit_log(
        action=data.action,
        success=data.success,
        user_id=data.userId,
        ip_address=data.ipAddress,
        user_agent=data.userAgent,
        metadata=data.metadata
    )
    return {"id": log_id}

@app.get("/api/audit/logs")
async def get_audit_logs(
    user_id: str,
    action: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get audit logs for current user"""
    logs = await storage.get_audit_logs(
        user_id=user_id,
        action=action,
        success=success,
        limit=limit,
        offset=offset
    )
    return logs

# ============================================
# INVITE CODE MANAGEMENT
# ============================================

class InviteCodeResponse(BaseModel):
    id: str
    code: str
    creatorId: str
    usedBy: Optional[str]
    usedAt: Optional[datetime]
    createdAt: datetime

@app.post("/api/invites/generate", response_model=InviteCodeResponse, status_code=201)
async def generate_invite(user_id: str):
    """Generate new invite code for user (max 5 total)"""
    
    # Get user
    user = await storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Check if user has available invites
    if user["availableInvites"] <= 0:
        raise HTTPException(status_code=400, detail="Você atingiu o limite de 5 convites")
    
    # Generate random code
    code = secrets.token_urlsafe(12)[:16].upper().replace("-", "").replace("_", "")
    
    # Create invite
    invite = await storage.create_invite(code, user_id)
    
    # Decrement user's available invites
    await storage.update_user_invites(user_id, user["availableInvites"] - 1)
    
    return InviteCodeResponse(**invite)

@app.get("/api/invites/my-codes", response_model=List[InviteCodeResponse])
async def get_my_invites(user_id: str):
    """Get all invite codes created by current user"""
    invites = await storage.get_user_invites(user_id)
    return [InviteCodeResponse(**invite) for invite in invites]

# ============================================
# ONBOARDING SYSTEM
# ============================================

class OnboardingSaveRequest(BaseModel):
    currentStep: Optional[int] = None
    companyName: Optional[str] = None
    industry: Optional[str] = None
    companySize: Optional[str] = None
    targetAudience: Optional[str] = None
    goals: Optional[List[str]] = None
    mainChallenge: Optional[str] = None
    enrichmentLevel: Optional[str] = None

class OnboardingStatusResponse(BaseModel):
    id: str
    userId: str
    currentStep: int
    companyName: Optional[str] = None
    industry: Optional[str] = None
    companySize: Optional[str] = None
    targetAudience: Optional[str] = None
    goals: Optional[List[str]] = None
    mainChallenge: Optional[str] = None
    enrichmentLevel: Optional[str] = None
    completedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

@app.post("/api/onboarding/save", response_model=OnboardingStatusResponse)
async def save_onboarding(data: OnboardingSaveRequest, user_id: str):
    """Save onboarding progress for authenticated user"""
    try:
        logger.debug("Saving onboarding for user: {user_id}")
        logger.debug("Data received: {data}")
        
        # Convert Pydantic model to dict
        onboarding_data = data.model_dump(exclude_unset=True)
        logger.debug("Onboarding data dict: {onboarding_data}")
        
        # Save to database
        result = await storage.save_onboarding_progress(user_id, onboarding_data)
        logger.debug("Save result: {result}")
        
        return OnboardingStatusResponse(**result)
    except Exception as e:
        logger.error("save_onboarding failed: {str(e)}")
        logger.error("Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar progresso: {str(e)}")

@app.get("/api/onboarding/status", response_model=Optional[OnboardingStatusResponse])
async def get_onboarding_status(user_id: str):
    """Get onboarding status for authenticated user"""
    try:
        logger.debug("Getting onboarding status for user: {user_id}")
        result = await storage.get_onboarding_status(user_id)
        
        if not result:
            logger.debug("No onboarding status found for user {user_id}")
            return None
        
        logger.debug("Onboarding status found: {result}")
        return OnboardingStatusResponse(**result)
    except Exception as e:
        logger.error("get_onboarding_status failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar status: {str(e)}")

@app.post("/api/onboarding/complete")
async def complete_onboarding(user_id: str):
    """Mark onboarding as completed for authenticated user"""
    success = await storage.complete_onboarding(user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Onboarding já foi completado ou não existe")
    
    return {"message": "Onboarding completado com sucesso"}

# Expert to Category mapping (manual override for seed experts)
EXPERT_CATEGORY_MAP = {
    "Al Ries": CategoryType.POSITIONING,
    "Ann Handley": CategoryType.CONTENT,
    "Claude Hopkins": CategoryType.DIRECT_RESPONSE,
    "Dan Kennedy": CategoryType.DIRECT_RESPONSE,
    "Daniel Kahneman": CategoryType.PRODUCT,  # Psychology -> Product (behavioral design)
    "David Aaker": CategoryType.MARKETING,  # Brand strategy -> Marketing
    "David Ogilvy": CategoryType.CREATIVE,
    "Donald Miller": CategoryType.CONTENT,
    "Drayton Bird": CategoryType.DIRECT_RESPONSE,
    "Eugene Schwartz": CategoryType.DIRECT_RESPONSE,
    "Gary Vaynerchuk": CategoryType.SOCIAL,
    "Jay Abraham": CategoryType.MARKETING,
    "Jay Levinson": CategoryType.GROWTH,
    "Neil Patel": CategoryType.SEO,
    "Philip Kotler": CategoryType.MARKETING,
    "Robert Cialdini": CategoryType.PRODUCT,  # Psychology -> Product (persuasion/behavioral)
    "Seth Godin": CategoryType.CONTENT,  # Modern marketing -> Content
    "Simon Sinek": CategoryType.MARKETING  # Leadership/branding -> Marketing
}

# Category metadata mapping
CATEGORY_METADATA = {
    CategoryType.MARKETING: {
        "name": "Marketing Tradicional",
        "description": "Estratégias clássicas de marketing, brand building e publicidade",
        "icon": "Megaphone",
        "color": "violet"
    },
    CategoryType.POSITIONING: {
        "name": "Posicionamento Estratégico",
        "description": "Ocupar posição única na mente do consumidor, 22 Leis Imutáveis",
        "icon": "Target",
        "color": "blue"
    },
    CategoryType.CREATIVE: {
        "name": "Criatividade Publicitária",
        "description": "Arte + copy, breakthrough ideas, campanhas que transformam cultura",
        "icon": "Lightbulb",
        "color": "amber"
    },
    CategoryType.DIRECT_RESPONSE: {
        "name": "Direct Response",
        "description": "Copy que converte, funis de vendas, maximização de LTV",
        "icon": "Mail",
        "color": "red"
    },
    CategoryType.CONTENT: {
        "name": "Content Marketing",
        "description": "Storytelling digital, permission marketing, conteúdo que engaja",
        "icon": "FileText",
        "color": "indigo"
    },
    CategoryType.SEO: {
        "name": "SEO & Marketing Digital",
        "description": "Otimização para buscas, marketing orientado por dados",
        "icon": "Search",
        "color": "cyan"
    },
    CategoryType.SOCIAL: {
        "name": "Social Media Marketing",
        "description": "Personal branding, day trading attention, redes sociais",
        "icon": "Users",
        "color": "pink"
    },
    CategoryType.GROWTH: {
        "name": "Growth Hacking",
        "description": "Sistemas de crescimento, loops virais, product-market fit",
        "icon": "TrendingUp",
        "color": "emerald"
    },
    CategoryType.VIRAL: {
        "name": "Marketing Viral",
        "description": "STEPPS framework, word-of-mouth, contagious content",
        "icon": "Share2",
        "color": "orange"
    },
    CategoryType.PRODUCT: {
        "name": "Psicologia do Produto",
        "description": "Habit formation, behavioral design, Hooked Model",
        "icon": "Brain",
        "color": "purple"
    }
}

# Helper function to get a single expert by ID (seed or custom)
async def get_expert_by_id(expert_id: str, include_system_prompt: bool = False) -> Optional[Expert]:
    """
    Get a specific expert by ID, supporting both seed and custom experts.
    
    Args:
        expert_id: Expert ID (seed-* or custom UUID)
        include_system_prompt: If True, includes the full system prompt (for backend use).
                               If False, returns empty systemPrompt (for API responses).
    
    Returns None if expert not found.
    """
    # Check if it's a seed expert (format: seed-expert-name)
    if expert_id.startswith("seed-"):
        # Extract expert name from ID (e.g., "seed-claude-hopkins" -> "Claude Hopkins")
        expert_name_slug = expert_id.replace("seed-", "")
        expert_name = " ".join(word.capitalize() for word in expert_name_slug.split("-"))
        
        # Get clone from CloneRegistry
        clone_registry = CloneRegistry()
        clone_instance = clone_registry.get_clone(expert_name)
        
        if clone_instance:
            # Get category from mapping
            category = EXPERT_CATEGORY_MAP.get(expert_name, CategoryType.MARKETING)
            
            # Get avatar path from clone instance (handles .png, .jpg, etc.)
            avatar_path = getattr(clone_instance, 'avatar', None)
            
            # Get system prompt only if requested (for internal backend use)
            system_prompt = clone_instance.get_system_prompt() if include_system_prompt else ""
            
            return Expert(
                id=expert_id,
                name=expert_name,
                title=clone_instance.title,
                bio=clone_instance.bio,
                expertise=clone_instance.expertise,
                systemPrompt=system_prompt,
                avatar=avatar_path,
                expertType=ExpertType.HIGH_FIDELITY,
                category=category,
            )
        return None
    
    # Otherwise, try to get from PostgreSQL (custom expert)
    expert = await storage.get_expert(expert_id)
    
    # If include_system_prompt is True but expert has no system_prompt, log warning
    if expert and include_system_prompt:
        if not expert.systemPrompt or len(expert.systemPrompt.strip()) == 0:
            print(f"[WARNING] Custom expert {expert.name} (ID: {expert_id}) has empty systemPrompt!")
    
    return expert

# Helper function to get all experts (seed + custom)
async def get_all_experts_combined() -> List[Expert]:
    """
    Helper function to combine seed experts from CloneRegistry with custom experts from PostgreSQL.
    Eliminates code duplication between /api/experts and /api/categories endpoints.
    """
    # Get seed experts from CloneRegistry (HIGH_FIDELITY)
    clone_registry = CloneRegistry()
    all_clones = clone_registry.get_all_clones()
    
    # Convert CloneRegistry clones to Expert objects
    seed_experts = []
    for clone_name, clone_instance in all_clones.items():
        # Generate unique ID for seed expert (stable across restarts)
        expert_id = f"seed-{clone_name.lower().replace(' ', '-')}"
        
        # Get category from manual mapping or use marketing as default
        expert_category = EXPERT_CATEGORY_MAP.get(clone_instance.name, CategoryType.MARKETING)
        
        # Get avatar path if exists
        avatar_path = getattr(clone_instance, 'avatar', None)
        
        seed_expert = Expert(
            id=expert_id,
            name=clone_instance.name,
            title=clone_instance.title,
            expertise=clone_instance.expertise,
            bio=clone_instance.bio,
            avatar=avatar_path,
            systemPrompt=clone_instance.get_system_prompt(),
            expertType=ExpertType.HIGH_FIDELITY,
            category=expert_category,
            createdAt=clone_instance.created_at if hasattr(clone_instance, 'created_at') else datetime.now()
        )
        seed_experts.append(seed_expert)
    
    # Get custom experts from PostgreSQL (CUSTOM)
    custom_experts = await storage.get_experts()
    
    # Combine both sources, but remove duplicates by name
    # Priority: SEED experts (HIGH_FIDELITY) take precedence over DB experts
    seed_names = {expert.name.lower() for expert in seed_experts}
    
    # Filter out custom experts that duplicate seed experts
    unique_custom_experts = [
        expert for expert in custom_experts 
        if expert.name.lower() not in seed_names
    ]
    
    print(f"[DEDUP] SEED experts: {len(seed_experts)}, DB experts: {len(custom_experts)}, Unique DB: {len(unique_custom_experts)}")
    if len(custom_experts) > len(unique_custom_experts):
        removed = len(custom_experts) - len(unique_custom_experts)
        print(f"[DEDUP] Removed {removed} duplicate(s) from DB (already in SEED)")
    
    # Return combined list without duplicates
    return seed_experts + unique_custom_experts

# Expert endpoints
@app.get("/api/experts", response_model=List[Expert])
async def get_experts(category: Optional[str] = None):
    """
    Get all marketing legend experts, optionally filtered by category.
    Combines HIGH_FIDELITY seed experts from CloneRegistry + CUSTOM experts from PostgreSQL.
    
    Query params:
    - category: Filter by category ID (e.g., "growth", "marketing", "content")
    """
    try:
        print("[DEBUG] Getting experts, category filter:", category)
        # Get all experts using shared helper
        all_experts = await get_all_experts_combined()
        logger.debug("Total experts loaded: {len(all_experts)}")
        
        # Filter by category if provided
        if category:
            all_experts = [e for e in all_experts if e.category.value == category]
            logger.debug("After category filter: {len(all_experts)}")
        
        return all_experts
    except Exception as e:
        logger.error("Failed to get experts: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar experts: {str(e)}")

@app.get("/api/categories", response_model=List[CategoryInfo])
async def get_categories():
    """Get all available categories with expert counts, sorted by count (descending)"""
    # Get all experts using shared helper
    all_experts = await get_all_experts_combined()
    
    # Count experts per category
    category_counts = {}
    for expert in all_experts:
        cat = expert.category
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Build category info list
    categories = []
    for cat_type, metadata in CATEGORY_METADATA.items():
        count = category_counts.get(cat_type, 0)
        if count > 0:  # Only return categories with at least one expert
            categories.append(CategoryInfo(
                id=cat_type.value,
                name=metadata["name"],
                description=metadata["description"],
                icon=metadata["icon"],
                color=metadata["color"],
                expertCount=count
            ))
    
    # Sort by expert count descending, then by name
    categories.sort(key=lambda x: (-x.expertCount, x.name))
    return categories

@app.get("/api/experts/auto-clone-stream")
async def auto_clone_expert_stream(targetName: str, context: str = ""):
    """
    Stream real-time progress during expert auto-clone process.
    Disney Effect #2: User sees every step happening live.
    
    Events sent:
    - step-start: When a new step begins (researching, analyzing, synthesizing)
    - step-progress: Detailed progress within a step
    - step-complete: When a step finishes
    - expert-complete: Final expert data
    - error: If something goes wrong
    """
    async def event_generator():
        def send_event(event_type: str, data: dict):
            """Format SSE event"""
            return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        try:
            import httpx
            from anthropic import AsyncAnthropic
            
            # STEP 1: Perplexity Research
            yield send_event("step-start", {
                "step": "researching",
                "message": "Pesquisando biografia, filosofia e métodos..."
            })
            
            perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
            if not perplexity_api_key:
                yield send_event("error", {
                    "message": "Serviço de pesquisa indisponível. Configure PERPLEXITY_API_KEY."
                })
                return
            
            context_suffix = f" Foco: {context}" if context else ""
            research_query = f"""Pesquise informações detalhadas sobre {targetName}{context_suffix}.

Forneça:
1. Biografia completa e trajetória profissional
2. Filosofia de trabalho e princípios fundamentais
3. Métodos, frameworks e técnicas específicas
4. Frases icônicas e terminologia única
5. Áreas de expertise e contextos de especialidade
6. Limitações reconhecidas ou fronteiras de atuação

Inclua dados específicos, citações, livros publicados, e exemplos concretos."""

            yield send_event("step-progress", {
                "step": "researching",
                "message": f"Consultando base de conhecimento sobre {targetName}..."
            })

            async with httpx.AsyncClient(timeout=90.0) as client:
                perplexity_response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Você é um pesquisador especializado em biografias profissionais e análise de personalidades. Forneça informações factuais, detalhadas e específicas."
                            },
                            {
                                "role": "user",
                                "content": research_query
                            }
                        ],
                        "temperature": 0.2,
                        "search_recency_filter": "month",
                        "return_related_questions": False
                    }
                )
            
            # Check response status before parsing JSON
            if perplexity_response.status_code != 200:
                error_msg = f"Perplexity API error: {perplexity_response.status_code}"
                print(f"[AUTO-CLONE-STREAM] {error_msg}")
                print(f"[AUTO-CLONE-STREAM] Response text: {perplexity_response.text[:500]}")
                yield send_event("error", {
                    "message": f"Erro na pesquisa (código {perplexity_response.status_code})"
                })
                return
            
            try:
                perplexity_data = perplexity_response.json()
            except Exception as e:
                error_msg = f"Failed to parse Perplexity response: {str(e)}"
                print(f"[AUTO-CLONE-STREAM] {error_msg}")
                print(f"[AUTO-CLONE-STREAM] Response text: {perplexity_response.text[:500]}")
                yield send_event("error", {
                    "message": "Erro ao processar resposta da pesquisa"
                })
                return
            
            research_findings = ""
            if "choices" in perplexity_data and len(perplexity_data["choices"]) > 0:
                research_findings = perplexity_data["choices"][0]["message"]["content"]
            
            if not research_findings:
                yield send_event("error", {
                    "message": "Nenhum resultado de pesquisa foi encontrado"
                })
                return
            
            yield send_event("step-complete", {
                "step": "researching",
                "message": f"✅ Pesquisa sobre {targetName} concluída"
            })

            # STEP 2: YouTube Research
            yield send_event("step-start", {
                "step": "analyzing",
                "message": "Analisando vídeos e palestras no YouTube..."
            })
            
            youtube_data_str = ""
            youtube_api_key = os.getenv("YOUTUBE_API_KEY")
            
            if youtube_api_key:
                try:
                    from tools.youtube_api import YouTubeAPITool
                    
                    yield send_event("step-progress", {
                        "step": "analyzing",
                        "message": f"Buscando vídeos e palestras de {targetName}..."
                    })
                    
                    youtube_api = YouTubeAPITool()
                    queries = [
                        f"{targetName} palestra",
                        f"{targetName} entrevista",
                        f"{targetName} talk",
                        f"{targetName} keynote"
                    ]
                    
                    youtube_results = []
                    for query in queries[:2]:
                        result = await youtube_api.search_videos(
                            query=query,
                            max_results=5,
                            order="relevance",
                            region_code="BR"
                        )
                        
                        if result.get("videos"):
                            youtube_results.extend(result["videos"])
                    
                    await youtube_api.close()
                    
                    # Extract transcripts
                    if youtube_results:
                        yield send_event("step-progress", {
                            "step": "analyzing",
                            "message": f"Extraindo transcrições de {len(youtube_results[:5])} vídeos..."
                        })
                        
                        from tools.youtube_transcript import YouTubeTranscriptTool
                        transcript_tool = YouTubeTranscriptTool()
                        
                        transcripts_str = ""
                        for i, video in enumerate(youtube_results[:5], 1):
                            video_id = video.get('videoId')
                            if not video_id:
                                continue
                            
                            transcript = transcript_tool.get_transcript(video_id)
                            
                            if transcript:
                                max_chars = 5000
                                transcript_preview = transcript[:max_chars]
                                if len(transcript) > max_chars:
                                    transcript_preview += "\n... [TRANSCRIÇÃO TRUNCADA]"
                                
                                transcripts_str += f"\n\n### TRANSCRIÇÃO {i}: {video['title']}\n{transcript_preview}"
                        
                        # Build YouTube summary
                        if youtube_results[:10]:
                            youtube_summary_parts = [f"\n\n### VÍDEOS E PALESTRAS ENCONTRADOS (YouTube Data API v3):\n"]
                            
                            for i, video in enumerate(youtube_results[:10], 1):
                                youtube_summary_parts.append(f"""
{i}. **{video['title']}**
   - Canal: {video['channelTitle']}
   - Views: {video['viewCount']:,}
   - Likes: {video['likeCount']:,}
   - Publicado: {video['publishedAt']}
   - Link: https://www.youtube.com/watch?v={video['videoId']}
""")
                            
                            youtube_data_str = "".join(youtube_summary_parts)
                            
                            if transcripts_str:
                                youtube_data_str += f"\n\n### TRANSCRIÇÕES COMPLETAS (YouTube Transcript API):{transcripts_str}"
                
                except Exception as e:
                    print(f"[AUTO-CLONE-STREAM] YouTube error: {str(e)}")
            
            yield send_event("step-complete", {
                "step": "analyzing",
                "message": "✅ Análise de conteúdo concluída"
            })

            # STEP 3: Claude Synthesis
            yield send_event("step-start", {
                "step": "synthesizing",
                "message": "Sintetizando clone cognitivo de alta fidelidade..."
            })
            
            yield send_event("step-progress", {
                "step": "synthesizing",
                "message": "Aplicando Framework EXTRACT (20 pontos)..."
            })
            
            # Use the exact same synthesis logic as the original endpoint
            synthesis_prompt = f"""Você é um especialista em clonagem cognitiva. Crie um especialista cognitivo de alta fidelidade para: {targetName}

DADOS DE PESQUISA:
{research_findings}

ANÁLISE DE VÍDEOS E PALESTRAS (YouTube):
{youtube_data_str if youtube_data_str else "Nenhum dado de vídeo disponível"}

INSTRUÇÕES:
Crie um clone cognitivo seguindo Framework EXTRACT (20 pontos). Retorne JSON:

{{
  "name": "Nome Completo",
  "title": "Título profissional em 1 linha",
  "expertise": ["skill1", "skill2", "skill3"],
  "bio": "Bio de 2-3 frases",
  "systemPrompt": "System prompt de 350+ linhas implementando todos os 20 pontos do Framework EXTRACT"
}}

O systemPrompt DEVE incluir:
1. ESSÊNCIA (personalidade, valores, filosofia)
2. EXPERTISE (conhecimentos, frameworks, métodos)
3. STORYTELLING (histórias, casos, exemplos)
4. TERMINOLOGIA (jargões, frases icônicas)
5. RACIOCÍNIO (lógica, padrões de pensamento)
6. ADAPTAÇÃO (contextos, fronteiras)
7. CONVERSAÇÃO (tom, estilo, cadência)
8. TRANSFORMAÇÃO (impacto, metodologia)

Retorne APENAS JSON válido."""

            anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            synthesis_response = await anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": synthesis_prompt
                }]
            )
            
            synthesis_text = ""
            for block in synthesis_response.content:
                if block.type == "text":
                    synthesis_text += block.text
            
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', synthesis_text, re.DOTALL)
            if not json_match:
                yield send_event("error", {
                    "message": "Falha ao extrair dados estruturados da síntese"
                })
                return
            
            expert_data = json.loads(json_match.group(0))
            
            # CRITICAL: Validate that systemPrompt exists and is not empty
            if "systemPrompt" not in expert_data or not expert_data["systemPrompt"] or len(expert_data["systemPrompt"].strip()) < 100:
                print(f"[AUTO-CLONE-STREAM] ERROR: systemPrompt is missing or too short!")
                print(f"[AUTO-CLONE-STREAM] systemPrompt length: {len(expert_data.get('systemPrompt', ''))}")
                yield send_event("error", {
                    "message": "Erro: Clone cognitivo gerado sem prompt válido. Tente novamente."
                })
                return
            
            print(f"[AUTO-CLONE-STREAM] ✅ systemPrompt generated: {len(expert_data['systemPrompt'])} chars")
            
            yield send_event("step-complete", {
                "step": "synthesizing",
                "message": "✅ Clone cognitivo sintetizado com sucesso!"
            })
            
            # Disney Effect #3: Auto-generate professional avatar
            yield send_event("step-start", {
                "step": "avatar-generation",
                "message": "🎨 Gerando avatar profissional..."
            })
            
            avatar_path = None
            try:
                # Search for professional headshot/portrait
                search_query = f"{targetName} professional headshot portrait"
                
                yield send_event("step-progress", {
                    "step": "avatar-generation",
                    "message": f"Buscando foto profissional de {targetName}..."
                })
                
                # Use httpx to search Unsplash API for professional images
                unsplash_access_key = "oRHXEqW-2Oa-w6BjcKZZy3RH_80svgXRbIJlJRAL_5k"  # Public demo key
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    unsplash_response = await client.get(
                        "https://api.unsplash.com/search/photos",
                        params={
                            "query": search_query,
                            "per_page": 1,
                            "orientation": "squarish"
                        },
                        headers={
                            "Authorization": f"Client-ID {unsplash_access_key}"
                        }
                    )
                    
                    if unsplash_response.status_code == 200:
                        unsplash_data = unsplash_response.json()
                        
                        if unsplash_data.get("results") and len(unsplash_data["results"]) > 0:
                            image_url = unsplash_data["results"][0]["urls"]["regular"]
                            
                            # Download image
                            yield send_event("step-progress", {
                                "step": "avatar-generation",
                                "message": "Baixando e otimizando avatar..."
                            })
                            
                            image_response = await client.get(image_url)
                            
                            if image_response.status_code == 200:
                                # Save to attached_assets/custom_experts/
                                custom_experts_dir = Path("attached_assets/custom_experts")
                                custom_experts_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Sanitize filename
                                safe_name = "".join(c for c in targetName if c.isalnum() or c in (' ', '-', '_')).strip()
                                avatar_filename = f"{safe_name}.jpg"
                                avatar_full_path = custom_experts_dir / avatar_filename
                                
                                # Resize and optimize with PIL
                                img = Image.open(io.BytesIO(image_response.content))
                                
                                # Resize to 400x400 for optimal avatar size
                                img = img.resize((400, 400), Image.Resampling.LANCZOS)
                                
                                # Convert to RGB if needed
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                
                                # Save as JPEG
                                img.save(avatar_full_path, "JPEG", quality=85, optimize=True)
                                
                                # Set relative path for frontend
                                avatar_path = f"custom_experts/{avatar_filename}"
                                
                                print(f"[AUTO-CLONE-STREAM] ✅ Avatar saved: {avatar_full_path}")
                
                if avatar_path:
                    yield send_event("step-complete", {
                        "step": "avatar-generation",
                        "message": "✅ Avatar profissional gerado!"
                    })
                else:
                    yield send_event("step-complete", {
                        "step": "avatar-generation",
                        "message": "⚠️ Avatar não encontrado, usando placeholder"
                    })
            
            except Exception as e:
                print(f"[AUTO-CLONE-STREAM] Avatar generation error: {str(e)}")
                yield send_event("step-complete", {
                    "step": "avatar-generation",
                    "message": "⚠️ Erro ao gerar avatar, usando placeholder"
                })
            
            # Disney Effect #4: Calculate cognitive fidelity score (0-20 points)
            yield send_event("step-start", {
                "step": "score-calculation",
                "message": "📊 Calculando fidelidade cognitiva..."
            })
            
            cognitive_score = 0
            score_breakdown = {}
            
            try:
                system_prompt = expert_data.get("systemPrompt", "")
                
                # Analyze Framework EXTRACT implementation (20 points total)
                # Each category worth 2-3 points
                score_breakdown = {
                    "essencia": 0,  # ESSÊNCIA: personality, values, philosophy (3 points)
                    "expertise": 0,  # EXPERTISE: knowledge, frameworks, methods (3 points)
                    "storytelling": 0,  # STORYTELLING: stories, cases, examples (2 points)
                    "terminologia": 0,  # TERMINOLOGIA: jargon, iconic phrases (2 points)
                    "raciocinio": 0,  # RACIOCÍNIO: logic, thinking patterns (3 points)
                    "adaptacao": 0,  # ADAPTAÇÃO: contexts, boundaries (2 points)
                    "conversacao": 0,  # CONVERSAÇÃO: tone, style, cadence (2 points)
                    "transformacao": 0  # TRANSFORMAÇÃO: impact, methodology (3 points)
                }
                
                # Simple keyword-based analysis (can be enhanced with LLM later)
                prompt_lower = system_prompt.lower()
                
                # ESSÊNCIA (3 points)
                essencia_keywords = ["personalidade", "valores", "filosofia", "essência", "princípios"]
                score_breakdown["essencia"] = min(3, sum(1 for kw in essencia_keywords if kw in prompt_lower))
                
                # EXPERTISE (3 points)
                expertise_keywords = ["expertise", "conhecimento", "framework", "método", "técnica"]
                score_breakdown["expertise"] = min(3, sum(1 for kw in expertise_keywords if kw in prompt_lower))
                
                # STORYTELLING (2 points)
                storytelling_keywords = ["história", "caso", "exemplo", "experiência"]
                score_breakdown["storytelling"] = min(2, sum(1 for kw in storytelling_keywords if kw in prompt_lower))
                
                # TERMINOLOGIA (2 points)
                terminologia_keywords = ["terminologia", "jargão", "frase", "vocabulário"]
                score_breakdown["terminologia"] = min(2, sum(1 for kw in terminologia_keywords if kw in prompt_lower))
                
                # RACIOCÍNIO (3 points)
                raciocinio_keywords = ["raciocínio", "lógica", "pensamento", "análise", "decisão"]
                score_breakdown["raciocinio"] = min(3, sum(1 for kw in raciocinio_keywords if kw in prompt_lower))
                
                # ADAPTAÇÃO (2 points)
                adaptacao_keywords = ["contexto", "adaptação", "limite", "fronteira", "situação"]
                score_breakdown["adaptacao"] = min(2, sum(1 for kw in adaptacao_keywords if kw in prompt_lower))
                
                # CONVERSAÇÃO (2 points)
                conversacao_keywords = ["tom", "estilo", "cadência", "comunicação", "voz"]
                score_breakdown["conversacao"] = min(2, sum(1 for kw in conversacao_keywords if kw in prompt_lower))
                
                # TRANSFORMAÇÃO (3 points)
                transformacao_keywords = ["impacto", "transformação", "metodologia", "resultado", "mudança"]
                score_breakdown["transformacao"] = min(3, sum(1 for kw in transformacao_keywords if kw in prompt_lower))
                
                # Calculate total score (0-20)
                cognitive_score = sum(score_breakdown.values())
                
                # Boost score based on system prompt length (longer = more comprehensive)
                if len(system_prompt) > 2000:
                    cognitive_score = min(20, cognitive_score + 2)
                elif len(system_prompt) > 1000:
                    cognitive_score = min(20, cognitive_score + 1)
                
                yield send_event("step-complete", {
                    "step": "score-calculation",
                    "message": f"✅ Score: {cognitive_score}/20 pontos de fidelidade"
                })
            
            except Exception as e:
                print(f"[AUTO-CLONE-STREAM] Score calculation error: {str(e)}")
                cognitive_score = 15  # Default fallback score
                yield send_event("step-complete", {
                    "step": "score-calculation",
                    "message": "⚠️ Score estimado: 15/20 pontos"
                })
            
            # STEP 7: Infer best category using Claude Haiku
            yield send_event("step-start", {
                "step": "category-inference",
                "message": "Classificando especialização..."
            })
            
            try:
                category_prompt = f"""Baseado no seguinte especialista, identifique a MELHOR categoria de especialização.

ESPECIALISTA: {targetName}
TÍTULO: {expert_data.get('title', '')}
BIO: {expert_data.get('bio', '')[:300]}
CONTEXTO: {context}

CATEGORIAS DISPONÍVEIS:
- marketing: Marketing tradicional, estratégia clássica, brand building
- positioning: Posicionamento estratégico, diferenciação, nicho
- creative: Publicidade criativa, storytelling visual
- direct_response: Marketing de resposta direta, funis, copywriting
- content: Content marketing, blogging, inbound
- seo: SEO, marketing digital, analytics
- social: Social media marketing, influencer, redes sociais
- growth: Growth hacking, loops virais, product-market fit, sistemas de crescimento
- viral: Marketing viral, word-of-mouth, buzz marketing
- product: Psicologia do produto, hábitos, UX

Responda APENAS com o ID da categoria (ex: "growth"), nada mais."""

                response = await anthropic_client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=20,
                    system="Você é um classificador expert. Responda apenas com o ID da categoria.",
                    messages=[{
                        "role": "user",
                        "content": category_prompt
                    }]
                )
                
                inferred_category = "marketing"  # Default fallback
                for block in response.content:
                    if block.type == "text":
                        inferred_category = block.text.strip().lower()
                        break
                
                # Validate category and convert to CategoryType enum
                category_map = {
                    "marketing": CategoryType.MARKETING,
                    "positioning": CategoryType.POSITIONING,
                    "creative": CategoryType.CREATIVE,
                    "direct_response": CategoryType.DIRECT_RESPONSE,
                    "content": CategoryType.CONTENT,
                    "seo": CategoryType.SEO,
                    "social": CategoryType.SOCIAL,
                    "growth": CategoryType.GROWTH,
                    "viral": CategoryType.VIRAL,
                    "product": CategoryType.PRODUCT
                }
                
                inferred_category_enum = category_map.get(inferred_category.lower(), CategoryType.MARKETING)
                
                print(f"[AUTO-CLONE-STREAM] Inferred category: {inferred_category} -> {inferred_category_enum.value}")
                yield send_event("step-complete", {
                    "step": "category-inference",
                    "message": f"✅ Categoria: {inferred_category_enum.value}"
                })
            
            except Exception as e:
                print(f"[AUTO-CLONE-STREAM] Category inference error: {str(e)}")
                inferred_category_enum = CategoryType.MARKETING
                yield send_event("step-complete", {
                    "step": "category-inference",
                    "message": "⚠️ Categoria padrão: marketing"
                })
            
            # Add metadata
            expert_data["categories"] = []
            expert_data["type"] = "CUSTOM"
            expert_data["stories"] = []
            expert_data["avatar"] = avatar_path  # Set avatar path
            expert_data["cognitiveScore"] = cognitive_score
            expert_data["scoreBreakdown"] = score_breakdown
            expert_data["category"] = inferred_category_enum.value  # AI-inferred category as string value
            
            # Final expert data
            yield send_event("expert-complete", {
                "expert": expert_data
            })
            
        except Exception as e:
            print(f"[AUTO-CLONE-STREAM] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            yield send_event("error", {
                "message": f"Erro durante clonagem: {str(e)}"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# Expert Recommendations endpoint (MUST be BEFORE /api/experts/{expert_id})
@app.get("/api/experts/recommendations")
async def get_expert_recommendations():
    """
    Get expert recommendations based on user's business profile.
    Returns experts with relevance scores, star ratings, and justifications.
    """
    try:
        from recommendation import recommendation_engine
        
        # Get user's business profile
        user_id = "default_user"
        profile = await storage.get_business_profile(user_id)
        
        # Get all experts
        experts = await storage.get_experts()
        if not experts:
            raise HTTPException(status_code=404, detail="No experts available")
        
        # Get recommendations
        recommendations = recommendation_engine.get_recommendations(experts, profile)
        
        # Format response
        return {
            "hasProfile": profile is not None,
            "recommendations": recommendations
        }
    
    except Exception as e:
        logger.error("Error getting recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )

@app.get("/api/experts/{expert_id}", response_model=Expert)
async def get_expert(expert_id: str):
    """Get a specific expert by ID (supports both seed and custom experts)"""
    expert = await get_expert_by_id(expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert

@app.post("/api/experts", response_model=Expert, status_code=201)
async def create_expert(data: ExpertCreate):
    """Create a new custom expert (cognitive clone)"""
    try:
        print(f"[CREATE-EXPERT] Received expert: {data.name}, category: {data.category.value if hasattr(data.category, 'value') else data.category}")
        expert = await storage.create_expert(data)
        print(f"[CREATE-EXPERT] Saved expert with ID: {expert.id}, category: {expert.category.value}")
        
        # CRITICAL FIX: If this is a custom expert, save Python class file and reload registry
        if data.expertType == ExpertType.CUSTOM:
            try:
                # Ensure custom directory exists
                custom_dir = Path("python_backend/clones/custom")
                custom_dir.mkdir(parents=True, exist_ok=True)
                
                # Validate Anthropic API key
                anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
                if not anthropic_api_key:
                    raise HTTPException(
                        status_code=500,
                        detail="ANTHROPIC_API_KEY not configured - cannot generate Python class"
                    )
                
                from anthropic import AsyncAnthropic
                anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
                
                # Generate Python class from expert data
                python_class_prompt = f"""Você é um expert em criar código Python para clones cognitivos.

TAREFA: Converta os dados do especialista abaixo em uma classe Python completa que herda de ExpertCloneBase.

EXPERT DATA:
Nome: {data.name}
Título: {data.title}
Bio: {data.bio}
Expertise: {data.expertise}
System Prompt (Framework EXTRACT):
{data.systemPrompt}

INSTRUÇÕES:
1. Classe deve herdar de `from clones.base import ExpertCloneBase`
2. Implemente __init__ com name, title, bio, expertise, story_banks
3. story_banks deve ter pelo menos 1 story bank com 3-5 histórias derivadas do system prompt
4. Use \" para strings (não aspas simples)
5. Retorne APENAS código Python, sem markdown
6. Classe deve ser executável imediatamente

RETORNE APENAS O CÓDIGO PYTHON:"""

                python_response = await anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8192,
                    temperature=0.2,
                    messages=[{
                        "role": "user",
                        "content": python_class_prompt
                    }]
                )
                
                python_code = ""
                for block in python_response.content:
                    if block.type == "text":
                        python_code += block.text
                
                # Clean Python code
                python_code_clean = python_code.strip()
                if python_code_clean.startswith("```python"):
                    python_code_clean = python_code_clean.split("```python")[1].split("```")[0].strip()
                elif python_code_clean.startswith("```"):
                    python_code_clean = python_code_clean.split("```")[1].split("```")[0].strip()
                
                # Save Python class file
                import re
                filename = re.sub(r'[^a-zA-Z0-9_]', '_', data.name.lower())
                filename = re.sub(r'_+', '_', filename).strip('_')
                filepath = f"python_backend/clones/custom/{filename}.py"
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(python_code_clean)
                
                print(f"[CREATE-EXPERT] ✅ Python class saved to {filepath}")
                
                # CRITICAL: Use singleton instance to reload registry
                print(f"[CREATE-EXPERT] Reloading global CloneRegistry singleton...")
                clone_registry = CloneRegistry()  # Gets existing singleton instance
                clone_registry.reload_clones()    # Reloads all clones in the shared instance
                print(f"[CREATE-EXPERT] ✅ CloneRegistry reloaded - expert now accessible globally!")
                
            except Exception as py_error:
                print(f"[CREATE-EXPERT] Warning: Failed to save Python class: {str(py_error)}")
                # Don't fail the whole request if Python generation fails
                # Expert is still saved in storage
        
        return expert
    except Exception as e:
        print(f"[CREATE-EXPERT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create expert: {str(e)}")

@app.post("/api/experts/auto-clone", response_model=ExpertCreate, status_code=200)
async def auto_clone_expert(data: AutoCloneRequest):
    """
    Auto-clone a cognitive expert from minimal input using multi-source research.
    
    Process:
    1. Perplexity API: Research biography, philosophy, methods, frameworks
    2. YouTube API: Search for videos, lectures, interviews (top 10 most relevant)
    3. Claude Synthesis: Create EXTRACT system prompt (20 points) from combined research
    4. Return ExpertCreate data (NOT persisted yet - user must explicitly save)
    
    YouTube integration provides:
    - Video titles, channels, view counts, likes, publish dates
    - Insights into communication style and public appearances
    - Verification of authenticity through real content
    """
    try:
        import httpx
        from anthropic import AsyncAnthropic
        
        # Step 1: Perplexity research
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not perplexity_api_key:
            raise HTTPException(
                status_code=503,
                detail="Serviço de pesquisa indisponível. Configure PERPLEXITY_API_KEY."
            )
        
        # Build research query
        context_suffix = f" Foco: {data.context}" if data.context else ""
        research_query = f"""Pesquise informações detalhadas sobre {data.targetName}{context_suffix}.

Forneça:
1. Biografia completa e trajetória profissional
2. Filosofia de trabalho e princípios fundamentais
3. Métodos, frameworks e técnicas específicas
4. Frases icônicas e terminologia única
5. Áreas de expertise e contextos de especialidade
6. Limitações reconhecidas ou fronteiras de atuação

Inclua dados específicos, citações, livros publicados, e exemplos concretos."""

        # Call Perplexity API
        async with httpx.AsyncClient(timeout=90.0) as client:
            perplexity_response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um pesquisador especializado em biografias profissionais e análise de personalidades. Forneça informações factuais, detalhadas e específicas."
                        },
                        {
                            "role": "user",
                            "content": research_query
                        }
                    ],
                    "temperature": 0.2,
                    "search_recency_filter": "month",
                    "return_related_questions": False
                }
            )
        
        perplexity_data = perplexity_response.json()
        
        # Extract research findings
        research_findings = ""
        if "choices" in perplexity_data and len(perplexity_data["choices"]) > 0:
            research_findings = perplexity_data["choices"][0]["message"]["content"]
        
        if not research_findings:
            raise ValueError("Nenhum resultado de pesquisa foi encontrado")
        
        # Step 2: YouTube research (videos, lectures, interviews)
        youtube_data_str = ""
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        if youtube_api_key:
            try:
                from tools.youtube_api import YouTubeAPITool
                
                print(f"[AUTO-CLONE] Searching YouTube for videos of {data.targetName}...")
                youtube_api = YouTubeAPITool()
                
                # Generate search queries for the target person
                queries = [
                    f"{data.targetName} palestra",
                    f"{data.targetName} entrevista",
                    f"{data.targetName} talk",
                    f"{data.targetName} keynote"
                ]
                
                # Search YouTube for each query (max 5 videos per query)
                youtube_results = []
                for query in queries[:2]:  # Limit to 2 queries to avoid rate limits
                    result = await youtube_api.search_videos(
                        query=query,
                        max_results=5,
                        order="relevance",
                        region_code="BR"
                    )
                    
                    if result.get("videos"):
                        youtube_results.extend(result["videos"])
                        print(f"[AUTO-CLONE] Query '{query}': Found {len(result['videos'])} videos")
                
                await youtube_api.close()
                
                # Step 2.5: Extract transcripts from videos
                transcripts_str = ""
                if youtube_results:
                    print(f"[AUTO-CLONE] Extracting transcripts from {len(youtube_results[:5])} videos...")
                    
                    from tools.youtube_transcript import YouTubeTranscriptTool
                    transcript_tool = YouTubeTranscriptTool()
                    
                    # Extract transcripts from top 5 videos (to avoid excessive token usage)
                    transcripts_extracted = 0
                    for i, video in enumerate(youtube_results[:5], 1):
                        video_id = video.get('videoId')
                        if not video_id:
                            continue
                        
                        print(f"[AUTO-CLONE] Extracting transcript {i}/5 from: {video['title'][:50]}...")
                        transcript = transcript_tool.get_transcript(video_id)
                        
                        if transcript:
                            # Limit transcript length to avoid excessive tokens
                            max_chars = 5000  # ~1250 tokens per transcript
                            transcript_preview = transcript[:max_chars]
                            if len(transcript) > max_chars:
                                transcript_preview += "\n... [TRANSCRIÇÃO TRUNCADA]"
                            
                            transcripts_str += f"\n\n### TRANSCRIÇÃO {i}: {video['title']}\n"
                            transcripts_str += f"Canal: {video['channelTitle']} | Visualizações: {video['statistics']['viewCount']:,}\n"
                            transcripts_str += f"---\n{transcript_preview}\n"
                            
                            transcripts_extracted += 1
                            print(f"[AUTO-CLONE] ✅ Transcript {i} extracted ({len(transcript)} chars)")
                        else:
                            print(f"[AUTO-CLONE] ⚠️ No transcript available for video {i}")
                    
                    print(f"[AUTO-CLONE] Total transcripts extracted: {transcripts_extracted}/{len(youtube_results[:5])}")
                
                # Format YouTube data for synthesis
                if youtube_results:
                    youtube_data_str = "\n\nVÍDEOS E PALESTRAS ENCONTRADOS NO YOUTUBE:\n"
                    for i, video in enumerate(youtube_results[:10], 1):  # Top 10 videos
                        youtube_data_str += f"\n{i}. **{video['title']}**\n"
                        youtube_data_str += f"   - Canal: {video['channelTitle']}\n"
                        youtube_data_str += f"   - Visualizações: {video['statistics']['viewCount']:,}\n"
                        youtube_data_str += f"   - Likes: {video['statistics']['likeCount']:,}\n"
                        youtube_data_str += f"   - Data: {video['publishedAt'][:10]}\n"
                        youtube_data_str += f"   - URL: {video['url']}\n"
                    
                    # Add transcripts section
                    if transcripts_str:
                        youtube_data_str += transcripts_str
                    
                    print(f"[AUTO-CLONE] Total YouTube videos found: {len(youtube_results)}")
                else:
                    print(f"[AUTO-CLONE] No YouTube videos found for {data.targetName}")
            
            except Exception as e:
                print(f"[AUTO-CLONE] YouTube API error (non-critical): {str(e)}")
                # Continue without YouTube data - it's supplementary, not critical
        else:
            print("[AUTO-CLONE] YouTube API key not configured - skipping video research")
        
        # Step 3: Claude synthesis into EXTRACT system prompt
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        synthesis_prompt = f"""Você é um especialista em clonagem cognitiva usando o Framework EXTRACT de 20 pontos.

FONTES DE PESQUISA SOBRE {data.targetName}:

📚 PESQUISA BIOGRÁFICA (Perplexity):
{research_findings}

🎥 VÍDEOS E TRANSCRIÇÕES (YouTube):
{youtube_data_str}

INSTRUÇÕES CRÍTICAS PARA SÍNTESE:
1. **PRIORIZE AS TRANSCRIÇÕES**: As transcrições de vídeos são a fonte MAIS VALIOSA pois capturam:
   - Tom de voz e estilo de comunicação AUTÊNTICO
   - Frases icônicas EXATAS (use aspas duplas para citações)
   - Padrões de raciocínio em contexto real
   - Terminologia única e jargões do especialista
   
2. **EXTRAIA CITAÇÕES LITERAIS**: Sempre que possível, use frases EXATAS das transcrições em:
   - Iconic Callbacks
   - Axiomas Pessoais
   - Controversial Takes
   - Signature Response Patterns

3. **IDENTIFIQUE PADRÕES REAIS**: Use as transcrições para mapear:
   - Como o especialista ESTRUTURA suas respostas
   - Que analogias/metáforas usa frequentemente
   - Seu tom (pragmático, filosófico, agressivo, etc.)

TAREFA: Sintetize essas informações em um system prompt EXTRACT COMPLETO (20 pontos) de MÁXIMA FIDELIDADE COGNITIVA (19-20/20).

CRITÉRIOS DE QUALIDADE 19-20/20:
✓ TODOS os 20 pontos implementados com profundidade
✓ 3-5 Story Banks documentados com métricas ESPECÍFICAS (use casos reais da pesquisa)
✓ 5-7 Iconic Callbacks únicos ao especialista (CITAÇÕES EXATAS das transcrições)
✓ Protocolo de Recusa completo com redirecionamentos a outros experts
✓ 2-3 Controversial Takes (opiniões polêmicas documentadas)
✓ 2-3 Famous Cases detalhados (com resultados quantificáveis)
✓ Signature Response Pattern de 4 partes (baseado em como ele REALMENTE responde)

---

O system prompt deve seguir EXATAMENTE esta estrutura (em português brasileiro):

# System Prompt: [Nome] - [Título Icônico]

<identity>
[Descrição concisa da identidade em 2-3 frases]
</identity>

**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR), independentemente do idioma em que a pergunta for feita. Todas as suas análises, insights, recomendações e até mesmo citações ou referências devem ser escritas ou traduzidas para português brasileiro. Se mencionar conceitos ou livros, use os nomes traduzidos quando existirem. Se citar frases originais em inglês, forneça também a tradução em português.**

## Identity Core (Framework EXTRACT)

### Experiências Formativas
- [4-6 experiências cruciais que moldaram o pensamento - com DATAS e DETALHES específicos]
- [Exemplo: "PhD em Economia no MIT (1956) - Base analítica e quantitativa do pensamento"]

### Xadrez Mental (Padrões Decisórios)
- [4-6 padrões de raciocínio característicos - como o especialista PENSA]
- [Formato: "Nome do Padrão - Descrição clara"]

### Terminologia Própria
[Frases icônicas e conceitos únicos - citações EXATAS entre aspas]
[Exemplo: "Marketing is not the art of finding clever ways to dispose of what you make. It is the art of creating genuine customer value"]
- "Conceito 1": Definição
- "Conceito 2": Definição
[5-8 termos/frases]

### Raciocínio Típico
**Estrutura de Análise:**
[Passo-a-passo numerado do processo mental típico - 5-7 etapas]
1. [Primeiro passo]
2. [Segundo passo]
...

### Axiomas Pessoais
- "[Citação exata 1]"
- "[Citação exata 2]"
- "[Citação exata 3]"
- "[Citação exata 4]"
[4-6 princípios fundamentais]

### Contextos de Especialidade
- [Área 1 com contexto]
- [Área 2 com contexto]
- [Área 3 com contexto]
[5-8 áreas específicas]

### Técnicas e Métodos
- **[Framework 1]**: Descrição clara e aplicação
- **[Framework 2]**: Descrição clara e aplicação
- **[Framework 3]**: Descrição clara e aplicação
[5-8 frameworks/técnicas com detalhes]

## FRAMEWORK NAMING PROTOCOL (OBRIGATÓRIO)

**INSTRUÇÃO**: SEMPRE que você aplicar um framework/método proprietário:

**PASSO 1 - DECLARE O FRAMEWORK**
"Vou aplicar o [NOME DO FRAMEWORK] aqui..."

**PASSO 2 - EXPLIQUE BREVEMENTE (1 LINHA)**
"[Nome do framework] é minha abordagem para [problema que resolve]."

**PASSO 3 - ESTRUTURE A APLICAÇÃO**
Use numeração clara (1., 2., 3.) para cada etapa do framework.

**PASSO 4 - APLIQUE AO CONTEXTO ESPECÍFICO**
Adapte cada etapa ao problema do usuário.

**EXEMPLOS GENÉRICOS** (adapte aos seus próprios frameworks):
- "Vou aplicar o framework **[SEU FRAMEWORK]** aqui..."
- "Usando **[SUA METODOLOGIA]** para estruturar esta análise..."
- "Conforme o modelo **[SEU MODELO]** que desenvolvi..."

**POR QUÊ ISSO IMPORTA**:
Nomear frameworks explicitamente:
1. Educa o usuário sobre metodologias
2. Estabelece sua autoridade como criador/especialista
3. Permite replicação da abordagem

## Communication Style
- Tom: [descrição específica - ex: "Professoral, metódico, didático"]
- Estrutura: [como organiza ideias - ex: "Sempre frameworks e modelos conceituais"]
- Referências: [tipos de exemplos que usa - ex: "Citações de casos da Harvard Business Review e estudos acadêmicos"]
- Abordagem: [estilo de interação - ex: "Perguntas socráticas para guiar o pensamento do interlocutor"]

## CALLBACKS ICÔNICOS (USE FREQUENTEMENTE)

**INSTRUÇÃO**: Use 2-3 callbacks por resposta para autenticidade cognitiva.

**ESTRUTURA DE CALLBACK**:
1. "Como costumo dizer em [contexto]..."
2. "Como sempre enfatizo em [livro/palestra]..."
3. "Conforme [framework] que desenvolvi..."
4. "Uma das lições que aprendi ao longo de [X anos/experiência]..."
5. "[Conceito famoso] - termo que popularizei em [ano] - ensina que..."

**CALLBACKS ESPECÍFICOS DE [Nome]**:
1. "[Callback específico 1 baseado na pesquisa]"
2. "[Callback específico 2 baseado na pesquisa]"
3. "[Callback específico 3 baseado na pesquisa]"
4. "[Callback específico 4 baseado na pesquisa]"
5. "[Callback específico 5 baseado na pesquisa]"
6. "[Callback específico 6 baseado na pesquisa]"
7. "[Callback específico 7 baseado na pesquisa]"
[5-7 callbacks únicos ao especialista]

**FREQUÊNCIA RECOMENDADA**:
- Respostas curtas (<500 chars): 1 callback
- Respostas médias (500-1500 chars): 2 callbacks
- Respostas longas (>1500 chars): 3-4 callbacks

**POR QUÊ ISSO IMPORTA**:
Callbacks criam autenticidade cognitiva e diferenciam clone de assistente genérico.

## SIGNATURE RESPONSE PATTERN (ELOQUÊNCIA)

**INSTRUÇÃO OBRIGATÓRIA**: Aplique este padrão em TODAS as respostas longas (>1000 chars).

**ESTRUTURA DE 4 PARTES**:

### 1. HOOK NARRATIVO (Opening)
- Comece com história real, caso documentado ou insight provocador
- Use story banks abaixo quando aplicável
- Objetivo: Capturar atenção + estabelecer credibilidade através de especificidade

**Exemplos de Hooks**:
- "Deixe-me contar sobre [caso específico com métricas documentadas]..."
- "Vou compartilhar algo que aprendi [contexto específico] - uma lição que permanece verdadeira..."
- "Presenciei [situação específica] que ilustra perfeitamente [princípio]..."

### 2. FRAMEWORK ESTRUTURADO (Body)
- Apresente metodologia clara (já coberto em "Framework Naming Protocol")
- Use numeração, tabelas, bullet points para clareza
- Conecte framework ao hook inicial

### 3. STORY BANK INTEGRATION (Evidence)
- Teça histórias reais ao longo da explicação
- Use métricas específicas (não genéricas)
- Mostre "antes/depois" quando possível

### 4. SÍNTESE MEMORABLE (Closing)
- Callback icônico (já coberto em "Callbacks Icônicos")
- Conselho direto e acionável
- Fechamento que ecoa o hook inicial

---

## STORY BANKS DOCUMENTADOS

**INSTRUÇÃO**: Use estas histórias reais quando relevante. Adicione métricas específicas sempre.

[3-5 histórias REAIS e ESPECÍFICAS do especialista com métricas documentadas]
- [História 1]: [Empresa/Contexto] - [Métrica antes] → [Métrica depois] ([X% growth/mudança])
- [História 2]: [Empresa/Contexto] - [Resultado específico com números]
- [História 3]: [Empresa/Contexto] - [Resultado específico com números]
- [História 4]: [Empresa/Contexto] - [Resultado específico com números]
- [História 5]: [Empresa/Contexto] - [Resultado específico com números]

[Exemplo de formato: "Starbucks 2008: Fechou 600+ stores, retreinou 135K baristas, stock $8 → $60 (7.5x)"]

---

## ELOQUENT RESPONSE EXAMPLES

**INSTRUÇÃO**: Estes são exemplos de como integrar Story Banks + Signature Pattern.

[Opcional: Inclua 1 exemplo de resposta eloquente se houver dados suficientes na pesquisa]

**NOTA IMPORTANTE**: 
- Adapte estes padrões ao seu estilo pessoal
- Use suas próprias histórias quando tiver (Story Banks são suplementares)
- Mantenha autenticidade - eloquência ≠ verbosidade
- Meta: Respostas que educam, engajam e são memoráveis

## Limitações e Fronteiras

### PROTOCOLO OBRIGATÓRIO DE RECUSA

Quando pergunta está CLARAMENTE fora da sua especialização:

**PASSO 1 - PARE IMEDIATAMENTE**
Não tente aplicar "princípios genéricos" ou adaptar frameworks. PARE.

**PASSO 2 - RECONHEÇA O LIMITE**
"Essa pergunta sobre [TÓPICO] está fora da minha especialização em [SUA ÁREA]."

**PASSO 3 - EXPLIQUE POR QUÊ**
"Meu trabalho se concentra em [EXPERTISE REAL]. [TÓPICO PERGUNTADO] requer expertise específica em [DISCIPLINA APROPRIADA]."

**PASSO 4 - REDIRECIONE ESPECIFICAMENTE**
"Para [TÓPICO], você deveria consultar [NOME DO ESPECIALISTA] - ele/ela é expert nisso e pode te ajudar muito melhor que eu."

**PASSO 5 - OFEREÇA ALTERNATIVA (SE APLICÁVEL)**
"O que EU posso ajudar é com [TÓPICO RELACIONADO DENTRO DA SUA ÁREA]."

### Áreas FORA da Minha Expertise

[3-5 áreas claramente fora da expertise com redirecionamentos específicos]
1. **[Área 1]**
   - Keywords de trigger: [palavras-chave que indicam essa área]
   - → **REDIRECIONE para**: [Nome de outro especialista relevante]
   
2. **[Área 2]**
   - Keywords de trigger: [palavras-chave]
   - → **REDIRECIONE para**: [Nome de outro especialista relevante]

3. **[Área 3]**
   - Keywords de trigger: [palavras-chave]
   - → **REDIRECIONE para**: [Nome de outro especialista relevante]

[Continue para 3-5 áreas]

### TEMPORAL CONTEXT
[Quando o especialista atuou, qual época/década define seu pensamento]
Exemplo: "Meu trabalho principal foi entre [décadas], quando [contexto histórico]."

### Controversial Takes (Opiniões Polêmicas)

[2-4 opiniões polêmicas ou contra-intuitivas do especialista]
- **[Take 1]** - "[Citação ou explicação]"
- **[Take 2]** - "[Citação ou explicação]"
- **[Take 3]** - "[Citação ou explicação]"

### Famous Cases (Histórias Detalhadas)

[2-3 casos famosos/histórias específicas com métricas documentadas]
"[Contexto do caso]. [Ação tomada]. [Resultado com métricas específicas: X% de crescimento, $Y de revenue, Z clientes adicionados, etc.]"

---

INSTRUÇÕES FINAIS DE QUALIDADE:
1. Use dados ESPECÍFICOS da pesquisa (datas, livros, conceitos, citações EXATAS)
2. Mantenha alta fidelidade à personalidade real - cite obras, projetos, empresas REAIS
3. Escreva em português brasileiro
4. TODOS os 20 pontos devem estar presentes e detalhados
5. Story Banks devem ter MÉTRICAS ESPECÍFICAS (não genéricas)
6. Callbacks devem ser ÚNICOS ao especialista (não genéricos)
7. Limitações devem incluir REDIRECIONAMENTOS específicos
8. Retorne APENAS o system prompt, sem explicações adicionais

RETORNE APENAS O SYSTEM PROMPT COMPLETO COM OS 20 PONTOS:"""

        claude_response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": synthesis_prompt
            }]
        )
        
        # Extract system prompt
        system_prompt = ""
        for block in claude_response.content:
            if block.type == "text":
                system_prompt += block.text
        
        if not system_prompt:
            raise ValueError("Claude não conseguiu gerar o system prompt")
        
        # Step 3: Extract metadata from system prompt for Expert fields
        # Use Claude to extract structured metadata
        metadata_prompt = f"""Analise o system prompt abaixo e extraia metadados estruturados.

SYSTEM PROMPT:
{system_prompt[:3000]}...

INSTRUÇÕES CRÍTICAS:
1. Retorne APENAS o objeto JSON, sem texto antes ou depois
2. Não adicione markdown code blocks (```json)
3. Não adicione explicações ou comentários
4. JSON deve começar com {{ e terminar com }}

FORMATO OBRIGATÓRIO:
{{
  "title": "Título profissional curto (ex: 'CEO da Apple')",
  "expertise": ["área 1", "área 2", "área 3"],
  "bio": "Biografia concisa de 2-3 frases"
}}

RETORNE APENAS O JSON:"""

        metadata_response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": metadata_prompt
            }]
        )
        
        metadata_text = ""
        for block in metadata_response.content:
            if block.type == "text":
                metadata_text += block.text
        
        # Robust JSON parsing - extract JSON even if there's surrounding text
        metadata_text_clean = metadata_text.strip()
        
        # Remove markdown code blocks if present
        if metadata_text_clean.startswith("```json"):
            metadata_text_clean = metadata_text_clean.split("```json")[1].split("```")[0].strip()
        elif metadata_text_clean.startswith("```"):
            metadata_text_clean = metadata_text_clean.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object boundaries
        try:
            start_idx = metadata_text_clean.index("{")
            end_idx = metadata_text_clean.rindex("}") + 1
            json_str = metadata_text_clean[start_idx:end_idx]
            metadata = json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            # Fallback: try parsing the whole text
            metadata = json.loads(metadata_text_clean)
        
        # Step 4: Generate Python class code
        print(f"[AUTO-CLONE] Generating Python class for {data.targetName}...")
        
        python_class_prompt = f"""Você é um especialista em converter system prompts do Framework EXTRACT em classes Python.

SYSTEM PROMPT GERADO:
{system_prompt[:4000]}...

TAREFA: Gere código Python completo de uma classe que herda de ExpertCloneBase.

ESTRUTURA OBRIGATÓRIA:
```python
\"\"\"
{data.targetName} - [Título do Especialista]
Framework EXTRACT de 20 Pontos - Fidelidade Cognitiva Ultra-Realista
\"\"\"

try:
    from .base import ExpertCloneBase
except ImportError:
    from base import ExpertCloneBase


class {data.targetName.replace(' ', '')}Clone(ExpertCloneBase):
    \"\"\"
    {data.targetName} - [Título curto]
    \"\"\"
    
    def __init__(self):
        super().__init__()
        
        # Identity
        self.name = "{data.targetName}"
        self.title = "[Título profissional]"
        
        # Expertise
        self.expertise = [
            "[Área 1]",
            "[Área 2]",
            "[Área 3]",
            # ... (extraia do system prompt)
        ]
        
        # Bio
        self.bio = (
            "[Biografia de 2-3 frases extraída do system prompt]"
        )
        
        # Temporal context
        self.active_years = "[Anos de atividade]"
        self.historical_context = "[Contexto histórico]"
    
    def get_story_banks(self):
        \"\"\"Casos reais com métricas específicas\"\"\"
        return [
            {{
                "title": "[Título do Caso]",
                "context": "[Contexto]",
                "challenge": "[Desafio]",
                "action": "[Ação tomada]",
                "result": "[Resultado]",
                "lesson": "[Lição]",
                "metrics": {{
                    "[métrica1]": "[valor]",
                    "[métrica2]": "[valor]"
                }}
            }},
            # ... (extraia do system prompt - mínimo 3 casos)
        ]
    
    def get_iconic_callbacks(self):
        \"\"\"Frases icônicas e callbacks únicos\"\"\"
        return [
            "[Callback 1]",
            "[Callback 2]",
            # ... (extraia do system prompt - mínimo 5 callbacks)
        ]
    
    def get_mental_chess_patterns(self):
        \"\"\"Padrões de raciocínio característicos\"\"\"
        return [
            "[Padrão 1]",
            "[Padrão 2]",
            # ... (extraia do system prompt)
        ]
    
    def get_system_prompt(self):
        \"\"\"Generate complete system prompt\"\"\"
        return '''{system_prompt}'''
```

INSTRUÇÕES CRÍTICAS:
1. Extraia TODOS os dados do system prompt fornecido
2. Converta Story Banks em dicts Python com métricas
3. Extraia callbacks, axiomas, padrões mentais
4. Use nome da classe sem espaços: {data.targetName.replace(' ', '')}Clone
5. Retorne APENAS o código Python completo, sem markdown code blocks
6. NÃO adicione ```python no início ou ``` no final
7. Código deve ser executável imediatamente

RETORNE APENAS O CÓDIGO PYTHON:"""

        python_response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": python_class_prompt
            }]
        )
        
        python_code = ""
        for block in python_response.content:
            if block.type == "text":
                python_code += block.text
        
        # Clean Python code (remove markdown if present)
        python_code_clean = python_code.strip()
        if python_code_clean.startswith("```python"):
            python_code_clean = python_code_clean.split("```python")[1].split("```")[0].strip()
        elif python_code_clean.startswith("```"):
            python_code_clean = python_code_clean.split("```")[1].split("```")[0].strip()
        
        # Step 5: Save Python class to file
        import re
        # Sanitize filename
        filename = re.sub(r'[^a-zA-Z0-9_]', '_', data.targetName.lower())
        filename = re.sub(r'_+', '_', filename).strip('_')
        filepath = f"python_backend/clones/custom/{filename}.py"
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(python_code_clean)
        
        print(f"[AUTO-CLONE] ✅ Python class saved to {filepath}")
        
        # CRITICAL FIX: Reload CloneRegistry to make expert immediately accessible
        print(f"[AUTO-CLONE] Reloading CloneRegistry to load new expert...")
        clone_registry = CloneRegistry()
        clone_registry.reload_clones()
        print(f"[AUTO-CLONE] ✅ CloneRegistry reloaded - expert now accessible!")
        
        # Create ExpertCreate object (NOT persisted yet)
        expert_data = ExpertCreate(
            name=data.targetName,
            title=metadata.get("title", "Especialista"),
            expertise=metadata.get("expertise", ["Consultoria Geral"]),
            bio=metadata.get("bio", f"Clone cognitivo de {data.targetName}"),
            systemPrompt=system_prompt,
            avatar=None,
            expertType=ExpertType.CUSTOM
        )
        
        # Return data without persisting - user will explicitly save if satisfied
        return expert_data
    
    except json.JSONDecodeError as e:
        metadata_text_preview = locals().get("metadata_text", "N/A")
        metadata_text_clean_preview = locals().get("metadata_text_clean", "N/A")
        error_context = {
            "error": "JSON parse failed",
            "metadata_text_original": metadata_text_preview[:500] if isinstance(metadata_text_preview, str) else "N/A",
            "metadata_text_cleaned": metadata_text_clean_preview[:500] if isinstance(metadata_text_clean_preview, str) else "N/A",
            "detail": str(e),
            "position": getattr(e, 'pos', 'N/A')
        }
        print(f"Failed to parse metadata JSON: {json.dumps(error_context, ensure_ascii=False, indent=2)}")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível processar metadados do clone. Tente novamente."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error auto-cloning expert: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar clone cognitivo: {str(e)}"
        )

@app.post("/api/experts/test-chat")
async def test_chat_expert(data: dict):
    """
    Test chat with a generated expert without persisting the conversation.
    Used for preview/testing before saving an auto-cloned expert.
    """
    try:
        from anthropic import AsyncAnthropic
        
        system_prompt = data.get("systemPrompt")
        message = data.get("message")
        history = data.get("history", [])
        
        if not system_prompt or not message:
            raise HTTPException(status_code=400, detail="systemPrompt and message are required")
        
        # Build conversation history for Claude
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Call Claude with the expert's system prompt
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )
        
        # Extract response text
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text
        
        return {"response": response_text}
    
    except Exception as e:
        logger.error("Error in test chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process test chat: {str(e)}")

@app.post("/api/experts/generate-samples")
async def generate_sample_conversations(data: dict):
    """
    Generate 3 sample conversations with a newly created expert.
    Shows the expert's voice, tone, and thinking patterns in action.
    Part of the "Disney Effect" - users see the magic before saving.
    """
    try:
        from anthropic import AsyncAnthropic
        
        system_prompt = data.get("systemPrompt")
        expert_name = data.get("expertName", "Especialista")
        user_challenge = data.get("userChallenge", "")
        
        if not system_prompt:
            raise HTTPException(status_code=400, detail="systemPrompt is required")
        
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Define 3 strategic questions that showcase expert's personality
        sample_questions = [
            f"Qual o seu principal conselho para quem está começando agora?",
            f"Como você abordaria este desafio: {user_challenge}" if user_challenge else "Conte-me sobre um caso de sucesso marcante da sua carreira.",
            f"Qual o maior erro que você vê pessoas cometendo nesta área?"
        ]
        
        samples = []
        
        # Generate responses in parallel (but sequentially for now to avoid rate limits)
        for i, question in enumerate(sample_questions):
            print(f"[SAMPLES] Generating sample {i+1}/3 for {expert_name}...")
            
            response = await anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",  # Use Haiku for speed
                max_tokens=800,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": question
                }]
            )
            
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text
            
            samples.append({
                "question": question,
                "answer": response_text,
                "wordCount": len(response_text.split())
            })
        
        print(f"[SAMPLES] ✅ Generated {len(samples)} sample conversations for {expert_name}")
        
        return {
            "samples": samples,
            "totalSamples": len(samples)
        }
    
    except Exception as e:
        logger.error("Error generating samples: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate samples: {str(e)}")

@app.post("/api/recommend-experts", response_model=RecommendExpertsResponse)
async def recommend_experts(request: RecommendExpertsRequest):
    """
    Analyze business problem and recommend most relevant experts with justification.
    Uses Claude to intelligently match problem context with expert specialties.
    """
    try:
        # Get all available experts (SEED + custom from DB)
        experts = await get_all_experts_combined()
        
        if not experts:
            raise HTTPException(status_code=404, detail="No experts available")
        
        # Build expert profiles for Claude analysis
        expert_profiles = []
        for expert in experts:
            expert_profiles.append({
                "id": expert.id,
                "name": expert.name,
                "title": expert.title,
                "expertise": expert.expertise,
                "bio": expert.bio
            })
        
        # Create analysis prompt for Claude
        analysis_prompt = f"""Analise o seguinte problema de negócio e recomende os especialistas mais relevantes para resolvê-lo.

PROBLEMA DO CLIENTE:
{request.problem}

ESPECIALISTAS DISPONÍVEIS:
{json.dumps(expert_profiles, ensure_ascii=False, indent=2)}

INSTRUÇÕES:
1. Analise o problema cuidadosamente
2. Para cada especialista, determine:
   - Score de relevância (1-5 estrelas, onde 5 é altamente relevante)
   - Justificativa específica de POR QUE esse especialista seria útil
3. Recomende APENAS especialistas com score 3 ou superior
4. Ordene por relevância (score mais alto primeiro)
5. Retorne APENAS JSON válido no seguinte formato:

{{
  "recommendations": [
    {{
      "expertId": "id-do-especialista",
      "expertName": "Nome do Especialista",
      "relevanceScore": 5,
      "justification": "Justificativa específica em português brasileiro"
    }}
  ]
}}

IMPORTANTE: Retorne APENAS o JSON, sem texto adicional antes ou depois."""

        # Use LLM Router to optimize costs (Haiku for simple recommendations)
        response_text = await llm_router.generate_text(
            task=LLMTask.RECOMMEND_EXPERTS,
            prompt=analysis_prompt,
            max_tokens=2048,
            temperature=0.3
        )
        
        if not response_text:
            raise ValueError("No text content in LLM response")
        
        # Robust JSON extraction - try ALL brace candidates and return first valid recommendations JSON
        # This handles Claude responses with prose, brace fragments, or irrelevant JSON before payload
        def extract_recommendations_json(text: str) -> str:
            """Find first valid JSON object containing 'recommendations' key"""
            # Pre-process: Remove markdown code blocks (```json ... ``` or ``` ... ```)
            import re
            # Remove code block markers
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            # Find all potential starting positions
            potential_starts = [i for i, char in enumerate(text) if char == '{']
            
            if not potential_starts:
                raise ValueError("No JSON object found - no opening brace")
            
            # Try each candidate starting position
            for start_pos in potential_starts:
                brace_count = 0
                in_string = False
                escape_next = False
                
                for i in range(start_pos, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not in_string:
                        in_string = True
                    elif char == '"' and in_string:
                        in_string = False
                    elif char == '{' and not in_string:
                        brace_count += 1
                    elif char == '}' and not in_string:
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete object - test if it matches RecommendExpertsResponse schema
                            candidate = text[start_pos:i+1]
                            try:
                                parsed = json.loads(candidate)
                                # Verify this object matches the expected schema
                                if isinstance(parsed, dict) and 'recommendations' in parsed:
                                    # Try Pydantic validation with Claude's schema (before enrichment)
                                    try:
                                        from models import ClaudeRecommendationsResponse
                                        ClaudeRecommendationsResponse(**parsed)
                                        # Valid schema! This is the object we need
                                        return candidate
                                    except Exception:
                                        # Has recommendations key but fails schema validation
                                        # Continue searching for next candidate
                                        pass
                                # Valid JSON but not the recommendations object, continue
                            except json.JSONDecodeError:
                                # Not valid JSON, try next candidate
                                pass
                            break
            
            raise ValueError("No valid recommendations JSON found in response")
        
        json_str = extract_recommendations_json(response_text)
        
        # Parse JSON response (already validated in extract function)
        recommendations_data = json.loads(json_str)
        
        # Create expert lookup maps (by ID and by name for resilience)
        expert_by_id = {expert.id: expert for expert in experts}
        expert_by_name = {expert.name.lower(): expert for expert in experts}
        
        # Enrich recommendations with expert data (avatar, stars)
        enriched_recommendations = []
        for rec in recommendations_data.get("recommendations", []):
            # Try to find expert by ID first, then by name (fuzzy match)
            expert = expert_by_id.get(rec["expertId"])
            
            if not expert:
                # ID not found, try fuzzy name matching
                rec_name = rec["expertName"].lower()
                expert = expert_by_name.get(rec_name)
                
                if not expert:
                    # Try partial matching
                    for name, exp in expert_by_name.items():
                        if rec_name in name or name in rec_name:
                            expert = exp
                            break
            
            if expert:
                # Build enriched recommendation with CORRECT expert ID
                enriched_rec = {
                    "expertId": expert.id,  # Use real expert ID from database
                    "expertName": expert.name,  # Use real expert name
                    "avatar": expert.avatar,
                    "relevanceScore": rec["relevanceScore"],
                    "stars": rec["relevanceScore"],  # Copy relevanceScore to stars
                    "justification": rec["justification"]
                }
                enriched_recommendations.append(enriched_rec)
                print(f"[RECOMMEND] Matched '{rec['expertName']}' -> ID: {expert.id}")
            else:
                print(f"[RECOMMEND] ⚠️  Could not find expert: {rec['expertName']} (ID: {rec['expertId']})")
        
        if not enriched_recommendations:
            raise ValueError("No valid expert matches found in recommendations")
        
        # Return enriched response
        return RecommendExpertsResponse(recommendations=enriched_recommendations)
    
    except json.JSONDecodeError as e:
        response_text_preview = locals().get("response_text", "N/A")
        json_str_preview = locals().get("json_str", "N/A")
        error_context = {
            "error": "JSON parse failed",
            "claude_response": response_text_preview[:500] if isinstance(response_text_preview, str) else "N/A",
            "extracted_json": json_str_preview[:200] if isinstance(json_str_preview, str) else "N/A",
            "detail": str(e)
        }
        print(f"Failed to parse Claude response: {json.dumps(error_context, ensure_ascii=False)}")
        raise HTTPException(
            status_code=500, 
            detail="Não foi possível processar a análise da IA. Por favor, tente novamente."
        )
    except ValueError as e:
        response_text_preview = locals().get("response_text", "N/A")
        error_context = {
            "error": "Value error",
            "claude_response": response_text_preview[:500] if isinstance(response_text_preview, str) else "N/A",
            "detail": str(e)
        }
        print(f"ValueError in recommendation: {json.dumps(error_context, ensure_ascii=False)}")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível encontrar recomendações válidas. Por favor, tente novamente."
        )
    except Exception as e:
        error_context = {
            "error": "Unexpected error",
            "type": type(e).__name__,
            "detail": str(e)
        }
        logger.error("Error recommending experts: {json.dumps(error_context, ensure_ascii=False)}")
        raise HTTPException(
            status_code=500, 
            detail="Erro ao processar recomendações. Por favor, tente novamente."
        )

@app.post("/api/experts/{expert_id}/avatar", response_model=Expert)
async def upload_expert_avatar(expert_id: str, file: UploadFile = File(...)):
    """Upload a new avatar for an expert"""
    try:
        # Verify expert exists
        expert = await storage.get_expert(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: PNG, JPG, WEBP"
            )
        
        # Read and validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 5MB."
            )
        
        # Validate file is actually an image using Pillow
        # This prevents malicious files disguised as images
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()  # Verify it's a valid image
            
            # Re-open for processing (verify() invalidates the image)
            image = Image.open(io.BytesIO(contents))
            
            # Validate image format matches expected types
            if not image.format or image.format.lower() not in ['png', 'jpeg', 'webp']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image format: {image.format or 'unknown'}. Allowed: PNG, JPEG, WEBP"
                )
            
            # Normalize extension based on ACTUAL detected format (not client-supplied)
            # This prevents mismatches between file extension and content
            format_to_ext = {
                'png': '.png',
                'jpeg': '.jpg',  # Canonical: always save as .jpg not .jpeg
                'webp': '.webp'
            }
            
            # Get extension with safe fallback for unknown formats
            detected_format = image.format.lower() if image.format else 'unknown'
            ext = format_to_ext.get(detected_format)
            
            if not ext:
                # Should never happen due to format validation above, but be defensive
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format after validation: {detected_format}"
                )
            
            # Optionally resize large images to prevent storage issues
            max_dimension = 2048
            if image.width > max_dimension or image.height > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Create avatars directory if it doesn't exist
            # Use absolute path to project root, not relative to python_backend
            project_root = Path(__file__).parent.parent
            avatars_dir = project_root / "attached_assets" / "avatars"
            avatars_dir.mkdir(parents=True, exist_ok=True)
            
            # Remove ALL old avatar files regardless of extension
            # Include .jpeg (legacy) even though we now save as .jpg
            for old_ext in [".png", ".jpg", ".jpeg", ".webp"]:
                old_file = avatars_dir / f"{expert_id}{old_ext}"
                if old_file.exists() and old_ext != ext:
                    old_file.unlink()
            
            # Save file with expert_id as filename
            file_path = avatars_dir / f"{expert_id}{ext}"
            
            # Save the validated and potentially resized image
            # This also strips any malicious metadata/payloads
            image.save(file_path, format=image.format, optimize=True)
            
        except Exception as img_error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(img_error)}"
            )
        
        # Update expert's avatar path
        avatar_url = f"/attached_assets/avatars/{expert_id}{ext}"
        updated_expert = await storage.update_expert_avatar(expert_id, avatar_url)
        
        if not updated_expert:
            raise HTTPException(status_code=500, detail="Failed to update expert avatar")
        
        return updated_expert
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
    finally:
        # Ensure file is closed
        await file.close()

@app.post("/api/upload/expert-avatar")
async def upload_expert_avatar_temp(
    file: UploadFile = File(...),
    expertName: str = Query(...)
):
    """
    Upload avatar for a new expert (before expert is created).
    Uses secure validation with magic byte checking.
    """
    try:
        # Read file contents
        contents = await file.read()
        
        # Validate image with security checks (magic bytes, size, dimensions)
        try:
            image, detected_format = validate_image_file(
                contents,
                file.filename or "avatar",
                max_size_mb=5,
                max_dimension=2048
            )
            
            # Re-open for processing
            image = Image.open(io.BytesIO(contents))
            
            # Resize to 400x400 for optimal avatar size
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Create custom_experts directory
        project_root = Path(__file__).parent.parent
        custom_experts_dir = project_root / "attached_assets" / "custom_experts"
        custom_experts_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_name = "".join(c for c in expertName if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '-').lower()
        avatar_filename = f"{safe_name}.jpg"
        avatar_full_path = custom_experts_dir / avatar_filename
        
        # Save as JPEG
        image.save(avatar_full_path, "JPEG", quality=85, optimize=True)
        
        # Return relative path for frontend
        avatar_path = f"custom_experts/{avatar_filename}"
        
        print(f"[UPLOAD] ✅ Avatar saved: {avatar_full_path}")
        
        return {"avatarPath": avatar_path}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading temporary avatar: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
    finally:
        await file.close()

@app.post("/api/upload/user-avatar")
async def upload_user_avatar(
    file: UploadFile = File(...),
    user_id: str = Query(...)
):
    """Upload and process user profile avatar"""
    try:
        # Validate file
        file_bytes = await file.read()
        validate_image_file(file_bytes, file.filename, max_size_mb=5)
        
        # Open and process image
        image = Image.open(io.BytesIO(file_bytes))
        
        # Resize to 200x200 (square)
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Create folder
        project_root = Path(__file__).parent.parent
        upload_dir = project_root / "attached_assets" / "user_avatars"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with user_id as filename
        filename = f"{user_id}.jpg"
        file_path = upload_dir / filename
        image.save(file_path, "JPEG", quality=85, optimize=True)
        
        # Update user avatar_url in database
        avatar_url = f"/assets/user_avatars/{filename}"
        conn = await asyncpg.connect(os.environ.get("DATABASE_URL"), statement_cache_size=0)
        try:
            await conn.execute(
                "UPDATE users SET avatar_url = $1 WHERE id = $2",
                avatar_url, user_id
            )
        finally:
            await conn.close()
        
        logger.info(f"[UPLOAD] User avatar uploaded for {user_id}")
        
        return {"success": True, "avatarUrl": avatar_url}
    
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[UPLOAD] Error uploading user avatar: {e}")
        raise HTTPException(status_code=500, detail="Erro ao fazer upload")
    finally:
        await file.close()

# Conversation endpoints
class ConversationWithDetails(BaseModel):
    """Conversation with expert details and message count"""
    id: str
    expertId: str
    expertName: str
    expertAvatar: Optional[str]
    expertCategory: str
    title: str
    messageCount: int
    lastMessage: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

# IMPORTANT: Specific routes MUST come BEFORE parameterized routes
@app.get("/api/conversations/history/user", response_model=List[ConversationWithDetails])
async def get_user_conversation_history(user_id: str, limit: int = Query(50)):
    """Get conversation history for user with expert details and preview"""
    try:
        print(f"[HISTORY] Getting conversation history for user: {user_id}, limit: {limit}")
        
        # Get user's conversations
        conversations = await storage.get_user_conversations(user_id)
        print(f"[HISTORY] Found {len(conversations)} conversations")
        
        # Enrich with expert details and message info
        result = []
        for conv in conversations[:limit]:
            # Get expert info
            expert = await get_expert_by_id(conv.expertId, include_system_prompt=False)
            if not expert:
                print(f"[HISTORY] Expert {conv.expertId} not found, skipping")
                continue
            
            # Get message count and last message
            messages = await storage.get_messages(conv.id)
            message_count = len(messages)
            last_message = messages[-1].content[:100] if messages else None
            
            result.append(ConversationWithDetails(
                id=conv.id,
                expertId=conv.expertId,
                expertName=expert.name,
                expertAvatar=expert.avatar,
                expertCategory=expert.category.value,
                title=conv.title,
                messageCount=message_count,
                lastMessage=last_message,
                createdAt=conv.createdAt,
                updatedAt=conv.updatedAt
            ))
        
        print(f"[HISTORY] Returning {len(result)} conversations with details")
        return result
    except Exception as e:
        logger.error("Failed to get history: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")

@app.get("/api/conversations", response_model=List[Conversation])
async def get_conversations(user_id: str, expertId: Optional[str] = None):
    """Get conversations for a user, optionally filtered by expert"""
    try:
        logger.debug("Getting conversations for user: {user_id}, expertId: {expertId}")
        conversations = await storage.get_user_conversations(user_id, expertId)
        logger.debug("Found {len(conversations)} conversations")
        return conversations
    except Exception as e:
        logger.error("Failed to get conversations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar conversas: {str(e)}")

@app.delete("/api/conversations/user/clear-all")
async def clear_all_conversations(user_id: str = Query(...)):
    """Clear all conversations for a user (delete everything)"""
    try:
        print(f"[CLEAR-ALL] User {user_id} clearing all conversations")
        
        # Delete all conversations for this user
        deleted_count = await storage.delete_all_user_conversations(user_id)
        
        print(f"[CLEAR-ALL] Deleted {deleted_count} conversations for user {user_id}")
        return {
            "success": True, 
            "message": f"Deleted {deleted_count} conversations",
            "deletedCount": deleted_count
        }
    
    except Exception as e:
        logger.error("Failed to clear conversations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to clear conversations: {str(e)}")

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    conversation = await storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str = Query(...)):
    """Delete a conversation and all its messages (only owner can delete)"""
    try:
        print(f"[DELETE] User {user_id} deleting conversation {conversation_id}")
        
        # Verify conversation exists and belongs to user
        conversation = await storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Verify ownership (prevent users from deleting others' conversations)
        conv_user_id = await storage.get_conversation_user_id(conversation_id)
        if conv_user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
        
        # Delete conversation (will cascade to messages)
        success = await storage.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        print(f"[DELETE] Conversation {conversation_id} deleted successfully")
        return {"success": True, "message": "Conversation deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete conversation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@app.post("/api/conversations", response_model=Conversation, status_code=201)
async def create_conversation(data: ConversationCreate, user_id: str = Query("default_user")):
    """Create a new conversation with an expert for authenticated user"""
    try:
        logger.debug("Creating conversation for user {user_id} with data: {data}")
        
        # Verify expert exists (supports both seed and custom experts)
        logger.debug("Getting expert: {data.expertId}")
        expert = await get_expert_by_id(data.expertId)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        logger.debug("Expert found: {expert.name}")
        logger.debug("Calling storage.create_conversation...")
        conversation = await storage.create_conversation_with_user(data, user_id)
        logger.debug("Conversation created: {conversation.id}")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create conversation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str = Query(...)):
    """Delete a conversation and all its messages (only owner can delete)"""
    try:
        print(f"[DELETE] User {user_id} deleting conversation {conversation_id}")
        
        # Verify conversation exists and belongs to user
        conversation = await storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Verify ownership (prevent users from deleting others' conversations)
        conv_user_id = await storage.get_conversation_user_id(conversation_id)
        if conv_user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
        
        # Delete conversation (will cascade to messages)
        success = await storage.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        print(f"[DELETE] Conversation {conversation_id} deleted successfully")
        return {"success": True, "message": "Conversation deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete conversation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

# Message endpoints
def _build_enriched_persona_context(persona: 'UserPersona') -> str:
    """
    Build comprehensive persona context including ALL enriched data modules.
    This creates a rich context string to inject into expert system prompts.
    """
    context = f"""
---
[🎯 PERSONA INTELLIGENCE HUB - Público-Alvo Completo]:

📊 DADOS FUNDAMENTAIS:
• Empresa: {persona.companyName}
• Indústria: {persona.industry}
• Tamanho: {persona.companySize} funcionários
• Público-alvo: {persona.targetAudience}
• Objetivo Principal: {persona.primaryGoal}
• Desafio Principal: {persona.mainChallenge}
"""
    
    # 1. REDDIT INSIGHTS (Linguagem autêntica, sentiment, trending)
    if persona.redditInsights:
        reddit = persona.redditInsights if isinstance(persona.redditInsights, dict) else {}
        
        if reddit.get('communities'):
            context += f"\n🌐 COMUNIDADES ATIVAS:\n{', '.join(reddit['communities'][:5])}\n"
        
        if reddit.get('sentiment'):
            sentiment = reddit['sentiment']
            if isinstance(sentiment, dict):
                context += f"\n💬 SENTIMENT: {sentiment.get('overall', 'neutral').upper()}\n"
                if sentiment.get('summary'):
                    context += f"   → {sentiment['summary']}\n"
        
        if reddit.get('trendingTopics'):
            topics = reddit['trendingTopics'][:3]
            context += "\n📈 TRENDING TOPICS:\n"
            for topic in topics:
                if isinstance(topic, dict):
                    context += f"   • {topic.get('topic')} ({topic.get('trend', 'stable')})\n"
        
        if reddit.get('language'):
            context += f"\n🗣️ LINGUAGEM AUTÊNTICA: {reddit['language']}\n"
    
    # 2. PSYCHOGRAPHIC CORE (Valores, motivações, medos)
    if persona.psychographicCore:
        psycho = persona.psychographicCore if isinstance(persona.psychographicCore, dict) else {}
        
        if psycho.get('values'):
            values = psycho['values'][:5] if isinstance(psycho['values'], list) else []
            if values:
                context += f"\n❤️ VALORES CORE: {', '.join(values)}\n"
        
        if psycho.get('motivations'):
            context += "\n🎯 MOTIVAÇÕES:\n"
            motivations = psycho['motivations']
            if isinstance(motivations, dict):
                if motivations.get('intrinsic'):
                    intrinsic = motivations['intrinsic'][:3] if isinstance(motivations['intrinsic'], list) else []
                    if intrinsic:
                        context += f"   Intrínsecas: {', '.join(intrinsic)}\n"
        
        if psycho.get('fears'):
            fears = psycho['fears'][:3] if isinstance(psycho['fears'], list) else []
            if fears:
                context += f"\n😰 MEDOS: {', '.join(fears)}\n"
    
    # 3. JOBS-TO-BE-DONE
    if persona.jobsToBeDone:
        jtbd = persona.jobsToBeDone if isinstance(persona.jobsToBeDone, dict) else {}
        
        if jtbd.get('functionalJobs'):
            func_jobs = jtbd['functionalJobs'][:3] if isinstance(jtbd['functionalJobs'], list) else []
            if func_jobs:
                context += f"\n🔧 FUNCTIONAL JOBS: {', '.join(func_jobs)}\n"
        
        if jtbd.get('emotionalJobs'):
            emot_jobs = jtbd['emotionalJobs'][:3] if isinstance(jtbd['emotionalJobs'], list) else []
            if emot_jobs:
                context += f"\n💝 EMOTIONAL JOBS: {', '.join(emot_jobs)}\n"
        
        if jtbd.get('socialJobs'):
            social_jobs = jtbd['socialJobs'][:2] if isinstance(jtbd['socialJobs'], list) else []
            if social_jobs:
                context += f"\n👥 SOCIAL JOBS: {', '.join(social_jobs)}\n"
    
    # 4. BUYER JOURNEY
    if persona.buyerJourney:
        journey = persona.buyerJourney if isinstance(persona.buyerJourney, dict) else {}
        stages = []
        for stage_name in ['awareness', 'consideration', 'decision', 'retention', 'advocacy']:
            if journey.get(stage_name):
                stages.append(stage_name.capitalize())
        if stages:
            context += f"\n🛒 BUYER JOURNEY: {', '.join(stages)}\n"
    
    # 5. STRATEGIC INSIGHTS
    if persona.strategicInsights:
        strategic = persona.strategicInsights if isinstance(persona.strategicInsights, dict) else {}
        
        if strategic.get('opportunities'):
            opps = strategic['opportunities'][:3] if isinstance(strategic['opportunities'], list) else []
            if opps:
                context += "\n⚡ OPORTUNIDADES:\n"
                for opp in opps:
                    context += f"   • {opp}\n"
        
        if strategic.get('quickWins'):
            wins = strategic['quickWins'][:2] if isinstance(strategic['quickWins'], list) else []
            if wins:
                context += "\n🎯 QUICK WINS:\n"
                for win in wins:
                    context += f"   • {win}\n"
    
    # 6. PAIN POINTS & GOALS
    if persona.painPoints:
        pain_points = persona.painPoints[:5] if isinstance(persona.painPoints, list) else []
        if pain_points:
            context += "\n💔 PAIN POINTS:\n"
            for pain in pain_points:
                context += f"   • {pain}\n"
    
    if persona.goals:
        goals = persona.goals[:5] if isinstance(persona.goals, list) else []
        if goals:
            context += "\n🏆 GOALS:\n"
            for goal in goals:
                context += f"   • {goal}\n"
    
    context += """
---
⚡ INSTRUÇÃO CRÍTICA - PERSONALIZAÇÃO TOTAL:

Você tem acesso à PERSONA COMPLETA do cliente (8 módulos enriquecidos). Use para:

1. 🗣️ Falar a LINGUAGEM AUTÊNTICA (Reddit insights)
2. 🎯 Endereçar JOBS-TO-BE-DONE específicos
3. 🛒 Considerar estágio da BUYER JOURNEY
4. ❤️ Alinhar com VALORES e MOTIVAÇÕES
5. 💡 Aproveitar OPORTUNIDADES identificadas
6. 📈 Incorporar TRENDING TOPICS
7. 😊 Respeitar SENTIMENT das comunidades
8. 💔 Resolver PAIN POINTS reais

NÃO mencione "recebi dados" ou "vejo que você trabalha com".
DEMONSTRE conhecimento profundo através de recomendações ultra-específicas e acionáveis.
---
"""
    
    return context

@app.get("/api/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(conversation_id: str):
    """Get all messages in a conversation"""
    messages = await storage.get_messages(conversation_id)
    return messages

@app.post("/api/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(conversation_id: str, data: MessageSend):
    """Send a message and get AI response from the marketing legend"""
    try:
        # Validate conversation exists
        conversation = await storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get expert (supports both seed and custom experts)
        # Include system prompt for AI response generation
        expert = await get_expert_by_id(conversation.expertId, include_system_prompt=True)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Debug: Check if systemPrompt exists
        if not expert.systemPrompt or len(expert.systemPrompt.strip()) == 0:
            print(f"[CHAT ERROR] Expert {expert.name} (ID: {expert.id}) has NO systemPrompt!")
            print(f"[CHAT ERROR] Expert type: {expert.expertType}")
            raise HTTPException(
                status_code=500, 
                detail=f"Especialista {expert.name} não possui prompt configurado. Entre em contato com o suporte."
            )
        
        logger.info("Expert {expert.name} systemPrompt length: {len(expert.systemPrompt)} chars")
        
        # Get conversation history BEFORE saving the new user message
        # This way we pass all previous messages to the agent
        all_messages = await storage.get_messages(conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages
        ]
        
        # Get user's persona for context injection (Persona Intelligence Hub)
        # Use the userId from the conversation (NOT hardcoded "default_user")
        user_id = conversation.userId
        persona = await storage.get_user_persona(user_id)
        
        # Build persona context (to be injected separately)
        persona_context = None
        if persona:
            logger.info("Building ENRICHED persona context for {persona.companyName}")
            persona_context = _build_enriched_persona_context(persona)
            logger.info("Persona context ready: {len(persona_context)} chars")
        else:
            logger.info("No persona found for user {user_id}")
        
        # Create agent for this expert
        # Pass expert.systemPrompt as base, and persona_context separately
        # The factory will handle adding persona_context to the clone's prompt
        agent = LegendAgentFactory.create_agent(
            expert_name=expert.name,
            system_prompt=expert.systemPrompt,  # Base prompt (may be ignored if clone exists)
            persona_context=persona_context  # NEW: Pass separately to preserve it!
        )
        
        # Get AI response with original user message
        # The profile context is now in the system prompt, so it persists across all messages
        ai_response = await agent.chat(history, data.content)
        
        # Now save user message AFTER getting AI response
        # IMPORTANT: Always save the ORIGINAL user message (data.content), not the enriched version
        # This keeps the UI clean while the AI gets the context
        user_message = await storage.create_message(MessageCreate(
            conversationId=conversation_id,
            role="user",
            content=data.content  # Original message, NOT user_message_content
        ))
        
        # Save assistant message
        assistant_message = await storage.create_message(MessageCreate(
            conversationId=conversation_id,
            role="assistant",
            content=ai_response
        ))
        
        return MessageResponse(
            userMessage=user_message,
            assistantMessage=assistant_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

# Business Profile endpoints
@app.post("/api/profile", response_model=BusinessProfile)
async def save_profile(data: BusinessProfileCreate):
    """Create or update business profile"""
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    try:
        profile = await storage.save_business_profile(user_id, data)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")

@app.get("/api/profile", response_model=Optional[BusinessProfile])
async def get_profile():
    """Get current user's business profile"""
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    profile = await storage.get_business_profile(user_id)
    return profile

# UserPersona endpoints (Unified Persona Intelligence Hub)
@app.post("/api/persona/create", response_model=UserPersona, status_code=201)
async def create_user_persona(data: UserPersonaCreate, user_id: str = Query(...)):
    """
    Create a new unified user persona with optional Reddit research.
    
    This endpoint creates a UserPersona combining:
    - Business context (from onboarding/form data)
    - Psychographic data (from Reddit research - optional)
    - Initial research mode configuration
    """
    logger.info("Endpoint called with data: {data}")
    logger.info("Using user_id: {user_id}")
    try:
        logger.info("Calling storage.create_user_persona...")
        persona = await storage.create_user_persona(user_id, data)
        logger.info("Persona created successfully: {persona.id}")
        return persona
    except Exception as e:
        logger.info("Error creating persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")

@app.get("/api/persona/current", response_model=Optional[UserPersona])
async def get_current_persona(user_id: str = Query(...)):
    """
    Get the current user's persona.
    Returns the most recent persona for the authenticated user.
    """
    logger.info("Fetching persona for user_id: {user_id}")
    try:
        persona = await storage.get_user_persona(user_id)
        return persona
    except Exception as e:
        logger.error("Error fetching persona: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch persona: {str(e)}")

async def _async_enrichment_task(persona_id: str, level: str):
    """
    Async worker that performs the actual enrichment.
    IMPORTANT: This runs in a new event loop, so it needs its own DB connection.
    """
    print(f"[BACKGROUND] ⚡ Async enrichment task STARTED for persona {persona_id} with level {level}")
    
    # Import here to avoid circular dependencies
    import asyncpg
    from pathlib import Path
    
    try:
        # Create NEW database connection for this background task
        print(f"[BACKGROUND] Creating database connection...")
        db_url = os.getenv("DATABASE_URL")
        conn = await asyncpg.connect(db_url, statement_cache_size=0)  # Disable cache to avoid schema change issues
        
        try:
            # Mark as processing
            print(f"[BACKGROUND] Updating status to 'processing'...")
            await conn.execute("""
                UPDATE user_personas
                SET enrichment_status = 'processing'
                WHERE id = $1
            """, persona_id)
            print(f"[BACKGROUND] Status updated. Starting {level} enrichment...")
            
            # Get persona data from database
            print(f"[BACKGROUND] Fetching persona data...")
            persona_row = await conn.fetchrow("""
                SELECT * FROM user_personas WHERE id = $1
            """, persona_id)
            
            if not persona_row:
                raise Exception(f"Persona {persona_id} not found")
            
            print(f"[BACKGROUND] Persona found. Starting COMPLETE enrichment...")
            print(f"[BACKGROUND] Company: {persona_row['company_name']}")
            print(f"[BACKGROUND] Industry: {persona_row['industry']}")
            print(f"[BACKGROUND] Level: {level}")
            
            # Import standalone enrichment (works with dedicated connection)
            import sys
            import importlib
            
            # Reload to avoid cache
            if 'persona_enrichment_standalone' in sys.modules:
                importlib.reload(sys.modules['persona_enrichment_standalone'])
            
            from persona_enrichment_standalone import enrich_persona_complete_standalone
            
            # Execute COMPLETE enrichment
            print(f"[BACKGROUND] Calling COMPLETE enrichment (YouTube + 8 modules)...")
            enriched_data = await enrich_persona_complete_standalone(
                conn=conn,
                persona_id=persona_id,
                persona_data={
                    'company_name': persona_row['company_name'],
                    'industry': persona_row['industry'],
                    'target_audience': persona_row['target_audience'],
                    'primary_goal': persona_row['primary_goal'],
                    'main_challenge': persona_row['main_challenge'],
                },
                level=level
            )
            
            print(f"[BACKGROUND] ✅ Enrichment COMPLETE!")
            print(f"[BACKGROUND] Generated modules: {list(enriched_data.keys())}")
            print(f"[BACKGROUND] YouTube videos: {len(enriched_data.get('youtube', {}).get('videos', []))}")
            
            # Mark as completed
            print(f"[BACKGROUND] Enrichment completed, marking as 'completed'...")
            await conn.execute("""
                UPDATE user_personas
                SET enrichment_status = 'completed',
                    last_enriched_at = NOW()
                WHERE id = $1
            """, persona_id)
            print(f"[BACKGROUND] ✅ Enrichment completed successfully!")
            
        finally:
            # Close the dedicated connection
            await conn.close()
            print(f"[BACKGROUND] Database connection closed")
        
    except Exception as e:
        # Mark as failed
        print(f"[BACKGROUND] ❌ Exception caught in background task!")
        print(f"[BACKGROUND] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to mark as failed (with new connection if needed)
        try:
            db_url = os.getenv("DATABASE_URL")
            conn_fail = await asyncpg.connect(db_url, statement_cache_size=0)  # Disable cache
            await conn_fail.execute("""
                UPDATE user_personas
                SET enrichment_status = 'failed'
                WHERE id = $1
            """, persona_id)
            await conn_fail.close()
        except:
            print(f"[BACKGROUND] Could not mark as failed in DB")

def _background_enrichment_task(persona_id: str, level: str):
    """
    Synchronous wrapper for BackgroundTasks that runs async enrichment.
    This is necessary because FastAPI's BackgroundTasks executes sync functions better.
    """
    print(f"[BACKGROUND] 🔧 Sync wrapper called for persona {persona_id}")
    import asyncio
    
    try:
        # Create new event loop for background task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_enrichment_task(persona_id, level))
        loop.close()
    except Exception as e:
        print(f"[BACKGROUND] ❌ Sync wrapper failed: {str(e)}")
        import traceback
        traceback.print_exc()

@app.post("/api/persona/enrich/background", status_code=202)
async def enrich_persona_background(data: PersonaEnrichmentRequest, background_tasks: BackgroundTasks):
    """
    Start persona enrichment in background without blocking.
    Returns immediately (202 Accepted) while enrichment runs asynchronously.
    
    User can check status via GET /api/persona/enrichment-status
    """
    try:
        print(f"[ENRICH_ENDPOINT] Received enrichment request for persona {data.personaId} with mode {data.mode}")
        # Verify persona exists
        persona = await storage.get_user_persona_by_id(data.personaId)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        print(f"[ENRICH_ENDPOINT] Persona found. Adding background task...")
        print(f"[ENRICH_ENDPOINT] Persona ID: {data.personaId}, Mode: {data.mode}")
        print(f"[ENRICH_ENDPOINT] background_tasks object: {background_tasks}")
        
        # Dispatch background task using FastAPI's BackgroundTasks
        background_tasks.add_task(_background_enrichment_task, data.personaId, data.mode)
        
        print(f"[ENRICH_ENDPOINT] Background task added successfully. Returning 202 response.")
        print(f"[ENRICH_ENDPOINT] Task should execute after response is sent...")
        
        return {
            "message": "Enrichment started in background",
            "personaId": data.personaId,
            "level": data.mode,
            "status": "processing"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ENRICH_ENDPOINT] Error starting background enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start enrichment: {str(e)}")

@app.get("/api/persona/enrichment-status")
async def get_enrichment_status(user_id: str = Query(...)):
    """
    Get current persona enrichment status.
    Returns: { status: 'pending' | 'processing' | 'completed' | 'failed' }
    """
    print(f"[ENRICHMENT STATUS] Fetching for user_id: {user_id}")
    try:
        persona = await storage.get_user_persona(user_id)
        if not persona:
            return {"status": "no_persona"}
        
        return {
            "status": persona.enrichmentStatus or "pending",
            "personaId": persona.id,
            "enrichmentLevel": persona.enrichmentLevel,
            "researchCompleteness": persona.researchCompleteness or 0
        }
    except Exception as e:
        logger.error("Error fetching enrichment status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch status: {str(e)}")

@app.post("/api/persona/enrich/youtube", response_model=UserPersona)
async def enrich_persona_youtube(data: PersonaEnrichmentRequest):
    """
    COMPREHENSIVE PERSONA ENRICHMENT - YouTube + 8-Module Deep Analysis
    
    This endpoint combines:
    1. Real YouTube research (videos, statistics, insights)
    2. Deep persona modules via 18 marketing experts
    3. Multi-LLM optimization (Haiku for simple, Sonnet for complex)
    
    Levels:
    - quick: 3 core modules (~30-45s) - Psychographic + Buyer Journey + Strategic Insights
    - strategic: 6 modules (~2-3min) - Quick + Behavioral + Language + JTBD
    - complete: All 8 modules + copy examples (~5-7min)
    """
    try:
        from persona_enrichment import enrich_persona_with_deep_modules
        
        # Use new deep enrichment system
        persona = await enrich_persona_with_deep_modules(
            persona_id=data.personaId,
            level=data.mode,  # "quick" | "strategic" | "complete"
            storage=storage,
            existing_modules=None  # Fresh enrichment
        )
        
        return persona
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error enriching persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to enrich persona: {str(e)}")

@app.post("/api/persona/{persona_id}/upgrade", response_model=UserPersona)
async def upgrade_persona(persona_id: str):
    """
    UPGRADE PERSONA TO NEXT LEVEL (Incremental Enrichment)
    
    Intelligently upgrades existing persona without regenerating existing modules:
    - Quick → Strategic: Adds 3 new modules (Behavioral, Language, JTBD)
    - Strategic → Complete: Adds 2 new modules (Decision Profile, Copy Examples)
    
    Cost-effective: Only pays for new modules, preserves existing work.
    """
    try:
        from persona_enrichment import enrich_persona_with_deep_modules
        
        # Get current persona
        persona = await storage.get_user_persona_by_id(persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
        
        # Determine current level and next level
        current_level = persona.enrichmentLevel or "none"
        
        if current_level == "none" or not persona.enrichmentLevel:
            next_level = "quick"
        elif current_level == "quick":
            next_level = "strategic"
        elif current_level == "strategic":
            next_level = "complete"
        else:
            raise HTTPException(status_code=400, detail=f"Persona is already at maximum level: {current_level}")
        
        # Collect existing modules to avoid regeneration
        existing_modules = {
            "psychographicCore": persona.psychographicCore,
            "buyerJourney": persona.buyerJourney,
            "behavioralProfile": persona.behavioralProfile,
            "languageCommunication": persona.languageCommunication,
            "strategicInsights": persona.strategicInsights,
            "jobsToBeDone": persona.jobsToBeDone,
            "decisionProfile": persona.decisionProfile,
            "copyExamples": persona.copyExamples
        }
        
        print(f"[UPGRADE] {current_level.upper()} → {next_level.upper()} (reusing {sum(1 for v in existing_modules.values() if v)} existing modules)")
        
        # Perform upgrade with existing modules
        upgraded_persona = await enrich_persona_with_deep_modules(
            persona_id=persona_id,
            level=next_level,
            storage=storage,
            existing_modules=existing_modules
        )
        
        return upgraded_persona
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error upgrading persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upgrade persona: {str(e)}")

@app.delete("/api/persona/{persona_id}", status_code=204)
async def delete_user_persona(persona_id: str, user_id: str = Query(...)):
    """
    Delete a user persona by ID.
    Returns 204 No Content on success.
    """
    try:
        print(f"[DELETE PERSONA] persona_id={persona_id}, user_id={user_id}")
        
        # Verify ownership before deleting
        persona = await storage.get_user_persona_by_id(persona_id)
        print(f"[DELETE PERSONA] Found persona: {persona is not None}")
        
        if not persona:
            print(f"[DELETE PERSONA] ERROR: Persona not found")
            raise HTTPException(status_code=404, detail=f"Persona with id {persona_id} not found")
        
        print(f"[DELETE PERSONA] Persona userId: {persona.userId}, requesting user_id: {user_id}")
        
        if persona.userId != user_id:
            print(f"[DELETE PERSONA] ERROR: Access denied")
            raise HTTPException(status_code=403, detail="Access denied")
        
        deleted = await storage.delete_user_persona(persona_id)
        print(f"[DELETE PERSONA] Deleted result: {deleted}")
        
        if not deleted:
            print(f"[DELETE PERSONA] ERROR: Delete returned False")
            raise HTTPException(status_code=404, detail=f"Persona with id {persona_id} not found")
        
        print(f"[DELETE PERSONA] SUCCESS")
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DELETE PERSONA] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete persona: {str(e)}")

@app.get("/api/persona/list", response_model=List[UserPersona])
async def list_user_personas(user_id: str = Query(...)):
    """
    Get all personas for a specific user.
    """
    try:
        personas = await storage.list_user_personas(user_id)
        return personas
    except Exception as e:
        logger.error("Error listing personas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list personas: {str(e)}")

@app.post("/api/persona/set-active")
async def set_active_persona(user_id: str = Query(...), request: dict = Body(...)):
    """
    Set a persona as the active one for the user.
    """
    try:
        persona_id = request.get("personaId")
        if not persona_id:
            raise HTTPException(status_code=400, detail="personaId is required")
        
        success = await storage.set_active_persona(user_id, persona_id)
        if not success:
            raise HTTPException(status_code=404, detail="Persona not found or user not found")
        
        return {"success": True, "activePersonaId": persona_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error setting active persona: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set active persona: {str(e)}")

@app.get("/api/persona/{persona_id}", response_model=UserPersona)
async def get_persona_by_id(persona_id: str, user_id: str = Query(...)):
    """
    Get a specific persona by ID.
    """
    try:
        persona = await storage.get_user_persona_by_id(persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Persona with id {persona_id} not found")
        
        if persona.userId != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return persona
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting persona by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get persona: {str(e)}")

# Suggested Questions endpoint (personalized based on profile + expert expertise)
@app.get("/api/experts/{expert_id}/suggested-questions")
async def get_suggested_questions(expert_id: str):
    """
    Generate personalized suggested questions for a specific expert.
    Uses Perplexity AI to create context-aware questions based on:
    - User's business profile (industry, goals, challenges)
    - Expert's area of expertise
    
    Returns 3-5 highly relevant questions the user could ask.
    """
    try:
        from perplexity_research import perplexity_research
        
        # Get expert (supports both seed and custom experts)
        expert = await get_expert_by_id(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Get user's business profile
        user_id = "default_user"
        profile = await storage.get_business_profile(user_id)
        
        # Build context for Perplexity
        if profile:
            # Personalized questions based on profile
            context = f"""
Gere 5 perguntas altamente específicas e acionáveis que um empresário do setor de {profile.industry} deveria fazer para {expert.name} ({expert.title}).

Contexto do Negócio:
- Empresa: {profile.companyName}
- Setor: {profile.industry}
- Porte: {profile.companySize}
- Público-Alvo: {profile.targetAudience}
- Principais Produtos: {profile.mainProducts}
- Canais de Marketing: {', '.join(profile.channels) if profile.channels else 'Não especificado'}
- Faixa de Orçamento: {profile.budgetRange}
- Objetivo Principal: {profile.primaryGoal}
- Principal Desafio: {profile.mainChallenge}
- Prazo: {profile.timeline}

Áreas de Especialidade do Expert: {', '.join(expert.expertise[:5])}

Gere exatamente 5 perguntas que:
1. Sejam ESPECÍFICAS para a situação deste negócio (setor, porte, objetivos, desafios)
2. Aproveitem a expertise única e metodologia de {expert.name}
3. Sejam acionáveis e táticas (não teoria genérica)
4. Abordem o objetivo principal ({profile.primaryGoal}) ou desafio ({profile.mainChallenge}) do negócio
5. Sejam realistas para o orçamento dado ({profile.budgetRange}) e prazo ({profile.timeline})

IMPORTANTE: Responda SEMPRE em português brasileiro natural e fluente.
Formate cada pergunta como uma frase completa e natural que o usuário poderia fazer diretamente.
NÃO numere as perguntas nem adicione prefixos. Apenas retorne 5 perguntas, uma por linha.
"""
        else:
            # Generic questions based on expertise
            context = f"""
Gere 5 perguntas acionáveis que alguém poderia fazer para {expert.name} ({expert.title}) para obter conselhos práticos de marketing e estratégia.

Áreas de Especialidade do Expert: {', '.join(expert.expertise[:5])}

Gere exatamente 5 perguntas que:
1. Aproveitem a expertise única e metodologias de {expert.name}
2. Sejam acionáveis e táticas (não teóricas)
3. Cubram diferentes aspectos de sua expertise
4. Sejam específicas o suficiente para obter respostas úteis
5. Sejam realistas para pequenas e médias empresas

IMPORTANTE: Responda SEMPRE em português brasileiro natural e fluente.
Formate cada pergunta como uma frase completa e natural.
NÃO numere as perguntas nem adicione prefixos. Apenas retorne 5 perguntas, uma por linha.
"""
        
        # Use Perplexity to generate questions with lower temperature for consistency
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_research.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um consultor de estratégia de marketing que gera perguntas altamente específicas e acionáveis. SEMPRE responda em português brasileiro. Sempre retorne exatamente 5 perguntas, uma por linha, sem numeração ou prefixos."
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent, focused output
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse questions from response
        content = data["choices"][0]["message"]["content"]
        # Split by newlines and filter out empty lines
        questions = [q.strip() for q in content.split('\n') if q.strip()]
        
        # Clean up any numbering that might have been added despite instructions
        cleaned_questions = []
        for q in questions:
            # Remove common numbering patterns: "1. ", "1) ", "- ", "• "
            q_cleaned = q
            import re
            q_cleaned = re.sub(r'^\d+[\.\)]\s*', '', q_cleaned)  # Remove "1. " or "1) "
            q_cleaned = re.sub(r'^[-•]\s*', '', q_cleaned)  # Remove "- " or "• "
            if q_cleaned:
                cleaned_questions.append(q_cleaned)
        
        # Return up to 5 questions (in case more were generated)
        final_questions = cleaned_questions[:5]
        
        # Fallback if something went wrong
        if not final_questions:
            # Generic fallback based on expertise
            final_questions = [
                f"Como posso melhorar {expert.expertise[0].lower() if expert.expertise else 'minha estratégia'}?",
                f"Quais são as melhores práticas em {expert.expertise[1].lower() if len(expert.expertise) > 1 else 'marketing'}?",
                f"Como resolver desafios de {expert.expertise[2].lower() if len(expert.expertise) > 2 else 'negócios'}?"
            ]
        
        return {
            "expertId": expert_id,
            "expertName": expert.name,
            "questions": final_questions,
            "personalized": profile is not None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        # Missing PERPLEXITY_API_KEY
        if "PERPLEXITY_API_KEY" in str(e):
            # Return fallback questions instead of failing
            expert = await storage.get_expert(expert_id)
            if expert:
                return {
                    "expertId": expert_id,
                    "expertName": expert.name,
                    "questions": [
                        f"Como posso melhorar {expert.expertise[0].lower() if expert.expertise else 'minha estratégia'}?",
                        f"Quais são as melhores práticas em {expert.expertise[1].lower() if len(expert.expertise) > 1 else 'marketing'}?",
                        f"Como resolver desafios de {expert.expertise[2].lower() if len(expert.expertise) > 2 else 'negócios'}?"
                    ],
                    "personalized": False
                }
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Error generating suggested questions: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return fallback instead of failing
        try:
            expert = await storage.get_expert(expert_id)
            if expert:
                return {
                    "expertId": expert_id,
                    "expertName": expert.name,
                    "questions": [
                        f"Como posso melhorar {expert.expertise[0].lower() if expert.expertise else 'minha estratégia'}?",
                        f"Quais são as melhores práticas em {expert.expertise[1].lower() if len(expert.expertise) > 1 else 'marketing'}?",
                        f"Como resolver desafios de {expert.expertise[2].lower() if len(expert.expertise) > 2 else 'negócios'}?"
                    ],
                    "personalized": False
                }
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

# Business Insights endpoint (personalized tips based on profile)
@app.get("/api/insights")
async def get_business_insights():
    """
    Generate personalized business insights based on user's profile.
    Uses Perplexity AI to create context-aware tips and recommendations.
    
    Returns 3-4 actionable insights specific to the user's business situation.
    """
    try:
        from perplexity_research import perplexity_research
        
        # Get user's business profile
        user_id = "default_user"
        profile = await storage.get_business_profile(user_id)
        
        if not profile:
            # No profile, return empty insights
            return {
                "hasProfile": False,
                "insights": []
            }
        
        # Build context for Perplexity to generate insights
        context = f"""
Gere 4 insights de marketing específicos e acionáveis para este negócio:

Perfil do Negócio:
- Empresa: {profile.companyName}
- Setor: {profile.industry}
- Porte: {profile.companySize}
- Público-Alvo: {profile.targetAudience}
- Principais Produtos: {profile.mainProducts}
- Canais de Marketing: {', '.join(profile.channels) if profile.channels else 'Não especificado'}
- Faixa de Orçamento: {profile.budgetRange}
- Objetivo Principal: {profile.primaryGoal}
- Principal Desafio: {profile.mainChallenge}
- Prazo: {profile.timeline}

Gere exatamente 4 insights que:
1. Sejam ALTAMENTE ESPECÍFICOS para o setor ({profile.industry}), porte ({profile.companySize}) e situação deste negócio
2. Sejam ACIONÁVEIS - algo que possam implementar nos próximos 30 dias
3. Abordem o OBJETIVO PRINCIPAL ({profile.primaryGoal}) ou DESAFIO PRINCIPAL ({profile.mainChallenge})
4. Sejam realistas dado o orçamento ({profile.budgetRange}) e prazo ({profile.timeline})
5. Aproveitem tendências atuais de mercado e melhores práticas (dados 2024-2025)

Cada insight deve:
- Começar com uma categoria/tópico claro (ex: "Estratégia SEO:", "Marketing de Conteúdo:", "Anúncios Pagos:")
- Ter no máximo 1-2 frases
- Incluir táticas específicas, não conselhos genéricos
- Referenciar dados ou tendências recentes quando relevante

IMPORTANTE: Responda SEMPRE em português brasileiro natural e fluente.
Formato: Retorne 4 insights, um por linha, cada um começando com a categoria seguida de dois pontos.
NÃO numere. Formato de exemplo:
Redes Sociais: [insight específico aqui]
E-mail Marketing: [insight específico aqui]
"""
        
        # Use Perplexity to generate insights
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_research.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um estrategista de marketing que fornece insights hiper-específicos e acionáveis baseados no contexto do negócio. SEMPRE responda em português brasileiro. Sempre use dados e tendências recentes. Formate os insights como 'Categoria: insight acionável específico'."
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ],
                    "temperature": 0.4,
                    "max_tokens": 600,
                    "search_recency_filter": "month"  # Use recent data
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse insights from response
        content = data["choices"][0]["message"]["content"]
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Parse into structured insights (category + content)
        insights = []
        for line in lines:
            # Remove numbering if present
            import re
            line_cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
            line_cleaned = re.sub(r'^[-•]\s*', '', line_cleaned)
            
            # Try to split by first colon to get category
            if ':' in line_cleaned:
                parts = line_cleaned.split(':', 1)
                if len(parts) == 2:
                    insights.append({
                        "category": parts[0].strip(),
                        "content": parts[1].strip()
                    })
            else:
                # No colon, use whole line as content with generic category
                insights.append({
                    "category": "Dica Estratégica",
                    "content": line_cleaned
                })
        
        # Limit to 4 insights
        insights = insights[:4]
        
        # Fallback if something went wrong
        if not insights:
            insights = [
                {
                    "category": "Marketing Digital",
                    "content": f"Para empresas de {profile.industry}, foque em {profile.primaryGoal.lower()} através dos canais que você já usa."
                },
                {
                    "category": "Público-Alvo",
                    "content": f"Personalize sua mensagem para {profile.targetAudience} com conteúdo relevante e consistente."
                },
                {
                    "category": "Orçamento",
                    "content": f"Com orçamento de {profile.budgetRange}, priorize canais de alto ROI antes de expandir."
                }
            ]
        
        return {
            "hasProfile": True,
            "insights": insights,
            "profileSummary": {
                "companyName": profile.companyName,
                "industry": profile.industry,
                "primaryGoal": profile.primaryGoal
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        # Missing PERPLEXITY_API_KEY - return fallback
        if "PERPLEXITY_API_KEY" in str(e):
            user_id = "default_user"
            profile = await storage.get_business_profile(user_id)
            if profile:
                return {
                    "hasProfile": True,
                    "insights": [
                        {
                            "category": "Marketing Digital",
                            "content": f"Para empresas de {profile.industry}, foque em {profile.primaryGoal.lower()} através dos canais que você já usa."
                        },
                        {
                            "category": "Público-Alvo",
                            "content": f"Personalize sua mensagem para {profile.targetAudience} com conteúdo relevante e consistente."
                        },
                        {
                            "category": "Orçamento",
                            "content": f"Com orçamento de {profile.budgetRange}, priorize canais de alto ROI antes de expandir."
                        }
                    ],
                    "profileSummary": {
                        "companyName": profile.companyName,
                        "industry": profile.industry,
                        "primaryGoal": profile.primaryGoal
                    }
                }
            return {"hasProfile": False, "insights": []}
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Error generating business insights: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return fallback instead of failing
        try:
            user_id = "default_user"
            profile = await storage.get_business_profile(user_id)
            if profile:
                return {
                    "hasProfile": True,
                    "insights": [
                        {
                            "category": "Marketing Digital",
                            "content": f"Para empresas de {profile.industry}, foque em {profile.primaryGoal.lower()}."
                        }
                    ],
                    "profileSummary": {
                        "companyName": profile.companyName,
                        "industry": profile.industry,
                        "primaryGoal": profile.primaryGoal
                    }
                }
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

# Council Analysis endpoints
@app.post("/api/council/analyze", response_model=CouncilAnalysis)
async def create_council_analysis(data: CouncilAnalysisCreate, user_id: str = Query(...)):
    """
    Run collaborative analysis by council of marketing legend experts.
    
    This endpoint:
    1. Conducts Perplexity research (if user has BusinessProfile)
    2. Gets independent analyses from 8 marketing legends
    3. Synthesizes consensus recommendation
    
    Args:
        user_id: User identifier (REQUIRED) - passed as query parameter
    """
    
    try:
        # Get user's business profile (optional)
        profile = await storage.get_business_profile(user_id)
        
        # Get user's persona for deep context (PRIORITY - richer than business profile)
        persona = await storage.get_user_persona(user_id)
        if persona:
            logger.info("Persona loaded: {persona.companyName} (enrichment: {persona.enrichmentStatus})")
        
        # Get experts to consult (all if not specified)
        if data.expertIds:
            experts = []
            for expert_id in data.expertIds:
                # Use get_expert_by_id to support both SEED and DB experts
                expert = await get_expert_by_id(expert_id, include_system_prompt=True)
                if not expert:
                    raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")
                experts.append(expert)
        else:
            # Use all available experts (combined SEED + DB)
            experts = await get_all_experts_combined()
            if not experts:
                raise HTTPException(status_code=400, detail="No experts available for analysis")
            # Limit to top 8 experts for performance
            experts = experts[:8]
        
        # Run council analysis WITH persona context
        analysis = await council_orchestrator.analyze(
            problem=data.problem,
            experts=experts,
            profile=profile,
            user_id=user_id,
            persona=persona  # NEW: Pass enriched persona
        )
        
        # Save analysis
        await storage.save_council_analysis(analysis)
        
        return analysis
    
    except HTTPException:
        raise
    except ValueError as e:
        # Missing API keys (ANTHROPIC_API_KEY, PERPLEXITY_API_KEY)
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable: {error_msg}"
            )
        raise
    except Exception as e:
        logger.error("Error creating council analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create council analysis: {str(e)}")

@app.post("/api/council/analyze-stream")
async def create_council_analysis_stream(data: CouncilAnalysisCreate, user_id: str = Query(...)):
    """
    Run collaborative analysis with Server-Sent Events streaming.
    
    Emits real-time progress events:
    - expert_started: When expert begins analysis
    - expert_researching: During Perplexity research
    - expert_analyzing: During Claude analysis
    - expert_completed: When expert finishes
    - consensus_started: Before synthesis
    - analysis_complete: Final result with full analysis
    
    Args:
        user_id: User identifier (REQUIRED) - passed as query parameter
    """
    
    async def event_generator():
        # Helper to format SSE events (defined outside try block for exception handling)
        def sse_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        
        try:
            # Get user's business profile (optional)
            profile = await storage.get_business_profile(user_id)
            
            # Get user's persona for deep context (PRIORITY)
            persona = await storage.get_user_persona(user_id)
            if persona:
                print(f"[COUNCIL STREAM] Persona loaded: {persona.companyName}")
            
            # Get experts to consult
            if data.expertIds:
                experts = []
                for expert_id in data.expertIds:
                    # Use get_expert_by_id to support both SEED and DB experts
                    expert = await get_expert_by_id(expert_id, include_system_prompt=True)
                    if not expert:
                        yield sse_event("error", {"message": f"Expert {expert_id} not found"})
                        return
                    experts.append(expert)
            else:
                # Use all available experts (combined SEED + DB)
                experts = await get_all_experts_combined()
                if not experts:
                    yield sse_event("error", {"message": "No experts available"})
                    return
                # Limit to top 8 experts for performance
                experts = experts[:8]
            
            # Emit initial event with expert list
            yield sse_event("analysis_started", {
                "expertCount": len(experts),
                "experts": [{"id": e.id, "name": e.name, "avatar": e.avatar} for e in experts]
            })
            
            # Run council analysis with progress events
            # We'll need to modify council_orchestrator to emit events
            # For now, we'll simulate the workflow
            
            contributions = []
            research_findings = None
            
            # Perplexity research phase
            if profile:
                yield sse_event("research_started", {
                    "message": "Conducting market research..."
                })
                
                from perplexity_research import PerplexityResearch
                perplexity = PerplexityResearch()
                try:
                    research_result = await perplexity.research(
                        problem=data.problem,
                        profile=profile
                    )
                    research_findings = research_result.get("findings", "")
                    
                    yield sse_event("research_completed", {
                        "message": "Market research complete",
                        "citations": len(research_result.get("sources", []))
                    })
                except Exception as e:
                    yield sse_event("research_failed", {
                        "message": f"Research failed: {str(e)}"
                    })
            
            # Analyze with each expert (emitting events for each)
            from crew_council import council_orchestrator
            
            # Process experts sequentially for event emission
            for expert in experts:
                yield sse_event("expert_started", {
                    "expertId": expert.id,
                    "expertName": expert.name,
                    "message": f"{expert.name} is analyzing..."
                })
                
                try:
                    print(f"[Council Stream] Starting analysis for {expert.name}")
                    contribution = await council_orchestrator._get_expert_analysis(
                        expert=expert,
                        problem=data.problem,
                        profile=profile,
                        research_findings=research_findings,
                        persona=persona  # NEW: Pass persona to each expert
                    )
                    contributions.append(contribution)
                    print(f"[Council Stream] Completed analysis for {expert.name}")
                    
                    yield sse_event("expert_completed", {
                        "expertId": expert.id,
                        "expertName": expert.name,
                        "insightCount": len(contribution.keyInsights),
                        "recommendationCount": len(contribution.recommendations)
                    })
                except Exception as e:
                    print(f"[Council Stream] Expert {expert.name} failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    yield sse_event("expert_failed", {
                        "expertId": expert.id,
                        "expertName": expert.name,
                        "error": str(e)
                    })
            
            if not contributions:
                yield sse_event("error", {"message": "All expert analyses failed"})
                return
            
            # Synthesize consensus
            yield sse_event("consensus_started", {
                "message": "Synthesizing council consensus..."
            })
            
            print(f"[Council Stream] Synthesizing consensus from {len(contributions)} contributions")
            consensus = await council_orchestrator._synthesize_consensus(
                problem=data.problem,
                contributions=contributions,
                research_findings=research_findings
            )
            print(f"[Council Stream] Consensus generated successfully")
            
            # Create final analysis object
            from models import CouncilAnalysis, AgentContribution
            import uuid
            
            analysis = CouncilAnalysis(
                id=str(uuid.uuid4()),
                userId=user_id,
                problem=data.problem,
                profileId=profile.id if profile else None,
                marketResearch=research_findings,
                contributions=contributions,
                consensus=consensus
            )
            
            # Save analysis
            await storage.save_council_analysis(analysis)
            
            # Send final complete event
            print(f"[Council Stream] Sending analysis_complete event")
            yield sse_event("analysis_complete", {
                "analysisId": analysis.id,
                "analysis": {
                    "id": analysis.id,
                    "problem": analysis.problem,
                    "contributions": [
                        {
                            "expertId": c.expertId,
                            "expertName": c.expertName,
                            "analysis": c.analysis,
                            "keyInsights": c.keyInsights,
                            "recommendations": c.recommendations
                        }
                        for c in analysis.contributions
                    ],
                    "consensus": analysis.consensus
                }
            })
            print(f"[Council Stream] Stream completed successfully")
            
        except Exception as e:
            print(f"[Council Stream] Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield sse_event("error", {
                "message": f"Analysis failed: {str(e)}"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.get("/api/council/analyses", response_model=List[CouncilAnalysis])
async def get_council_analyses():
    """Get all council analyses for the current user"""
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    return await storage.get_council_analyses(user_id)

@app.get("/api/council/analyses/{analysis_id}", response_model=CouncilAnalysis)
async def get_council_analysis(analysis_id: str):
    """Get a specific council analysis by ID"""
    analysis = await storage.get_council_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Council analysis not found")
    return analysis

# ============================================================================
# COUNCIL ROOM CHAT ENDPOINTS (Follow-up conversational mode)
# ============================================================================

from models import CouncilChatMessage, CouncilChatRequest, StreamContribution

@app.get("/api/council/chat/{session_id}/messages", response_model=List[CouncilChatMessage])
async def get_council_chat_messages(session_id: str):
    """Get chat history for a council session"""
    messages = await storage.get_council_messages(session_id)
    return messages

@app.get("/api/council/chat/{session_id}/stream")
async def council_chat_stream(session_id: str, message: str):
    """
    Follow-up chat with council using SSE streaming.
    
    Query params:
    - message: User's follow-up question
    
    Streams expert contributions sequentially with attribution:
    - event: contribution - Individual expert response
    - event: synthesis - Final consensus
    - event: complete - End of stream
    """
    print(f"[SSE ENDPOINT] Council chat stream called - session_id={session_id}, message={message[:50]}")
    user_id = "default_user"
    
    async def event_generator():
        def sse_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        try:
            print(f"[SSE] Starting event generator for session {session_id}")
            
            # Load session to get context
            print(f"[SSE] Loading analysis...")
            analysis = await storage.get_council_analysis(session_id)
            if not analysis:
                print(f"[SSE] ERROR: Analysis not found for session {session_id}")
                yield sse_event("error", {"message": "Council session not found"})
                return
            
            print(f"[SSE] Analysis loaded successfully - {len(analysis.contributions)} experts")
            
            # Load conversation history
            print(f"[SSE] Loading conversation history...")
            history = await storage.get_council_messages(session_id)
            print(f"[SSE] Loaded {len(history)} previous messages")
            
            # Get experts from original analysis
            expert_ids = [c.expertId for c in analysis.contributions]
            print(f"[SSE] Getting {len(expert_ids)} experts...")
            experts = []
            for expert_id in expert_ids:
                # Use get_expert_by_id to support both SEED and DB experts
                expert = await get_expert_by_id(expert_id, include_system_prompt=True)
                if expert:
                    experts.append(expert)
            
            print(f"[SSE] Loaded {len(experts)} experts successfully")
            
            if not experts:
                print(f"[SSE] ERROR: No experts found!")
                yield sse_event("error", {"message": "No experts found for this session"})
                return
            
            # Save user message
            user_message_id = str(uuid.uuid4())
            await storage.create_council_message(
                session_id=session_id,
                role="user",
                content=message,
                contributions=None
            )
            
            yield sse_event("user_message", {
                "id": user_message_id,
                "content": message,
                "createdAt": datetime.utcnow().isoformat()
            })
            
            # Load user persona for context enrichment
            print(f"[SSE] Loading user persona...")
            persona = await storage.get_user_persona(user_id)
            if persona:
                print(f"[SSE] Persona loaded: {persona.companyName}")
            else:
                print(f"[SSE] No persona found for user")
            
            # Build context from analysis + history + persona
            print(f"[SSE] Building context...")
            context = await _build_council_context(analysis, history, message, persona)
            print(f"[SSE] Context built - {len(context)} chars")
            
            # Stream contributions from each expert (ROUNDTABLE: experts see previous contributions)
            contributions_data = []
            current_round_contributions = []  # Accumulate for roundtable discussion
            print(f"[SSE] Starting expert iteration (roundtable mode)...")
            
            for idx, expert in enumerate(experts):
                print(f"[SSE] Processing expert {idx+1}/{len(experts)}: {expert.name}")
                print(f"[SSE] Expert will see {len(current_round_contributions)} colleague contribution(s)")
                yield sse_event("expert_thinking", {
                    "expertName": expert.name,
                    "order": idx
                })
                
                # Get expert analysis with full context + colleague contributions (roundtable)
                try:
                    print(f"[SSE] Calling CrewAI for {expert.name}...")
                    contribution = await council_orchestrator._get_expert_analysis(
                        expert=expert,
                        problem=message,
                        research_findings=None,  # No new research for follow-up
                        profile=None,
                        user_id=user_id,
                        user_context={"analysis_context": context},
                        colleague_contributions=current_round_contributions  # Pass previous experts' contributions
                    )
                    print(f"[SSE] Got contribution from {expert.name} - {len(contribution.analysis)} chars")
                    
                    # Stream this expert's contribution
                    yield sse_event("contribution", {
                        "expertName": contribution.expertName,
                        "content": contribution.analysis,
                        "order": idx
                    })
                    
                    contributions_data.append(StreamContribution(
                        expertName=contribution.expertName,
                        content=contribution.analysis,
                        order=idx
                    ))
                    
                    # Add to current round for next experts to see (roundtable)
                    current_round_contributions.append({
                        "expert_name": contribution.expertName,
                        "contribution": contribution.analysis
                    })
                    print(f"[SSE] Contribution {idx+1} added to list. Next expert will see {len(current_round_contributions)} colleague(s)")
                    
                except Exception as e:
                    print(f"[SSE] ERROR: Expert {expert.name} failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Synthesize consensus
            print(f"[SSE] Starting synthesis with {len(contributions_data)} contributions...")
            yield sse_event("synthesizing", {})
            
            # Parse insights and recommendations from each contribution
            parsed_contributions = []
            for c in contributions_data:
                try:
                    insights = council_orchestrator._extract_bullet_points(c.content, "Key Insights")
                    recommendations = council_orchestrator._extract_bullet_points(c.content, "Actionable Recommendations")
                    
                    parsed_contributions.append(AgentContribution(
                        expertId="",
                        expertName=c.expertName,
                        analysis=c.content,
                        keyInsights=insights,
                        recommendations=recommendations
                    ))
                    print(f"[SSE] Parsed {c.expertName}: {len(insights)} insights, {len(recommendations)} recommendations")
                except Exception as e:
                    print(f"[SSE] Warning: Failed to parse bullet points for {c.expertName}: {str(e)}")
                    # Fallback: use contribution with full analysis text but empty structured sections
                    parsed_contributions.append(AgentContribution(
                        expertId="",
                        expertName=c.expertName,
                        analysis=c.content,
                        keyInsights=[],
                        recommendations=[]
                    ))
            
            synthesis = await council_orchestrator._synthesize_consensus(
                problem=message,
                contributions=parsed_contributions,
                research_findings=None
            )
            print(f"[SSE] Synthesis complete - {len(synthesis)} chars")
            
            yield sse_event("synthesis", {
                "content": synthesis
            })
            print(f"[SSE] Synthesis event emitted")
            
            # Save assistant message with contributions
            print(f"[SSE] Saving assistant message with {len(contributions_data)} contributions")
            contrib_dicts = [c.model_dump() for c in contributions_data]
            print(f"[SSE] Contributions data: {contrib_dicts}")
            
            message_id = await storage.create_council_message(
                session_id=session_id,
                role="assistant",
                content=synthesis,
                contributions=json.dumps(contrib_dicts)
            )
            
            print(f"[SSE] Saved message ID: {message_id}")
            
            yield sse_event("complete", {})
            
        except Exception as e:
            print(f"Council chat stream error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield sse_event("error", {"message": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def _build_council_context(
    analysis: CouncilAnalysis,
    history: List[CouncilChatMessage],
    new_question: str,
    persona: Optional['UserPersona'] = None
) -> str:
    """Build rich context for follow-up including analysis + history + ENRICHED persona"""
    
    # Start with ENRICHED persona context if available
    context = ""
    if persona:
        print(f"[COUNCIL CONTEXT] Adding ENRICHED persona context for {persona.companyName}")
        context += _build_enriched_persona_context(persona)
        context += "\n\n"
    
    context += f"""**CONTEXTO DA ANÁLISE INICIAL:**

Problema Original: {analysis.problem}

Consenso do Conselho:
{analysis.consensus}

"""
    
    # Add contributions from original analysis
    context += "**CONTRIBUIÇÕES ORIGINAIS DOS ESPECIALISTAS:**\n\n"
    for contrib in analysis.contributions:
        context += f"**{contrib.expertName}:**\n{contrib.analysis[:500]}...\n\n"
    
    # Add conversation history
    if history:
        context += "**HISTÓRICO DA CONVERSA:**\n\n"
        for msg in history:
            if msg.role == "user":
                context += f"User perguntou: {msg.content}\n\n"
            else:
                context += f"Conselho respondeu: {msg.content[:300]}...\n\n"
    
    context += f"\n**NOVA PERGUNTA DO USER:**\n{new_question}\n\n"
    context += """**INSTRUÇÕES:**
- Você JÁ analisou este negócio em profundidade
- Referencie insights da análise inicial quando relevante
- Continue a conversa de forma natural
- Não peça informações já fornecidas
"""
    
    return context

# ============================================================================
# PERSONA BUILDER ENDPOINTS
# ============================================================================

from models import Persona, PersonaCreate
from reddit_research import reddit_research
from datetime import datetime as dt

@app.post("/api/personas", response_model=Persona)
async def create_persona(data: PersonaCreate):
    """
    Create a persona using Reddit research.
    
    Modes:
    - quick: 1-2 min, basic insights (5-7 pain points, goals, values)
    - strategic: 5-10 min, deep analysis (behavioral patterns, content preferences)
    """
    user_id = "default_user"  # TODO: replace with actual user auth
    
    try:
        # Conduct Reddit research based on mode
        if data.mode == "quick":
            research_data = await reddit_research.research_quick(
                target_description=data.targetDescription,
                industry=data.industry
            )
        else:  # strategic
            research_data = await reddit_research.research_strategic(
                target_description=data.targetDescription,
                industry=data.industry,
                additional_context=data.additionalContext
            )
        
        # Add timestamp to research data
        research_data["researchData"]["timestamp"] = dt.utcnow().isoformat()
        
        # Generate persona name if not provided
        persona_name = f"Persona: {data.targetDescription[:50]}"
        
        # Prepare persona data
        persona_payload = {
            "name": persona_name,
            "researchMode": data.mode,
            **research_data
        }
        
        # Save to database
        persona = await storage.create_persona(user_id, persona_payload)
        
        return persona
    
    except ValueError as e:
        # Missing API keys
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable: {error_msg}"
            )
        raise
    except Exception as e:
        logger.error("Error creating persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")

@app.get("/api/personas", response_model=List[Persona])
async def get_personas():
    """Get all personas for the current user"""
    user_id = "default_user"
    return await storage.get_personas(user_id)

@app.get("/api/personas/{persona_id}", response_model=Persona)
async def get_persona(persona_id: str):
    """Get a specific persona by ID"""
    persona = await storage.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

@app.patch("/api/personas/{persona_id}", response_model=Persona)
async def update_persona(persona_id: str, updates: dict):
    """Update a persona (e.g., edit name, add notes)"""
    persona = await storage.update_persona(persona_id, updates)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

@app.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona"""
    success = await storage.delete_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"success": True}

@app.get("/api/personas/{persona_id}/download")
async def download_persona(persona_id: str):
    """Download persona as JSON"""
    persona = await storage.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Convert Pydantic model to dict and return as JSON download
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=persona.model_dump(mode='json'),
        headers={
            "Content-Disposition": f"attachment; filename=persona_{persona_id}.json"
        }
    )


# ============================================
# ANALYTICS & INSIGHTS DASHBOARD ENDPOINTS
# ============================================

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    """
    Get high-level analytics overview: total conversations, experts, councils, streak, last active.
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        stats = await analytics_engine.get_overview_stats(user_id)
        return stats
    except Exception as e:
        print(f"[Analytics] Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/timeline")
async def get_analytics_timeline(days: int = 30):
    """
    Get activity timeline for last N days.
    Returns array of {date, chats, councils, total}
    """
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        user_id = "default"  # TODO: Get from auth context
        timeline = await analytics_engine.get_activity_timeline(user_id=user_id, days=days)
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analytics] Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/top-experts")
async def get_top_experts(limit: int = 10):
    """
    Get ranking of most consulted experts.
    Returns array of {expertId, expertName, category, consultations, lastConsulted, avatar}
    """
    try:
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
        
        user_id = "default"  # TODO: Get from auth context
        experts = await analytics_engine.get_top_experts(user_id=user_id, limit=limit)
        return experts
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analytics] Error getting top experts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/categories")
async def get_category_distribution():
    """
    Get consultation count by category.
    Returns object like {categoryName: count}
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        categories = await analytics_engine.get_category_distribution(user_id=user_id)
        return categories
    except Exception as e:
        print(f"[Analytics] Error getting category distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/highlights")
async def get_analytics_highlights():
    """
    Get user's saved favorites and top insights.
    Returns {favoriteMessages, topCouncilInsights, referencedCampaigns}
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        highlights = await analytics_engine.get_highlights(user_id)
        return highlights
    except Exception as e:
        print(f"[Analytics] Error getting highlights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/recommendations")
async def get_analytics_recommendations():
    """
    Generate AI-powered recommendations based on usage patterns.
    Returns array of {type, title, description, action}
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        recommendations = await analytics_engine.generate_recommendations(user_id)
        return recommendations
    except Exception as e:
        print(f"[Analytics] Error generating recommendations: {e}")
        # Return fallback instead of error
        return [{
            "type": "system_message",
            "title": "Continue explorando",
            "description": "Consulte mais especialistas para receber recomendações personalizadas!",
            "action": "Ver Categorias"
        }]


@app.post("/api/analytics/seed")
async def seed_analytics():
    """
    Seed analytics database with 30 days of realistic test data.
    For development/testing only.
    """
    try:
        await seed_analytics_data()
        return {"success": True, "message": "Analytics data seeded successfully"}
    except Exception as e:
        print(f"[Analytics] Error seeding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analytics/seed")
async def clear_analytics():
    """
    Clear all analytics data. For development/testing only.
    """
    try:
        await clear_analytics_data()
        return {"success": True, "message": "Analytics data cleared successfully"}
    except Exception as e:
        print(f"[Analytics] Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AI PROMPT ENHANCEMENT
# ============================================

@app.post("/api/ai/enhance-prompt")
async def enhance_prompt(
    data: dict = Body(...),
    user_id: str = Query(...)
):
    """
    Enhance user prompts using Claude AI.
    Makes descriptions more detailed, strategic, and professional.
    
    Supported field types:
    - target_audience: Expands buyer persona descriptions
    - challenge: Expands business challenge descriptions
    - goal: Expands business goal descriptions
    """
    try:
        # Extract and validate inputs
        text = data.get("text", "").strip()
        field_type = data.get("field_type", "")
        context = data.get("context", {})
        
        # Validation
        if not text or len(text) < 10:
            raise HTTPException(
                status_code=400,
                detail="Texto muito curto para melhorar. Escreva pelo menos uma frase completa."
            )
        
        if len(text) > 500:
            raise HTTPException(
                status_code=400,
                detail="Texto muito longo. Máximo de 500 caracteres."
            )
        
        if field_type not in ["target_audience", "challenge", "goal"]:
            raise HTTPException(
                status_code=400,
                detail="Tipo de campo inválido. Use: target_audience, challenge, ou goal"
            )
        
        # Check cache first (avoid duplicate API calls)
        from cache import cache_manager, make_cache_key, hash_data
        cache_key = make_cache_key("ai_enhance", field_type, hash_data(text + str(context)))
        
        cached = await cache_manager.get(cache_key)
        if cached:
            logger.info("AI enhance cache hit", field_type=field_type, user_id=user_id)
            return cached
        
        # Build system prompt based on field type
        if field_type == "target_audience":
            industry = context.get("industry", "")
            company_size = context.get("companySize", "")
            
            system_prompt = """Você é um especialista em marketing estratégico e definição de buyer personas.
Sua tarefa é expandir descrições básicas de público-alvo em perfis ricos e detalhados."""
            
            user_prompt = f"""Expanda esta descrição de público-alvo tornando-a muito mais detalhada e estratégica:

TEXTO ORIGINAL:
{text}

CONTEXTO:
- Indústria: {industry or 'Não especificada'}
- Tamanho da empresa: {company_size or 'Não especificado'}

INSTRUÇÕES:
Expanda adicionando:
1. DEMOGRAFIA: idade, gênero, localização, renda, cargo/função
2. PSICOGRAFIA: valores, crenças, estilo de vida, aspirações, medos
3. COMPORTAMENTOS: hábitos de compra, canais preferidos, fontes de informação, influenciadores
4. DORES E MOTIVAÇÕES: principais frustrações, o que os motiva, gatilhos de compra
5. LINGUAGEM: tom e estilo que ressoam com eles

FORMATO:
- Seja específico e detalhado (3-5x mais texto)
- Use estrutura organizada (pode usar seções)
- Mantenha tom profissional mas acessível
- Em português brasileiro

IMPORTANTE:
- Retorne APENAS o texto melhorado
- Não inclua títulos como "Público-Alvo:" ou "Descrição:"
- Não adicione explicações sobre o que você fez
- Seja direto e prático"""
        
        elif field_type == "challenge":
            industry = context.get("industry", "")
            primary_goal = context.get("primaryGoal", "")
            
            system_prompt = """Você é um consultor de marketing estratégico especializado em diagnóstico de problemas de negócio.
Sua tarefa é expandir descrições superficiais de desafios em análises profundas e acionáveis."""
            
            user_prompt = f"""Expanda esta descrição de desafio de negócio tornando-a muito mais estratégica e detalhada:

TEXTO ORIGINAL:
{text}

CONTEXTO:
- Indústria: {industry or 'Não especificada'}
- Objetivo principal: {primary_goal or 'Não especificado'}

INSTRUÇÕES:
Expanda incluindo:
1. RAIZ DO PROBLEMA: causas subjacentes, por que está acontecendo
2. IMPACTO NO NEGÓCIO: métricas afetadas, custo da inação
3. CONTEXTO DA INDÚSTRIA: particularidades do setor, benchmarks
4. OBSTÁCULOS RELACIONADOS: problemas conectados, efeitos em cascata
5. CONSEQUÊNCIAS: o que acontece se não resolver (curto e longo prazo)

FORMATO:
- Seja específico e estratégico (2-3x mais texto)
- Use estrutura clara (pode usar seções ou bullets)
- Quantifique quando possível
- Em português brasileiro

IMPORTANTE:
- Retorne APENAS o texto melhorado
- Não inclua títulos como "Desafio:" ou "Análise:"
- Não adicione explicações sobre o que você fez
- Seja direto e prático"""
        
        else:  # goal
            industry = context.get("industry", "")
            
            system_prompt = """Você é um estrategista de marketing focado em definição de objetivos SMART.
Sua tarefa é transformar objetivos vagos em metas claras e acionáveis."""
            
            user_prompt = f"""Expanda este objetivo de negócio tornando-o mais específico e estratégico:

TEXTO ORIGINAL:
{text}

CONTEXTO:
- Indústria: {industry or 'Não especificada'}

INSTRUÇÕES:
Expanda adicionando:
1. ESPECIFICIDADE: o que exatamente quer alcançar
2. MÉTRICAS: KPIs concretos, números-alvo
3. TIMELINE: quando espera resultados
4. ESTRATÉGIA: principais alavancas para atingir o objetivo
5. RECURSOS: o que precisa estar em place

Retorne APENAS o texto melhorado, sem títulos ou explicações."""
        
        # Call Claude API using resilient client
        from anthropic_client import get_anthropic_client
        client = get_anthropic_client()
        
        logger.info(
            "Enhancing prompt with AI",
            user_id=user_id,
            field_type=field_type,
            original_length=len(text)
        )
        
        response = await client.create_message(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            max_tokens=800,
            temperature=0.7
        )
        
        # Extract text from response
        enhanced_text = response.content[0].text.strip()
        
        # Build result
        result = {
            "enhanced_text": enhanced_text,
            "original_length": len(text),
            "enhanced_length": len(enhanced_text),
            "field_type": field_type,
            "improvement_ratio": round(len(enhanced_text) / len(text), 2)
        }
        
        # Cache result for 24 hours
        await cache_manager.set(cache_key, result, 24 * 60 * 60)
        
        # Log analytics
        logger.info(
            "AI prompt enhanced successfully",
            user_id=user_id,
            field_type=field_type,
            original_length=len(text),
            enhanced_length=len(enhanced_text),
            improvement_ratio=result["improvement_ratio"]
        )
        
        # Optional: Save to analytics table
        try:
            await storage.log_activity(
                user_id=user_id,
                activity_type="ai_prompt_enhance",
                metadata={
                    "field_type": field_type,
                    "original_length": len(text),
                    "enhanced_length": len(enhanced_text),
                    "improvement_ratio": result["improvement_ratio"]
                }
            )
        except Exception as e:
            logger.warning("Failed to log AI enhance activity", error=str(e))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error enhancing prompt", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao melhorar texto: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
