from typing import Dict, List, Optional
from datetime import datetime
import uuid
from models import (
    Expert, ExpertCreate, Conversation, ConversationCreate, 
    Message, MessageCreate, ExpertType, CategoryType, BusinessProfile, BusinessProfileCreate,
    CouncilAnalysis, Persona, PersonaCreate
)
import os
import json
from datetime import datetime as dt
import asyncpg

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
                createdAt=row["created_at"].isoformat() if hasattr(row["created_at"], 'isoformat') else str(row["created_at"]),
                updatedAt=row["updated_at"].isoformat() if hasattr(row["updated_at"], 'isoformat') else str(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get a specific persona by ID"""
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow("SELECT * FROM personas WHERE id = $1", persona_id)
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
                createdAt=row["created_at"].isoformat() if hasattr(row["created_at"], 'isoformat') else str(row["created_at"]),
                updatedAt=row["updated_at"].isoformat() if hasattr(row["updated_at"], 'isoformat') else str(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def get_personas(self, user_id: str) -> List[Persona]:
        """Get all personas for a user"""
        conn = await self._get_db_connection()
        try:
            rows = await conn.fetch(
                "SELECT * FROM personas WHERE user_id = $1 ORDER BY created_at DESC",
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
                    createdAt=row["created_at"],
                    updatedAt=row["updated_at"]
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
            params = [now]
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
                createdAt=row["created_at"].isoformat() if hasattr(row["created_at"], 'isoformat') else str(row["created_at"]),
                updatedAt=row["updated_at"].isoformat() if hasattr(row["updated_at"], 'isoformat') else str(row["updated_at"])
            )
        finally:
            await conn.close()
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona"""
        conn = await self._get_db_connection()
        try:
            result = await conn.execute("DELETE FROM personas WHERE id = $1", persona_id)
            return result == "DELETE 1"
        finally:
            await conn.close()

# Global storage instance
storage = MemStorage()
