from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Body
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
import httpx

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
    if env == "production":
        # In production, REQUIRE Replit environment variables for security
        replit_domain = os.getenv("REPL_SLUG", "")
        replit_owner = os.getenv("REPL_OWNER", "")
        if not replit_domain or not replit_owner:
            raise ValueError(
                "REPL_SLUG and REPL_OWNER environment variables are required in production for CORS security"
            )
        return [
            f"https://{replit_domain}-{replit_owner}.replit.app",
            f"https://{replit_domain}.{replit_owner}.repl.co",
        ]
    else:
        # Development: allow localhost
        return ["http://localhost:5000", "http://127.0.0.1:5000"]

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
    # Initialize PostgreSQL connection pool
    print("[Startup] Initializing PostgreSQL storage...")
    await storage.initialize()
    print("[Startup] PostgreSQL storage initialized successfully")
    
    # NOTE: Seed experts are now served from CloneRegistry (18 HIGH_FIDELITY experts with avatars)
    # PostgreSQL only stores CUSTOM experts created by users via /api/experts/auto-clone
    # Seeding disabled to prevent duplicates
    # await seed_legends(storage)
    print("[Startup] Seed experts loaded from CloneRegistry. PostgreSQL ready for custom experts.")

@app.on_event("shutdown")
async def shutdown_event():
    # Close PostgreSQL connection pool
    print("[Shutdown] Closing PostgreSQL storage...")
    await storage.close()
    print("[Shutdown] PostgreSQL storage closed successfully")

# Health check
@app.get("/")
async def root():
    return {"message": "O Conselho Marketing Legends API", "status": "running"}

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

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
async def register_user(data: RegisterRequest):
    """Register new user with invite code"""
    
    # Validate invite code
    invite = await storage.get_invite(data.inviteCode)
    if not invite:
        raise HTTPException(status_code=400, detail="Código de convite inválido")
    
    if invite["usedBy"]:
        raise HTTPException(status_code=400, detail="Este código de convite já foi utilizado")
    
    # Check if email already exists
    existing_user = await storage.get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Hash password
    password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    user = await storage.create_user(data.username, data.email, password_hash)
    
    # Mark invite as used
    await storage.use_invite(data.inviteCode, user["id"])
    
    # Decrement creator's available invites
    creator = await storage.get_user_by_id(invite["creatorId"])
    if creator and creator["availableInvites"] > 0:
        await storage.update_user_invites(invite["creatorId"], creator["availableInvites"] - 1)
    
    # Return user with default role (backward compatibility)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        availableInvites=user["availableInvites"],
        role=user.get("role", "user"),
        createdAt=user["createdAt"]
    )

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
        createdAt=user["createdAt"]
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
        createdAt=user["createdAt"]
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
    companyName: Optional[str]
    industry: Optional[str]
    companySize: Optional[str]
    targetAudience: Optional[str]
    goals: Optional[List[str]]
    mainChallenge: Optional[str]
    enrichmentLevel: Optional[str]
    completedAt: Optional[datetime]
    createdAt: datetime
    updatedAt: datetime

@app.post("/api/onboarding/save", response_model=OnboardingStatusResponse)
async def save_onboarding(data: OnboardingSaveRequest, user_id: str):
    """Save onboarding progress for authenticated user"""
    
    # Convert Pydantic model to dict
    onboarding_data = data.model_dump(exclude_unset=True)
    
    # Save to database
    result = await storage.save_onboarding_progress(user_id, onboarding_data)
    
    return OnboardingStatusResponse(**result)

