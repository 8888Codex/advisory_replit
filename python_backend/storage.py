from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from models import (
    Expert, ExpertCreate, Conversation, ConversationCreate, 
    Message, MessageCreate, ExpertType, CategoryType, BusinessProfile, BusinessProfileCreate,
    CouncilAnalysis, Persona, PersonaCreate, UserPersona, UserPersonaCreate
)
import os
import json
from datetime import datetime as dt
import asyncpg

def _parse_timestamp(value):
    """Parse timestamp from database - handles both datetime objects and ISO format strings"""
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value

class PostgresStorage:
    """
    PostgreSQL-backed storage for persistent data.
    Uses asyncpg connection pool for high-performance async operations.
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection pool"""
        if self._initialized:
            return
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable not set")
        
        self.pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        self._initialized = True
        print("[PostgresStorage] Connection pool initialized")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("[PostgresStorage] Connection pool closed")
    
    # Expert operations
    async def create_expert(self, data: ExpertCreate) -> Expert:
        """Create a new expert in PostgreSQL"""
        async with self.pool.acquire() as conn:
            expert_id = str(uuid.uuid4())
            category_value = data.category.value if hasattr(data.category, 'value') else str(data.category)
            
            row = await conn.fetchrow("""
                INSERT INTO experts (id, name, title, expertise, bio, avatar, system_prompt, category)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, name, title, expertise, bio, avatar, system_prompt as "systemPrompt", category, created_at as "createdAt"
            """, expert_id, data.name, data.title, data.expertise, data.bio, 
                 data.avatar, data.systemPrompt, category_value)
            
            return Expert(
                id=row['id'],
                name=row['name'],
                title=row['title'],
                expertise=row['expertise'],
                bio=row['bio'],
                avatar=row['avatar'],
                systemPrompt=row['systemPrompt'],
                expertType=data.expertType,
                category=CategoryType(row['category']),
                createdAt=row['createdAt']
            )
    
    async def get_expert(self, expert_id: str) -> Optional[Expert]:
        """Get expert by ID from PostgreSQL"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, title, expertise, bio, avatar, 
                       system_prompt as "systemPrompt", category, created_at as "createdAt"
                FROM experts WHERE id = $1
            """, expert_id)
            
            if not row:
                return None
            
            return Expert(
                id=row['id'],
                name=row['name'],
                title=row['title'],
                expertise=row['expertise'],
                bio=row['bio'],
                avatar=row['avatar'],
                systemPrompt=row['systemPrompt'],
                expertType=ExpertType.CUSTOM,  # Assume custom if in DB
                category=CategoryType(row['category']),
                createdAt=row['createdAt']
            )
    
    async def get_expert_by_name(self, name: str) -> Optional[Expert]:
        """Get expert by name from PostgreSQL (for idempotent seeding)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, title, expertise, bio, avatar, 
                       system_prompt as "systemPrompt", category, created_at as "createdAt"
                FROM experts WHERE name = $1
            """, name)
            
            if not row:
                return None
            
            return Expert(
                id=row['id'],
                name=row['name'],
                title=row['title'],
                expertise=row['expertise'],
                bio=row['bio'],
                avatar=row['avatar'],
                systemPrompt=row['systemPrompt'],
                expertType=ExpertType.CUSTOM,
                category=CategoryType(row['category']),
                createdAt=row['createdAt']
            )
    
    async def get_experts(self) -> List[Expert]:
        """Get all experts from PostgreSQL"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, title, expertise, bio, avatar,
                       system_prompt as "systemPrompt", category, created_at as "createdAt"
                FROM experts
                ORDER BY created_at DESC
            """)
            
            return [
                Expert(
                    id=row['id'],
                    name=row['name'],
                    title=row['title'],
                    expertise=row['expertise'],
                    bio=row['bio'],
                    avatar=row['avatar'],
                    systemPrompt=row['systemPrompt'],
                    expertType=ExpertType.CUSTOM,
                    category=CategoryType(row['category']),
                    createdAt=row['createdAt']
                )
                for row in rows
            ]
    
    async def update_expert_avatar(self, expert_id: str, avatar_path: str) -> Optional[Expert]:
        """Update expert's avatar path"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE experts SET avatar = $1
                WHERE id = $2
                RETURNING id, name, title, expertise, bio, avatar,
                          system_prompt as "systemPrompt", category, created_at as "createdAt"
            """, avatar_path, expert_id)
            
            if not row:
                return None
            
            return Expert(
                id=row['id'],
                name=row['name'],
                title=row['title'],
                expertise=row['expertise'],
                bio=row['bio'],
                avatar=row['avatar'],
                systemPrompt=row['systemPrompt'],
                expertType=ExpertType.CUSTOM,
                category=CategoryType(row['category']),
                createdAt=row['createdAt']
            )
    
    # Conversation operations
    async def create_conversation(self, data: ConversationCreate) -> Conversation:
        """Create a new conversation in PostgreSQL"""
        async with self.pool.acquire() as conn:
            conversation_id = str(uuid.uuid4())
            
            row = await conn.fetchrow("""
                INSERT INTO conversations (id, expert_id, title)
                VALUES ($1, $2, $3)
                RETURNING id, expert_id as "expertId", title, created_at as "createdAt", updated_at as "updatedAt"
            """, conversation_id, data.expertId, data.title)
            
            return Conversation(
                id=row['id'],
                expertId=row['expertId'],
                title=row['title'],
                createdAt=row['createdAt'],
                updatedAt=row['updatedAt']
            )
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID from PostgreSQL"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, expert_id as "expertId", title, created_at as "createdAt", updated_at as "updatedAt"
                FROM conversations WHERE id = $1
            """, conversation_id)
            
            if not row:
                return None
            
            return Conversation(
                id=row['id'],
                expertId=row['expertId'],
                title=row['title'],
                createdAt=row['createdAt'],
                updatedAt=row['updatedAt']
            )
    
    async def get_conversations(self, expert_id: Optional[str] = None) -> List[Conversation]:
        """Get all conversations, optionally filtered by expert_id"""
        async with self.pool.acquire() as conn:
            if expert_id:
                rows = await conn.fetch("""
                    SELECT id, expert_id as "expertId", title, created_at as "createdAt", updated_at as "updatedAt"
                    FROM conversations WHERE expert_id = $1
                    ORDER BY updated_at DESC
                """, expert_id)
            else:
                rows = await conn.fetch("""
                    SELECT id, expert_id as "expertId", title, created_at as "createdAt", updated_at as "updatedAt"
                    FROM conversations
                    ORDER BY updated_at DESC
                """)
            
            return [
                Conversation(
                    id=row['id'],
                    expertId=row['expertId'],
                    title=row['title'],
                    createdAt=row['createdAt'],
                    updatedAt=row['updatedAt']
                )
                for row in rows
            ]
    
    async def update_conversation_timestamp(self, conversation_id: str):
        """Update conversation's updated_at timestamp"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE conversations SET updated_at = NOW()
                WHERE id = $1
            """, conversation_id)
    
    # Message operations
    async def create_message(self, data: MessageCreate) -> Message:
        """Create a new message in PostgreSQL"""
        async with self.pool.acquire() as conn:
            message_id = str(uuid.uuid4())
            
            row = await conn.fetchrow("""
                INSERT INTO messages (id, conversation_id, role, content)
                VALUES ($1, $2, $3, $4)
                RETURNING id, conversation_id as "conversationId", role, content, created_at as "createdAt"
            """, message_id, data.conversationId, data.role, data.content)
            
            # Update conversation timestamp
            await self.update_conversation_timestamp(data.conversationId)
            
            return Message(
                id=row['id'],
                conversationId=row['conversationId'],
                role=row['role'],
                content=row['content'],
                createdAt=row['createdAt']
            )
    
    async def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, conversation_id as "conversationId", role, content, created_at as "createdAt"
                FROM messages WHERE conversation_id = $1
                ORDER BY created_at ASC
            """, conversation_id)
            
            return [
                Message(
                    id=row['id'],
                    conversationId=row['conversationId'],
                    role=row['role'],
                    content=row['content'],
                    createdAt=row['createdAt']
                )
                for row in rows
            ]
    
    # Business Profile operations (keep using in-memory for now - can migrate later)
    async def save_business_profile(self, user_id: str, data: BusinessProfileCreate) -> BusinessProfile:
        """Create or update business profile - TODO: migrate to PostgreSQL"""
        # For now, keep this as a placeholder that returns a simple profile
        # We'll implement full PostgreSQL storage in a follow-up task
        profile_id = str(uuid.uuid4())
        return BusinessProfile(
            id=profile_id,
            userId=user_id,
            companyName=data.companyName,
            industry=data.industry,
            companySize=data.companySize,
            targetAudience=data.targetAudience,
            mainProducts=data.mainProducts,
            channels=data.channels,
            budgetRange=data.budgetRange,
            primaryGoal=data.primaryGoal,
            mainChallenge=data.mainChallenge,
            timeline=data.timeline,
            createdAt=datetime.utcnow().isoformat(),
            updatedAt=datetime.utcnow().isoformat()
        )
    
    async def get_business_profile(self, user_id: str) -> Optional[BusinessProfile]:
        """Get business profile - TODO: migrate to PostgreSQL"""
        return None  # Temporary implementation
    
    # Council Analysis operations (stubbed - TODO: implement full PostgreSQL support)
    async def save_council_analysis(self, analysis: CouncilAnalysis) -> CouncilAnalysis:
        """Save council analysis - stub for now"""
        return analysis
    
    async def get_council_analysis(self, analysis_id: str) -> Optional[CouncilAnalysis]:
        """Get council analysis - stub for now"""
        return None
    
    async def get_council_analyses(self, user_id: str) -> List[CouncilAnalysis]:
        """Get council analyses for user - stub for now"""
        return []
    
    # Council Messages (PostgreSQL implementation)
    async def get_council_messages(self, session_id: str) -> List:
        """Get council messages for a session"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, session_id as "sessionId", role, content, contributions, created_at as "createdAt"
                FROM council_messages
                WHERE session_id = $1
                ORDER BY created_at ASC
            """, session_id)
            
            return [dict(row) for row in rows]
    
    async def create_council_message(
        self,
        session_id: str,
        role: str,
        content: str,
        contributions: Optional[str] = None
    ):
        """Create a new council message"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            message_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO council_messages (id, session_id, role, content, contributions)
                VALUES ($1, $2, $3, $4, $5)
            """, message_id, session_id, role, content, contributions)
            
            return {"id": message_id, "session_id": session_id, "role": role, "content": content}
    
    # Persona operations (stubbed - TODO: implement)
    async def create_persona(self, user_id: str, persona_data: dict) -> Persona:
        """Create persona - stub for now"""
        raise NotImplementedError("Persona operations not yet migrated to PostgreSQL")
    
    async def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get persona - stub for now"""
        return None
    
    async def get_personas(self, user_id: str) -> List[Persona]:
        """Get personas - stub for now"""
        return []
    
    async def update_persona(self, persona_id: str, updates: dict) -> Optional[Persona]:
        """Update persona - stub for now"""
        return None
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete persona - stub for now"""
        return False
    
    # User Persona operations removed - using unified implementation starting at line ~1400
    
    async def update_user_persona_legacy(self, persona_id: str, updates: dict) -> UserPersona:
        """Update user persona"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            # Build update query dynamically based on provided fields
            set_clauses = []
            params = [persona_id]
            param_count = 2
            
            for key, value in updates.items():
                if key in ['demographics', 'psychographics', 'painPoints', 'goals', 'values', 
                          'contentPreferences', 'communities', 'behavioralPatterns', 'researchData']:
                    # JSON fields - need to serialize
                    snake_key = ''.join(['_'+c.lower() if c.isupper() else c for c in key]).lstrip('_')
                    set_clauses.append(f"{snake_key} = ${param_count}")
                    params.append(json.dumps(value))
                    param_count += 1
                elif key in ['name', 'researchMode']:
                    snake_key = ''.join(['_'+c.lower() if c.isupper() else c for c in key]).lstrip('_')
                    set_clauses.append(f"{snake_key} = ${param_count}")
                    params.append(value)
                    param_count += 1
            
            if not set_clauses:
                # No updates provided, just return current persona
                return await self.get_user_persona_by_id(persona_id)
            
            query = f"""
                UPDATE user_personas 
                SET {', '.join(set_clauses)}, updated_at = NOW()
                WHERE id = $1
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *params)
            
            if not row:
                raise ValueError(f"Persona {persona_id} not found")
            
            return UserPersona(
                id=row['id'],
                userId=row['user_id'],
                name=row['name'],
                researchMode=row['research_mode'],
                demographics=json.loads(row['demographics']) if row['demographics'] else {},
                psychographics=json.loads(row['psychographics']) if row['psychographics'] else {},
                painPoints=json.loads(row['pain_points']) if row['pain_points'] else [],
                goals=json.loads(row['goals']) if row['goals'] else [],
                values=json.loads(row['values']) if row['values'] else [],
                contentPreferences=json.loads(row['content_preferences']) if row['content_preferences'] else {},
                communities=json.loads(row['communities']) if row['communities'] else [],
                behavioralPatterns=json.loads(row['behavioral_patterns']) if row['behavioral_patterns'] else {},
                researchData=json.loads(row['research_data']) if row['research_data'] else {},
                createdAt=row['created_at'],
                updatedAt=row['updated_at']
            )
    
    async def enrich_persona_youtube(self, persona_id: str, youtube_data: dict) -> UserPersona:
        """Enrich persona with YouTube data"""
        return await self.update_user_persona(persona_id, {"researchData": youtube_data})
    
    async def delete_user_persona(self, persona_id: str) -> bool:
        """Delete user persona"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM user_personas WHERE id = $1
            """, persona_id)
            
            return result == "DELETE 1"
    
    # ============================================
    # USER AUTHENTICATION METHODS
    # ============================================
    
    async def create_user(self, username: str, email: str, password_hash: str) -> dict:
        """Create a new user with username, email, and hashed password"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            user_id = str(uuid.uuid4())
            
            row = await conn.fetchrow("""
                INSERT INTO users (id, username, email, password, available_invites)
                VALUES ($1, $2, $3, $4, 5)
                RETURNING id, username, email, available_invites as "availableInvites", created_at as "createdAt"
            """, user_id, username, email, password_hash)
            
            return {
                "id": row['id'],
                "username": row['username'],
                "email": row['email'],
                "availableInvites": row['availableInvites'],
                "createdAt": row['createdAt']
            }
    
    # ============================================
    # USER PERSONA OPERATIONS (PostgreSQL)
    # ============================================
    
    async def create_user_persona(self, user_id: str, data: UserPersonaCreate) -> UserPersona:
        """Create or replace user persona (UPSERT logic to handle unique constraint on user_id)"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            persona_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            row = await conn.fetchrow(
                """
                INSERT INTO user_personas (
                    id, user_id,
                    company_name, industry, company_size, target_audience,
                    main_products, channels, budget_range, primary_goal,
                    main_challenge, timeline,
                    demographics, psychographics, pain_points, goals, values,
                    communities, behavioral_patterns, content_preferences,
                    youtube_research, video_insights, campaign_references, inspiration_videos,
                    research_mode, enrichment_level, enrichment_status, research_completeness, last_enriched_at,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    industry = EXCLUDED.industry,
                    company_size = EXCLUDED.company_size,
                    target_audience = EXCLUDED.target_audience,
                    main_products = EXCLUDED.main_products,
                    channels = EXCLUDED.channels,
                    budget_range = EXCLUDED.budget_range,
                    primary_goal = EXCLUDED.primary_goal,
                    main_challenge = EXCLUDED.main_challenge,
                    timeline = EXCLUDED.timeline,
                    research_mode = EXCLUDED.research_mode,
                    enrichment_level = EXCLUDED.enrichment_level,
                    enrichment_status = EXCLUDED.enrichment_status,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                persona_id, user_id,
                data.companyName, data.industry, data.companySize, data.targetAudience,
                data.mainProducts, data.channels, data.budgetRange, data.primaryGoal,
                data.mainChallenge, data.timeline,
                json.dumps({}), json.dumps({}), [], [], [],
                [], json.dumps({}), json.dumps({}),
                json.dumps([]), [], json.dumps([]), json.dumps([]),
                data.researchMode, data.enrichmentLevel or data.researchMode, "pending", 0, None,
                now, now
            )
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
    
    async def get_user_persona(self, user_id: str) -> Optional[UserPersona]:
        """Get the user persona for a specific user"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_personas WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
                user_id
            )
            if not row:
                return None
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
    
    async def get_user_persona_by_id(self, persona_id: str) -> Optional[UserPersona]:
        """Get a specific user persona by ID"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_personas WHERE id = $1",
                persona_id
            )
            if not row:
                return None
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
    
    async def update_user_persona(self, persona_id: str, updates: dict) -> UserPersona:
        """Update a user persona with partial updates"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            now = datetime.utcnow()
            
            set_clauses = ["updated_at = $1"]
            params: List[Any] = [now]
            param_num = 2
            
            field_mapping = {
                "companyName": "company_name",
                "industry": "industry",
                "companySize": "company_size",
                "targetAudience": "target_audience",
                "mainProducts": "main_products",
                "channels": "channels",
                "budgetRange": "budget_range",
                "primaryGoal": "primary_goal",
                "mainChallenge": "main_challenge",
                "timeline": "timeline",
                "demographics": "demographics",
                "psychographics": "psychographics",
                "painPoints": "pain_points",
                "goals": "goals",
                "values": "values",
                "communities": "communities",
                "behavioralPatterns": "behavioral_patterns",
                "contentPreferences": "content_preferences",
                "youtubeResearch": "youtube_research",
                "videoInsights": "video_insights",
                "campaignReferences": "campaign_references",
                "inspirationVideos": "inspiration_videos",
                "researchMode": "research_mode",
                "enrichmentLevel": "enrichment_level",
                "enrichmentStatus": "enrichment_status",
                "researchCompleteness": "research_completeness",
                "lastEnrichedAt": "last_enriched_at",
                # 8-Module Deep Persona System
                "psychographicCore": "psychographic_core",
                "buyerJourney": "buyer_journey",
                "behavioralProfile": "behavioral_profile",
                "languageCommunication": "language_communication",
                "strategicInsights": "strategic_insights",
                "jobsToBeDone": "jobs_to_be_done",
                "decisionProfile": "decision_profile",
                "copyExamples": "copy_examples"
            }
            
            json_fields = [
                "demographics", "psychographics", "behavioral_patterns", 
                "content_preferences", "youtube_research", "campaign_references", 
                "inspiration_videos",
                # 8-Module Deep Persona System (all JSON)
                "psychographic_core", "buyer_journey", "behavioral_profile",
                "language_communication", "strategic_insights", "jobs_to_be_done",
                "decision_profile", "copy_examples"
            ]
            
            for field_camel, field_snake in field_mapping.items():
                if field_camel in updates:
                    value = updates[field_camel]
                    if field_snake in json_fields:
                        value = json.dumps(value)
                    
                    set_clauses.append(f"{field_snake} = ${param_num}")
                    params.append(value)
                    param_num += 1
            
            params.append(persona_id)
            query = f"UPDATE user_personas SET {', '.join(set_clauses)} WHERE id = ${param_num} RETURNING *"
            
            row = await conn.fetchrow(query, *params)
            if not row:
                raise ValueError(f"UserPersona with id {persona_id} not found")
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
    
    async def enrich_persona_youtube(self, persona_id: str, youtube_data: dict) -> UserPersona:
        """Enrich persona with YouTube research data"""
        now = datetime.utcnow()
        
        updates = {
            "youtubeResearch": youtube_data.get("youtubeResearch", []),
            "videoInsights": youtube_data.get("videoInsights", []),
            "campaignReferences": youtube_data.get("campaignReferences", []),
            "inspirationVideos": youtube_data.get("inspirationVideos", []),
            "researchCompleteness": youtube_data.get("researchCompleteness", 50),
            "lastEnrichedAt": now
        }
        
        return await self.update_user_persona(persona_id, updates)
    
    async def delete_user_persona(self, persona_id: str) -> bool:
        """Delete a user persona"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM user_personas WHERE id = $1", persona_id)
            return result == "DELETE 1"
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email address"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, username, email, password, role, available_invites as "availableInvites", created_at as "createdAt"
                FROM users
                WHERE email = $1
            """, email)
            
            if not row:
                return None
            
            return {
                "id": row['id'],
                "username": row['username'],
                "email": row['email'],
                "password": row['password'],
                "role": row['role'],
                "availableInvites": row['availableInvites'],
                "createdAt": row['createdAt']
            }
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, username, email, password, role, available_invites as "availableInvites", created_at as "createdAt"
                FROM users
                WHERE id = $1
            """, user_id)
            
            if not row:
                return None
            
            return {
                "id": row['id'],
                "username": row['username'],
                "email": row['email'],
                "password": row['password'],
                "role": row['role'],
                "availableInvites": row['availableInvites'],
                "createdAt": row['createdAt']
            }
    
    async def update_user_invites(self, user_id: str, new_count: int) -> bool:
        """Update user's available invite count"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE users
                SET available_invites = $1
                WHERE id = $2
            """, new_count, user_id)
            
            return result == "UPDATE 1"
    
    # ============================================
    # INVITE CODE METHODS
    # ============================================
    
    async def create_invite(self, code: str, creator_id: str) -> dict:
        """Create a new invite code"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            invite_id = str(uuid.uuid4())
            
            row = await conn.fetchrow("""
                INSERT INTO invite_codes (id, code, creator_id)
                VALUES ($1, $2, $3)
                RETURNING id, code, creator_id as "creatorId", used_by as "usedBy", 
                          used_at as "usedAt", created_at as "createdAt"
            """, invite_id, code, creator_id)
            
            return {
                "id": row['id'],
                "code": row['code'],
                "creatorId": row['creatorId'],
                "usedBy": row['usedBy'],
                "usedAt": row['usedAt'],
                "createdAt": row['createdAt']
            }
    
    async def get_invite(self, code: str) -> Optional[dict]:
        """Get invite code by code string"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, code, creator_id as "creatorId", used_by as "usedBy",
                       used_at as "usedAt", created_at as "createdAt"
                FROM invite_codes
                WHERE code = $1
            """, code)
            
            if not row:
                return None
            
            return {
                "id": row['id'],
                "code": row['code'],
                "creatorId": row['creatorId'],
                "usedBy": row['usedBy'],
                "usedAt": row['usedAt'],
                "createdAt": row['createdAt']
            }
    
    async def use_invite(self, code: str, used_by: str) -> bool:
        """Mark invite code as used"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE invite_codes
                SET used_by = $1, used_at = NOW()
                WHERE code = $2 AND used_by IS NULL
            """, used_by, code)
            
            return result == "UPDATE 1"
    
    async def get_user_invites(self, creator_id: str) -> List[dict]:
        """Get all invite codes created by a user"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, code, creator_id as "creatorId", used_by as "usedBy",
                       used_at as "usedAt", created_at as "createdAt"
                FROM invite_codes
                WHERE creator_id = $1
                ORDER BY created_at DESC
            """, creator_id)
            
            return [
                {
                    "id": row['id'],
                    "code": row['code'],
                    "creatorId": row['creatorId'],
                    "usedBy": row['usedBy'],
                    "usedAt": row['usedAt'],
                    "createdAt": row['createdAt']
                }
                for row in rows
            ]
    
    # ============================================
    # ONBOARDING METHODS
    # ============================================
    
    async def save_onboarding_progress(self, user_id: str, data: dict) -> dict:
        """Save or update onboarding progress for a user"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            # Check if onboarding record exists
            existing = await conn.fetchrow("""
                SELECT id FROM onboarding_status WHERE user_id = $1
            """, user_id)
            
            if existing:
                # Update existing record
                row = await conn.fetchrow("""
                    UPDATE onboarding_status
                    SET current_step = COALESCE($2, current_step),
                        company_name = COALESCE($3, company_name),
                        industry = COALESCE($4, industry),
                        company_size = COALESCE($5, company_size),
                        target_audience = COALESCE($6, target_audience),
                        goals = COALESCE($7, goals),
                        main_challenge = COALESCE($8, main_challenge),
                        enrichment_level = COALESCE($9, enrichment_level),
                        updated_at = NOW()
                    WHERE user_id = $1
                    RETURNING id, user_id as "userId", current_step as "currentStep",
                              company_name as "companyName", industry, company_size as "companySize",
                              target_audience as "targetAudience", goals, main_challenge as "mainChallenge",
                              enrichment_level as "enrichmentLevel", completed_at as "completedAt",
                              created_at as "createdAt", updated_at as "updatedAt"
                """, user_id, data.get('currentStep'), data.get('companyName'), 
                     data.get('industry'), data.get('companySize'), data.get('targetAudience'),
                     data.get('goals'), data.get('mainChallenge'), data.get('enrichmentLevel'))
            else:
                # Create new record
                onboarding_id = str(uuid.uuid4())
                row = await conn.fetchrow("""
                    INSERT INTO onboarding_status (
                        id, user_id, current_step, company_name, industry, company_size,
                        target_audience, goals, main_challenge, enrichment_level
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id, user_id as "userId", current_step as "currentStep",
                              company_name as "companyName", industry, company_size as "companySize",
                              target_audience as "targetAudience", goals, main_challenge as "mainChallenge",
                              enrichment_level as "enrichmentLevel", completed_at as "completedAt",
                              created_at as "createdAt", updated_at as "updatedAt"
                """, onboarding_id, user_id, data.get('currentStep', 0), 
                     data.get('companyName'), data.get('industry'), data.get('companySize'),
                     data.get('targetAudience'), data.get('goals'), data.get('mainChallenge'),
                     data.get('enrichmentLevel'))
            
            return {
                "id": row['id'],
                "userId": row['userId'],
                "currentStep": row['currentStep'],
                "companyName": row['companyName'],
                "industry": row['industry'],
                "companySize": row['companySize'],
                "targetAudience": row['targetAudience'],
                "goals": row['goals'],
                "mainChallenge": row['mainChallenge'],
                "enrichmentLevel": row['enrichmentLevel'],
                "completedAt": row['completedAt'],
                "createdAt": row['createdAt'],
                "updatedAt": row['updatedAt']
            }
    
    async def get_onboarding_status(self, user_id: str) -> Optional[dict]:
        """Get onboarding status for a user"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, user_id as "userId", current_step as "currentStep",
                       company_name as "companyName", industry, company_size as "companySize",
                       target_audience as "targetAudience", goals, main_challenge as "mainChallenge",
                       enrichment_level as "enrichmentLevel", completed_at as "completedAt",
                       created_at as "createdAt", updated_at as "updatedAt"
                FROM onboarding_status
                WHERE user_id = $1
            """, user_id)
            
            if not row:
                return None
            
            return {
                "id": row['id'],
                "userId": row['userId'],
                "currentStep": row['currentStep'],
                "companyName": row['companyName'],
                "industry": row['industry'],
                "companySize": row['companySize'],
                "targetAudience": row['targetAudience'],
                "goals": row['goals'],
                "mainChallenge": row['mainChallenge'],
                "enrichmentLevel": row['enrichmentLevel'],
                "completedAt": row['completedAt'],
                "createdAt": row['createdAt'],
                "updatedAt": row['updatedAt']
            }
    
    async def complete_onboarding(self, user_id: str) -> bool:
        """Mark onboarding as completed"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE onboarding_status
                SET completed_at = NOW(), updated_at = NOW()
                WHERE user_id = $1 AND completed_at IS NULL
            """, user_id)
            
            return result == "UPDATE 1"
    
    # ============================================
    # PASSWORD RESET OPERATIONS
    # ============================================
    
    async def create_password_reset_token(self, user_id: str, hashed_token: str, expires_at: datetime) -> str:
        """Create a password reset token"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            token_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO password_reset_tokens (id, user_id, hashed_token, expires_at)
                VALUES ($1, $2, $3, $4)
            """, token_id, user_id, hashed_token, expires_at)
            
            return token_id
    
    async def get_password_reset_token(self, hashed_token: str) -> Optional[dict]:
        """Get password reset token by hashed token"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, user_id as "userId", hashed_token as "hashedToken",
                       expires_at as "expiresAt", used_at as "usedAt", created_at as "createdAt"
                FROM password_reset_tokens
                WHERE hashed_token = $1
            """, hashed_token)
            
            if not row:
                return None
            
            return {
                "id": row['id'],
                "userId": row['userId'],
                "hashedToken": row['hashedToken'],
                "expiresAt": row['expiresAt'],
                "usedAt": row['usedAt'],
                "createdAt": row['createdAt']
            }
    
    async def mark_token_as_used(self, hashed_token: str) -> bool:
        """Mark a password reset token as used"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE password_reset_tokens
                SET used_at = NOW()
                WHERE hashed_token = $1 AND used_at IS NULL
            """, hashed_token)
            
            return result == "UPDATE 1"
    
    async def update_user_password(self, user_id: str, hashed_password: str) -> bool:
        """Update user password"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE users
                SET password = $1
                WHERE id = $2
            """, hashed_password, user_id)
            
            return result == "UPDATE 1"
    
    # ============================================
    # AUDIT LOGGING OPERATIONS
    # ============================================
    
    async def create_audit_log(
        self,
        action: str,
        success: bool,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Create an audit log entry"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        async with self.pool.acquire() as conn:
            log_id = str(uuid.uuid4())
            
            # Append success/failure to action name
            full_action = f"{action}_{'success' if success else 'failure'}"
            
            # Include user_agent and success in metadata
            full_metadata = metadata.copy() if metadata else {}
            full_metadata['success'] = success
            if user_agent:
                full_metadata['user_agent'] = user_agent
            
            # Insert into audit_logs table (not login_audit)
            # Convert metadata dict to JSON string for asyncpg
            metadata_json = json.dumps(full_metadata)
            await conn.execute("""
                INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, metadata, ip_address)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, log_id, user_id, full_action, "auth", None, metadata_json, ip_address)
            
            return log_id
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get audit logs with optional filters"""
        if not self.pool:
            raise RuntimeError("PostgresStorage not initialized")
        
        # Build dynamic query with filters
        conditions = []
        params = []
        param_count = 1
        
        if user_id:
            conditions.append(f"user_id = ${param_count}")
            params.append(user_id)
            param_count += 1
        
        if action:
            conditions.append(f"action = ${param_count}")
            params.append(action)
            param_count += 1
        
        if success is not None:
            success_str = "true" if success else "false"
            conditions.append(f"success = ${param_count}")
            params.append(success_str)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Add limit and offset
        params.append(limit)
        params.append(offset)
        
        query = f"""
            SELECT id, user_id as "userId", action, success, ip_address as "ipAddress",
                   user_agent as "userAgent", metadata, timestamp
            FROM login_audit
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return [
                {
                    "id": row['id'],
                    "userId": row['userId'],
                    "action": row['action'],
                    "success": row['success'] == "true",
                    "ipAddress": row['ipAddress'],
                    "userAgent": row['userAgent'],
                    "metadata": row['metadata'],
                    "timestamp": row['timestamp']
                }
                for row in rows
            ]
    
    async def list_user_personas(self, user_id: str) -> List[UserPersona]:
        """Get all personas for a specific user"""
        def safe_json_parse(value, default):
            """Safely parse JSON - handles both strings and already-parsed objects from asyncpg"""
            if value is None:
                return default
            if isinstance(value, (dict, list)):
                return value  # Already parsed by asyncpg for JSONB columns
            if isinstance(value, str):
                return json.loads(value)
            return default
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM user_personas 
                WHERE user_id = $1 
                ORDER BY created_at DESC
            """, user_id)
            
            personas = []
            for row in rows:
                personas.append(UserPersona(
                    id=row["id"],
                    userId=row["user_id"],
                    companyName=row["company_name"],
                    industry=row["industry"],
                    companySize=row["company_size"],
                    targetAudience=row["target_audience"],
                    mainProducts=row.get("main_products"),
                    channels=safe_json_parse(row.get("channels"), []),
                    budgetRange=row.get("budget_range"),
                    primaryGoal=row["primary_goal"],
                    mainChallenge=row["main_challenge"],
                    timeline=row.get("timeline"),
                    demographics=safe_json_parse(row.get("demographics"), {}),
                    psychographics=safe_json_parse(row.get("psychographics"), {}),
                    painPoints=safe_json_parse(row.get("pain_points"), []),
                    goals=safe_json_parse(row.get("goals"), []),
                    values=safe_json_parse(row.get("values"), []),
                    communities=safe_json_parse(row.get("communities"), []),
                    behavioralPatterns=safe_json_parse(row.get("behavioral_patterns"), {}),
                    contentPreferences=safe_json_parse(row.get("content_preferences"), {}),
                    youtubeResearch=safe_json_parse(row.get("youtube_research"), []),
                    videoInsights=safe_json_parse(row.get("video_insights"), []),
                    campaignReferences=safe_json_parse(row.get("campaign_references"), []),
                    inspirationVideos=safe_json_parse(row.get("inspiration_videos"), []),
                    researchMode=row.get("research_mode", "strategic"),
                    enrichmentLevel=row.get("enrichment_level"),
                    enrichmentStatus=row.get("enrichment_status", "pending"),
                    researchCompleteness=row["research_completeness"],
                    lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                    psychographicCore=safe_json_parse(row.get("psychographic_core"), None),
                    buyerJourney=safe_json_parse(row.get("buyer_journey"), None),
                    behavioralProfile=safe_json_parse(row.get("behavioral_profile"), None),
                    languageCommunication=safe_json_parse(row.get("language_communication"), None),
                    strategicInsights=safe_json_parse(row.get("strategic_insights"), None),
                    jobsToBeDone=safe_json_parse(row.get("jobs_to_be_done"), None),
                    decisionProfile=safe_json_parse(row.get("decision_profile"), None),
                    copyExamples=safe_json_parse(row.get("copy_examples"), None),
                    createdAt=_parse_timestamp(row["created_at"]),
                    updatedAt=_parse_timestamp(row["updated_at"])
                ))
            return personas
    
    async def set_active_persona(self, user_id: str, persona_id: str) -> bool:
        """Set a persona as the active one for a user"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE users 
                SET active_persona_id = $1 
                WHERE id = $2
            """, persona_id, user_id)
            return result == "UPDATE 1"

class MemStorage:
    """In-memory storage compatible with frontend API expectations"""
    
    def __init__(self):
        self.experts: Dict[str, Expert] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.messages: Dict[str, Message] = {}
        self.profiles: Dict[str, BusinessProfile] = {}  # userId -> BusinessProfile
        self.council_analyses: Dict[str, CouncilAnalysis] = {}  # analysisId -> CouncilAnalysis
    
    # Expert operations
    async def create_expert(self, data: ExpertCreate) -> Expert:
        expert_id = str(uuid.uuid4())
        expert = Expert(
            id=expert_id,
            name=data.name,
            title=data.title,
            bio=data.bio,
            expertise=data.expertise,
            systemPrompt=data.systemPrompt,
            avatar=data.avatar,
            expertType=data.expertType,
            category=data.category,
        )
        self.experts[expert_id] = expert
        return expert
    
    async def get_expert(self, expert_id: str) -> Optional[Expert]:
        return self.experts.get(expert_id)
    
    async def get_experts(self) -> List[Expert]:
        return list(self.experts.values())
    
    async def update_expert_avatar(self, expert_id: str, avatar_path: str) -> Optional[Expert]:
        """Update expert's avatar path"""
        expert = self.experts.get(expert_id)
        if expert:
            expert.avatar = avatar_path
            return expert
        return None
    
    # Conversation operations
    async def create_conversation(self, data: ConversationCreate) -> Conversation:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            expertId=data.expertId,
            title=data.title,
        )
        self.conversations[conversation_id] = conversation
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.conversations.get(conversation_id)
    
    async def get_conversations(self, expert_id: Optional[str] = None) -> List[Conversation]:
        conversations = list(self.conversations.values())
        if expert_id:
            conversations = [c for c in conversations if c.expertId == expert_id]
        # Sort by updatedAt descending
        conversations.sort(key=lambda x: x.updatedAt, reverse=True)
        return conversations
    
    async def update_conversation_timestamp(self, conversation_id: str):
        if conversation_id in self.conversations:
            self.conversations[conversation_id].updatedAt = datetime.utcnow()
    
    # Message operations
    async def create_message(self, data: MessageCreate) -> Message:
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            conversationId=data.conversationId,
            role=data.role,
            content=data.content,
        )
        self.messages[message_id] = message
        
        # Update conversation timestamp
        await self.update_conversation_timestamp(data.conversationId)
        
        return message
    
    async def get_messages(self, conversation_id: str) -> List[Message]:
        messages = [m for m in self.messages.values() if m.conversationId == conversation_id]
        # Sort by createdAt ascending (chronological order)
        messages.sort(key=lambda x: x.createdAt)
        return messages
    
    # Business Profile operations
    async def save_business_profile(self, user_id: str, data: BusinessProfileCreate) -> BusinessProfile:
        """Create or update business profile for a user"""
        existing_profile = self.profiles.get(user_id)
        
        if existing_profile:
            # Update existing profile
            profile = BusinessProfile(
                id=existing_profile.id,
                userId=user_id,
                companyName=data.companyName,
                industry=data.industry,
                companySize=data.companySize,
                targetAudience=data.targetAudience,
                mainProducts=data.mainProducts,
                channels=data.channels,
                budgetRange=data.budgetRange,
                primaryGoal=data.primaryGoal,
                mainChallenge=data.mainChallenge,
                timeline=data.timeline,
                createdAt=existing_profile.createdAt,
                updatedAt=datetime.utcnow()
            )
        else:
            # Create new profile
            profile_id = str(uuid.uuid4())
            profile = BusinessProfile(
                id=profile_id,
                userId=user_id,
                companyName=data.companyName,
                industry=data.industry,
                companySize=data.companySize,
                targetAudience=data.targetAudience,
                mainProducts=data.mainProducts,
                channels=data.channels,
                budgetRange=data.budgetRange,
                primaryGoal=data.primaryGoal,
                mainChallenge=data.mainChallenge,
                timeline=data.timeline
            )
        
        self.profiles[user_id] = profile
        return profile
    
    async def get_business_profile(self, user_id: str) -> Optional[BusinessProfile]:
        """Get business profile for a user"""
        return self.profiles.get(user_id)
    
    # Council Analysis operations
    async def save_council_analysis(self, analysis: CouncilAnalysis) -> CouncilAnalysis:
        """Save a completed council analysis"""
        self.council_analyses[analysis.id] = analysis
        return analysis
    
    async def get_council_analysis(self, analysis_id: str) -> Optional[CouncilAnalysis]:
        """Get a specific council analysis"""
        return self.council_analyses.get(analysis_id)
    
    async def get_council_analyses(self, user_id: str) -> List[CouncilAnalysis]:
        """Get all council analyses for a user"""
        analyses = [a for a in self.council_analyses.values() if a.userId == user_id]
        # Sort by createdAt descending (most recent first)
        analyses.sort(key=lambda x: x.createdAt, reverse=True)
        return analyses
    
    # Council Chat Messages operations (PostgreSQL)
    async def get_council_messages(self, session_id: str) -> List:
        """Get chat history for a council session"""
        print(f"[STORAGE] get_council_messages called with session_id: {session_id}")
        conn = await self._get_db_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM council_messages 
                WHERE session_id = $1 
                ORDER BY created_at ASC
                """,
                session_id
            )
            print(f"[STORAGE] Query returned {len(rows)} rows for session {session_id}")
            
            from models import CouncilChatMessage, StreamContribution
            messages = []
            for idx, row in enumerate(rows):
                print(f"[STORAGE] Processing row {idx+1}: role={row['role']}, content_length={len(row['content'])}")
                contributions = None
                if row["contributions"]:
                    contrib_list = json.loads(row["contributions"])
                    contributions = [StreamContribution(**c) for c in contrib_list]
                
                messages.append(CouncilChatMessage(
                    id=str(row["id"]),
                    sessionId=row["session_id"],
                    role=row["role"],
                    content=row["content"],
                    contributions=contributions,
                    createdAt=row["created_at"]
                ))
            
            print(f"[STORAGE] Returning {len(messages)} messages")
            return messages
        finally:
            await conn.close()
    
    async def create_council_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        contributions: Optional[str] = None
    ):
        """Save a council chat message"""
        conn = await self._get_db_connection()
        try:
            message_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO council_messages (
                    id, session_id, role, content, contributions
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                message_id, session_id, role, content, contributions
            )
            return message_id
        finally:
            await conn.close()
    
    # Persona operations (PostgreSQL)
    async def _get_db_connection(self):
        """Get PostgreSQL connection from DATABASE_URL"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        return await asyncpg.connect(database_url)
    
    async def create_persona(self, user_id: str, persona_data: dict) -> Persona:
        """Create a new persona in PostgreSQL"""
        conn = await self._get_db_connection()
        try:
            persona_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            row = await conn.fetchrow(
                """
                INSERT INTO personas (
                    id, user_id, name, research_mode,
                    demographics, psychographics,
                    pain_points, goals, values,
                    content_preferences, communities, behavioral_patterns,
                    research_data,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                RETURNING *
                """,
                persona_id, user_id,
                persona_data.get("name", ""),
                persona_data.get("researchMode", "quick"),
                json.dumps(persona_data.get("demographics", {})),
                json.dumps(persona_data.get("psychographics", {})),
                persona_data.get("painPoints", []),
                persona_data.get("goals", []),
                persona_data.get("values", []),
                json.dumps(persona_data.get("contentPreferences", {})),
                persona_data.get("communities", []),
                json.dumps(persona_data.get("behavioralPatterns", {})),
                json.dumps(persona_data.get("researchData", {})),
                now, now
            )
            
            return Persona(
                id=str(row["id"]),  # Convert UUID to string
                userId=row["user_id"],
                name=row["name"],
                researchMode=row["research_mode"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                researchData=json.loads(row["research_data"]) if row["research_data"] else {},
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get a specific persona by ID"""
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow("SELECT * FROM user_personas WHERE id = $1", persona_id)
            if not row:
                return None
            
            return Persona(
                id=str(row["id"]),  # Convert UUID to string
                userId=row["user_id"],
                name=row["name"],
                researchMode=row["research_mode"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                researchData=json.loads(row["research_data"]) if row["research_data"] else {},
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def get_personas(self, user_id: str) -> List[Persona]:
        """Get all personas for a user"""
        conn = await self._get_db_connection()
        try:
            rows = await conn.fetch(
                "SELECT * FROM user_personas WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            
            personas = []
            for row in rows:
                personas.append(Persona(
                    id=str(row["id"]),  # Convert UUID to string
                    userId=row["user_id"],
                    name=row["name"],
                    researchMode=row["research_mode"],
                    demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                    psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                    painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                    goals=list(row["goals"]) if row["goals"] else [],
                    values=list(row["values"]) if row["values"] else [],
                    contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                    communities=list(row["communities"]) if row["communities"] else [],
                    behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                    researchData=json.loads(row["research_data"]) if row["research_data"] else {},
                    createdAt=_parse_timestamp(row["created_at"]),
                    updatedAt=_parse_timestamp(row["updated_at"])
                ))
            
            return personas
        finally:
            await conn.close()
    
    async def update_persona(self, persona_id: str, updates: dict) -> Optional[Persona]:
        """Update a persona"""
        conn = await self._get_db_connection()
        try:
            now = datetime.utcnow()
            
            # Build dynamic UPDATE query based on provided fields
            set_clauses = ["updated_at = $1"]
            params: List[Any] = [now]
            param_num = 2
            
            field_mapping = {
                "name": "name",
                "demographics": "demographics",
                "psychographics": "psychographics",
                "painPoints": "pain_points",
                "goals": "goals",
                "values": "values",
                "contentPreferences": "content_preferences",
                "communities": "communities",
                "behavioralPatterns": "behavioral_patterns",
                "researchData": "research_data"
            }
            
            for field_camel, field_snake in field_mapping.items():
                if field_camel in updates:
                    value = updates[field_camel]
                    # JSON fields need to be stringified
                    if field_snake in ["demographics", "psychographics", "content_preferences", "behavioral_patterns", "research_data"]:
                        value = json.dumps(value)
                    
                    set_clauses.append(f"{field_snake} = ${param_num}")
                    params.append(value)
                    param_num += 1
            
            params.append(persona_id)
            query = f"UPDATE personas SET {', '.join(set_clauses)} WHERE id = ${param_num} RETURNING *"
            
            row = await conn.fetchrow(query, *params)
            if not row:
                return None
            
            return Persona(
                id=str(row["id"]),  # Convert UUID to string
                userId=row["user_id"],
                name=row["name"],
                researchMode=row["research_mode"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                researchData=json.loads(row["research_data"]) if row["research_data"] else {},
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona"""
        conn = await self._get_db_connection()
        try:
            result = await conn.execute("DELETE FROM user_personas WHERE id = $1", persona_id)
            return result == "DELETE 1"
        finally:
            await conn.close()
    
    # UserPersona operations (Unified Persona Model with YouTube enrichment)
    async def create_user_persona(self, user_id: str, data: UserPersonaCreate) -> UserPersona:
        """Create or replace user persona (UPSERT logic to handle unique constraint on user_id)"""
        conn = await self._get_db_connection()
        try:
            persona_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            row = await conn.fetchrow(
                """
                INSERT INTO user_personas (
                    id, user_id,
                    company_name, industry, company_size, target_audience,
                    main_products, channels, budget_range, primary_goal,
                    main_challenge, timeline,
                    demographics, psychographics, pain_points, goals, values,
                    communities, behavioral_patterns, content_preferences,
                    youtube_research, video_insights, campaign_references, inspiration_videos,
                    research_mode, enrichment_level, enrichment_status, research_completeness, last_enriched_at,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    industry = EXCLUDED.industry,
                    company_size = EXCLUDED.company_size,
                    target_audience = EXCLUDED.target_audience,
                    main_products = EXCLUDED.main_products,
                    channels = EXCLUDED.channels,
                    budget_range = EXCLUDED.budget_range,
                    primary_goal = EXCLUDED.primary_goal,
                    main_challenge = EXCLUDED.main_challenge,
                    timeline = EXCLUDED.timeline,
                    research_mode = EXCLUDED.research_mode,
                    enrichment_level = EXCLUDED.enrichment_level,
                    enrichment_status = EXCLUDED.enrichment_status,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                persona_id, user_id,
                data.companyName, data.industry, data.companySize, data.targetAudience,
                data.mainProducts, data.channels, data.budgetRange, data.primaryGoal,
                data.mainChallenge, data.timeline,
                json.dumps({}), json.dumps({}), [], [], [],
                [], json.dumps({}), json.dumps({}),
                json.dumps([]), [], json.dumps([]), json.dumps([]),
                data.researchMode, data.enrichmentLevel or data.researchMode, "pending", 0, None,
                now, now
            )
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def get_user_persona(self, user_id: str) -> Optional[UserPersona]:
        """Get the user persona for a specific user"""
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM user_personas WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
                user_id
            )
            if not row:
                return None
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def get_user_persona_by_id(self, persona_id: str) -> Optional[UserPersona]:
        """Get a specific user persona by ID"""
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM user_personas WHERE id = $1",
                persona_id
            )
            if not row:
                return None
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def update_user_persona(self, persona_id: str, updates: dict) -> UserPersona:
        """Update a user persona with partial updates"""
        conn = await self._get_db_connection()
        try:
            now = datetime.utcnow()
            
            set_clauses = ["updated_at = $1"]
            params: List[Any] = [now]
            param_num = 2
            
            field_mapping = {
                "companyName": "company_name",
                "industry": "industry",
                "companySize": "company_size",
                "targetAudience": "target_audience",
                "mainProducts": "main_products",
                "channels": "channels",
                "budgetRange": "budget_range",
                "primaryGoal": "primary_goal",
                "mainChallenge": "main_challenge",
                "timeline": "timeline",
                "demographics": "demographics",
                "psychographics": "psychographics",
                "painPoints": "pain_points",
                "goals": "goals",
                "values": "values",
                "communities": "communities",
                "behavioralPatterns": "behavioral_patterns",
                "contentPreferences": "content_preferences",
                "youtubeResearch": "youtube_research",
                "videoInsights": "video_insights",
                "campaignReferences": "campaign_references",
                "inspirationVideos": "inspiration_videos",
                "researchMode": "research_mode",
                "enrichmentLevel": "enrichment_level",
                "enrichmentStatus": "enrichment_status",
                "researchCompleteness": "research_completeness",
                "lastEnrichedAt": "last_enriched_at",
                # 8-Module Deep Persona System
                "psychographicCore": "psychographic_core",
                "buyerJourney": "buyer_journey",
                "behavioralProfile": "behavioral_profile",
                "languageCommunication": "language_communication",
                "strategicInsights": "strategic_insights",
                "jobsToBeDone": "jobs_to_be_done",
                "decisionProfile": "decision_profile",
                "copyExamples": "copy_examples"
            }
            
            json_fields = [
                "demographics", "psychographics", "behavioral_patterns", 
                "content_preferences", "youtube_research", "campaign_references", 
                "inspiration_videos",
                # 8-Module Deep Persona System (all JSON)
                "psychographic_core", "buyer_journey", "behavioral_profile",
                "language_communication", "strategic_insights", "jobs_to_be_done",
                "decision_profile", "copy_examples"
            ]
            
            for field_camel, field_snake in field_mapping.items():
                if field_camel in updates:
                    value = updates[field_camel]
                    if field_snake in json_fields:
                        value = json.dumps(value)
                    
                    set_clauses.append(f"{field_snake} = ${param_num}")
                    params.append(value)
                    param_num += 1
            
            params.append(persona_id)
            query = f"UPDATE user_personas SET {', '.join(set_clauses)} WHERE id = ${param_num} RETURNING *"
            
            row = await conn.fetchrow(query, *params)
            if not row:
                raise ValueError(f"UserPersona with id {persona_id} not found")
            
            return UserPersona(
                id=str(row["id"]),
                userId=row["user_id"],
                companyName=row["company_name"],
                industry=row["industry"],
                companySize=row["company_size"],
                targetAudience=row["target_audience"],
                mainProducts=row["main_products"],
                channels=list(row["channels"]) if row["channels"] else [],
                budgetRange=row["budget_range"],
                primaryGoal=row["primary_goal"],
                mainChallenge=row["main_challenge"],
                timeline=row["timeline"],
                demographics=json.loads(row["demographics"]) if row["demographics"] else {},
                psychographics=json.loads(row["psychographics"]) if row["psychographics"] else {},
                painPoints=list(row["pain_points"]) if row["pain_points"] else [],
                goals=list(row["goals"]) if row["goals"] else [],
                values=list(row["values"]) if row["values"] else [],
                communities=list(row["communities"]) if row["communities"] else [],
                behavioralPatterns=json.loads(row["behavioral_patterns"]) if row["behavioral_patterns"] else {},
                contentPreferences=json.loads(row["content_preferences"]) if row["content_preferences"] else {},
                youtubeResearch=json.loads(row["youtube_research"]) if row["youtube_research"] else [],
                videoInsights=list(row["video_insights"]) if row["video_insights"] else [],
                campaignReferences=json.loads(row["campaign_references"]) if row["campaign_references"] else [],
                inspirationVideos=json.loads(row["inspiration_videos"]) if row["inspiration_videos"] else [],
                researchMode=row["research_mode"],
                enrichmentLevel=row.get("enrichment_level"),
                enrichmentStatus=row.get("enrichment_status", "pending"),
                researchCompleteness=row["research_completeness"],
                lastEnrichedAt=_parse_timestamp(row["last_enriched_at"]) if row["last_enriched_at"] else None,
                # 8-Module Deep Persona System
                psychographicCore=json.loads(row["psychographic_core"]) if row.get("psychographic_core") else None,
                buyerJourney=json.loads(row["buyer_journey"]) if row.get("buyer_journey") else None,
                behavioralProfile=json.loads(row["behavioral_profile"]) if row.get("behavioral_profile") else None,
                languageCommunication=json.loads(row["language_communication"]) if row.get("language_communication") else None,
                strategicInsights=json.loads(row["strategic_insights"]) if row.get("strategic_insights") else None,
                jobsToBeDone=json.loads(row["jobs_to_be_done"]) if row.get("jobs_to_be_done") else None,
                decisionProfile=json.loads(row["decision_profile"]) if row.get("decision_profile") else None,
                copyExamples=json.loads(row["copy_examples"]) if row.get("copy_examples") else None,
                createdAt=_parse_timestamp(row["created_at"]),
                updatedAt=_parse_timestamp(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def enrich_persona_youtube(self, persona_id: str, youtube_data: dict) -> UserPersona:
        """Enrich persona with YouTube research data"""
        now = datetime.utcnow()
        
        updates = {
            "youtubeResearch": youtube_data.get("youtubeResearch", []),
            "videoInsights": youtube_data.get("videoInsights", []),
            "campaignReferences": youtube_data.get("campaignReferences", []),
            "inspirationVideos": youtube_data.get("inspirationVideos", []),
            "researchCompleteness": youtube_data.get("researchCompleteness", 50),
            "lastEnrichedAt": now
        }
        
        return await self.update_user_persona(persona_id, updates)
    
    async def delete_user_persona(self, persona_id: str) -> bool:
        """Delete a user persona"""
        conn = await self._get_db_connection()
        try:
            result = await conn.execute("DELETE FROM user_personas WHERE id = $1", persona_id)
            return result == "DELETE 1"
        finally:
            await conn.close()

# Global storage instance - PostgreSQL backed
storage = PostgresStorage()