@app.get("/api/onboarding/status", response_model=Optional[OnboardingStatusResponse])
async def get_onboarding_status(user_id: str):
    """Get onboarding status for authenticated user"""
    result = await storage.get_onboarding_status(user_id)
    
    if not result:
        return None
    
    return OnboardingStatusResponse(**result)

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
async def get_expert_by_id(expert_id: str) -> Optional[Expert]:
    """
    Get a specific expert by ID, supporting both seed and custom experts.
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
            
            return Expert(
                id=expert_id,
                name=expert_name,
                title=clone_instance.title,
                bio=clone_instance.bio,
                expertise=clone_instance.expertise,
                systemPrompt="",  # Not exposed for seed experts
                avatar=avatar_path,
                expertType=ExpertType.HIGH_FIDELITY,
                category=category,
            )
        return None
    
    # Otherwise, try to get from PostgreSQL (custom expert)
    return await storage.get_expert(expert_id)

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
    
    # Combine both sources
    return seed_experts + custom_experts

# Expert endpoints
@app.get("/api/experts", response_model=List[Expert])
async def get_experts(category: Optional[str] = None):
    """
    Get all marketing legend experts, optionally filtered by category.
    Combines HIGH_FIDELITY seed experts from CloneRegistry + CUSTOM experts from PostgreSQL.
    
    Query params:
    - category: Filter by category ID (e.g., "growth", "marketing", "content")
    """
    # Get all experts using shared helper
    all_experts = await get_all_experts_combined()
    
    # Filter by category if provided
    if category:
        all_experts = [e for e in all_experts if e.category.value == category]
    
    return all_experts

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
        print(f"Error auto-cloning expert: {str(e)}")
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
        print(f"Error in test chat: {str(e)}")
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
        print(f"Error generating samples: {str(e)}")
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
        # Get all available experts
        experts = await storage.get_experts()
        
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
        
        # Enrich recommendations with expert data (avatar, stars)
        enriched_recommendations = []
        for rec in recommendations_data.get("recommendations", []):
            # Get full expert data from storage
            expert = await storage.get_expert(rec["expertId"])
            
            # Build enriched recommendation
            enriched_rec = {
                "expertId": rec["expertId"],
                "expertName": rec["expertName"],
                "avatar": expert.avatar if expert else None,
                "relevanceScore": rec["relevanceScore"],
                "stars": rec["relevanceScore"],  # Copy relevanceScore to stars
                "justification": rec["justification"]
            }
            enriched_recommendations.append(enriched_rec)
        
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
        print(f"Error recommending experts: {json.dumps(error_context, ensure_ascii=False)}")
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
        print(f"Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
    finally:
        # Ensure file is closed
        await file.close()

# Conversation endpoints
@app.get("/api/conversations", response_model=List[Conversation])
async def get_conversations(expertId: Optional[str] = None):
    """Get conversations, optionally filtered by expert"""
    return await storage.get_conversations(expertId)

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    conversation = await storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.post("/api/conversations", response_model=Conversation, status_code=201)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation with an expert"""
    try:
        # Verify expert exists
        expert = await storage.get_expert(data.expertId)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        conversation = await storage.create_conversation(data)
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

# Message endpoints
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
        
        # Get expert
        expert = await storage.get_expert(conversation.expertId)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Get conversation history BEFORE saving the new user message
        # This way we pass all previous messages to the agent
        all_messages = await storage.get_messages(conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages
        ]
        
        # Get user's persona for context injection (Persona Intelligence Hub)
        user_id = "default_user"
        persona = await storage.get_user_persona(user_id)
        
        # Enrich system prompt with persona context if available
        enriched_system_prompt = expert.systemPrompt
        if persona:
            # Build persona context with core business data
            persona_context = f"""

---
[CONTEXTO DO NEGÓCIO DO CLIENTE - Persona Intelligence Hub]:
• Empresa: {persona.companyName or 'Não especificado'}
• Indústria: {persona.industry or 'Não especificado'}
• Público-alvo: {persona.targetAudience or 'Não especificado'}
• Objetivo Principal: {persona.primaryGoal or 'Não especificado'}
• Desafio Principal: {persona.mainChallenge or 'Não especificado'}
"""
            
            # Add YouTube campaign insights if enriched
            if persona.campaignReferences and len(persona.campaignReferences) > 0:
                persona_context += "\n🎥 CAMPANHAS DE REFERÊNCIA (YouTube Research):\n"
                for i, campaign in enumerate(persona.campaignReferences[:5], 1):
                    # Defensive: handle both dict and Pydantic model access
                    if isinstance(campaign, dict):
                        title = campaign.get('title', 'N/A')
                        channel = campaign.get('channel', 'N/A')
                        insights = campaign.get('insights', [])
                    else:
                        title = getattr(campaign, 'title', 'N/A')
                        channel = getattr(campaign, 'channel', 'N/A')
                        insights = getattr(campaign, 'insights', [])
                    
                    persona_context += f"  {i}. \"{title}\" por {channel}\n"
                    if insights:
                        persona_context += f"     → Insights: {', '.join(insights[:2])}\n"
            
            # Add pain points and psychographics if available
            if persona.painPoints and len(persona.painPoints) > 0:
                persona_context += "\n💬 INSIGHTS DO PÚBLICO:\n"
                for i, pain_point in enumerate(persona.painPoints[:3], 1):
                    persona_context += f"  {i}. {pain_point}\n"
            
            persona_context += """
INSTRUÇÃO IMPORTANTE: Use essas informações para oferecer conselhos personalizados e estratégicos. NÃO mencione explicitamente "recebi informações da sua empresa" - simplesmente use o contexto naturalmente para enriquecer suas análises e recomendações com exemplos relevantes.
---
"""
            enriched_system_prompt = expert.systemPrompt + persona_context
        
        # Create agent for this expert with enriched system prompt
        agent = LegendAgentFactory.create_agent(
            expert_name=expert.name,
            system_prompt=enriched_system_prompt
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
        print(f"Error processing message: {str(e)}")
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
async def create_user_persona(data: UserPersonaCreate):
    """
    Create a new unified user persona with optional Reddit research.
    
    This endpoint creates a UserPersona combining:
    - Business context (from onboarding/form data)
    - Psychographic data (from Reddit research - optional)
    - Initial research mode configuration
    """
    print(f"[PERSONA CREATE] Endpoint called with data: {data}")
    user_id = "default_user"
    print(f"[PERSONA CREATE] Using user_id: {user_id}")
    try:
        print(f"[PERSONA CREATE] Calling storage.create_user_persona...")
        persona = await storage.create_user_persona(user_id, data)
        print(f"[PERSONA CREATE] Persona created successfully: {persona.id}")
        return persona
    except Exception as e:
        print(f"[PERSONA CREATE] Error creating persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")

@app.get("/api/persona/current", response_model=Optional[UserPersona])
async def get_current_persona():
    """
    Get the current user's persona.
    Returns the most recent persona for user_id="default_user".
    """
    user_id = "default_user"
    try:
        persona = await storage.get_user_persona(user_id)
        return persona
    except Exception as e:
        print(f"Error fetching persona: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch persona: {str(e)}")

async def _background_enrichment_task(persona_id: str, level: str):
    """
    Background task to enrich persona without blocking HTTP response.
    Updates enrichmentStatus as it progresses.
    """
    try:
        # Mark as processing
        await storage.update_user_persona(persona_id, {
            "enrichmentStatus": "processing"
        })
        print(f"[BACKGROUND] Starting {level} enrichment for persona {persona_id}...")
        
        from persona_enrichment import enrich_persona_with_deep_modules
        
        # Execute enrichment
        persona = await enrich_persona_with_deep_modules(
            persona_id=persona_id,
            level=level,
            storage=storage,
            existing_modules=None
        )
        
        # Mark as completed
        await storage.update_user_persona(persona_id, {
            "enrichmentStatus": "completed"
        })
        print(f"[BACKGROUND] ✅ Enrichment completed for persona {persona_id}")
        
    except Exception as e:
        # Mark as failed
        await storage.update_user_persona(persona_id, {
            "enrichmentStatus": "failed"
        })
        print(f"[BACKGROUND] ❌ Enrichment failed for persona {persona_id}: {str(e)}")
        import traceback
        traceback.print_exc()

@app.post("/api/persona/enrich/background", status_code=202)
async def enrich_persona_background(data: PersonaEnrichmentRequest):
    """
    Start persona enrichment in background without blocking.
    Returns immediately (202 Accepted) while enrichment runs asynchronously.
    
    User can check status via GET /api/persona/enrichment-status
    """
    import asyncio
    
    try:
        # Verify persona exists
        persona = await storage.get_user_persona_by_id(data.personaId)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        # Dispatch background task (fire and forget)
        asyncio.create_task(_background_enrichment_task(data.personaId, data.mode))
        
        return {
            "message": "Enrichment started in background",
            "personaId": data.personaId,
            "level": data.mode,
            "status": "processing"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting background enrichment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start enrichment: {str(e)}")

@app.get("/api/persona/enrichment-status")
async def get_enrichment_status():
    """
    Get current persona enrichment status.
    Returns: { status: 'pending' | 'processing' | 'completed' | 'failed' }
    """
    user_id = "default_user"
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
        print(f"Error fetching enrichment status: {str(e)}")
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
        print(f"Error enriching persona: {str(e)}")
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
        print(f"Error upgrading persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upgrade persona: {str(e)}")

@app.delete("/api/persona/{persona_id}", status_code=204)
async def delete_user_persona(persona_id: str):
    """
    Delete a user persona by ID.
    Returns 204 No Content on success.
    """
    try:
        deleted = await storage.delete_user_persona(persona_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Persona with id {persona_id} not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting persona: {str(e)}")
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
        print(f"Error listing personas: {str(e)}")
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
        print(f"Error setting active persona: {str(e)}")
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
        print(f"Error getting persona by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get persona: {str(e)}")

# Expert Recommendations endpoint (based on business profile)
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
        print(f"Error getting recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )

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
        print(f"Error generating suggested questions: {str(e)}")
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
        print(f"Error generating business insights: {str(e)}")
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
async def create_council_analysis(data: CouncilAnalysisCreate):
    """
    Run collaborative analysis by council of marketing legend experts.
    
    This endpoint:
    1. Conducts Perplexity research (if user has BusinessProfile)
    2. Gets independent analyses from 8 marketing legends
    3. Synthesizes consensus recommendation
    """
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    
    try:
        # Get user's business profile (optional)
        profile = await storage.get_business_profile(user_id)
        
        # Get experts to consult (all 8 if not specified)
        if data.expertIds:
            experts = []
            for expert_id in data.expertIds:
                expert = await storage.get_expert(expert_id)
                if not expert:
                    raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")
                experts.append(expert)
        else:
            # Use all available experts
            experts = await storage.get_experts()
            if not experts:
                raise HTTPException(status_code=400, detail="No experts available for analysis")
        
        # Run council analysis
        analysis = await council_orchestrator.analyze(
            problem=data.problem,
            experts=experts,
            profile=profile,
            user_id=user_id
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
        print(f"Error creating council analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create council analysis: {str(e)}")

@app.post("/api/council/analyze-stream")
async def create_council_analysis_stream(data: CouncilAnalysisCreate):
    """
    Run collaborative analysis with Server-Sent Events streaming.
    
    Emits real-time progress events:
    - expert_started: When expert begins analysis
    - expert_researching: During Perplexity research
    - expert_analyzing: During Claude analysis
    - expert_completed: When expert finishes
    - consensus_started: Before synthesis
    - analysis_complete: Final result with full analysis
    """
    user_id = "default_user"
    
    async def event_generator():
        # Helper to format SSE events (defined outside try block for exception handling)
        def sse_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        
        try:
            # Get user's business profile (optional)
            profile = await storage.get_business_profile(user_id)
            
            # Get experts to consult
            if data.expertIds:
                experts = []
                for expert_id in data.expertIds:
                    expert = await storage.get_expert(expert_id)
                    if not expert:
                        yield sse_event("error", {"message": f"Expert {expert_id} not found"})
                        return
                    experts.append(expert)
            else:
                experts = await storage.get_experts()
                if not experts:
                    yield sse_event("error", {"message": "No experts available"})
                    return
            
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
                        research_findings=research_findings
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
                expert = await storage.get_expert(expert_id)
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
    """Build rich context for follow-up including analysis + history + persona"""
    
    # Start with persona context if available (Persona Intelligence Hub)
    context = ""
    if persona:
        context += f"""**CONTEXTO DO NEGÓCIO DO CLIENTE (Persona Intelligence Hub):**
• Empresa: {persona.companyName or 'Não especificado'}
• Indústria: {persona.industry or 'Não especificado'}
• Público-alvo: {persona.targetAudience or 'Não especificado'}
• Objetivo Principal: {persona.primaryGoal or 'Não especificado'}
• Desafio Principal: {persona.mainChallenge or 'Não especificado'}
"""
        
        # Add enrichment data if available
        if persona.campaignReferences and len(persona.campaignReferences) > 0:
            context += "\n🎥 CAMPANHAS DE REFERÊNCIA (YouTube Research):\n"
            for i, campaign in enumerate(persona.campaignReferences[:3], 1):
                # Defensive: handle both dict and Pydantic model access
                if isinstance(campaign, dict):
                    title = campaign.get('title', 'N/A')
                    channel = campaign.get('channel', 'N/A')
                else:
                    title = getattr(campaign, 'title', 'N/A')
                    channel = getattr(campaign, 'channel', 'N/A')
                
                context += f"  {i}. \"{title}\" por {channel}\n"
        
        context += "\n**INSTRUÇÃO**: Use essas informações do cliente para personalizar suas análises.\n\n---\n\n"
    
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
        print(f"Error creating persona: {str(e)}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
