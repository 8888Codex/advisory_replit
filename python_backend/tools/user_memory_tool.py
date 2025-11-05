"""
UserMemoryTool - Access user's conversation history and profile for personalization
Enables continuity and context-aware recommendations
"""
from typing import Optional, Dict, Any, List
import os
import asyncpg
import json


class UserMemoryTool:
    """
    Tool that allows marketing legend agents to access user's conversation history,
    business profile, and accumulated insights for personalized recommendations.
    
    Benefits for "Disney Experience":
    - Remembers past conversations and recommendations
    - Understands user's business context deeply
    - Provides continuity across sessions
    - Enables proactive suggestions based on history
    """
    
    def __init__(self):
        self.name = "user_memory"
        self.description = (
            "Accesses user's conversation history, business profile, "
            "and past insights. Use to provide personalized, context-aware "
            "recommendations that build on previous interactions."
        )
    
    async def get_user_context(
        self,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve user's recent conversation history and profile
        
        Args:
            user_id: User identifier
            limit: Number of recent messages to retrieve
        
        Returns:
            Dict containing user profile, recent conversations, insights
        """
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return self._empty_context(user_id)
        
        conn = None
        try:
            conn = await asyncpg.connect(database_url)
            
            # 1. Get user profile extended (psychographics)
            profile_row = await conn.fetchrow(
                "SELECT * FROM user_profiles_extended WHERE user_id = $1",
                user_id
            )
            profile = dict(profile_row) if profile_row else None
            
            # 2. Get recent council insights (valuable outputs)
            insights_rows = await conn.fetch(
                """SELECT insight, expert_name, category, created_at 
                   FROM council_insights 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC 
                   LIMIT $2""",
                user_id, limit
            )
            past_insights = [dict(row) for row in insights_rows]
            
            # 3. Get recent council sessions (for context continuity)
            sessions_rows = await conn.fetch(
                """SELECT id, problem, consensus, created_at 
                   FROM council_sessions 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC 
                   LIMIT $2""",
                user_id, 5
            )
            recent_sessions = [dict(row) for row in sessions_rows]
            
            # 4. Parse expert affinity if available
            expert_affinity = {}
            if profile and profile.get("expert_affinity"):
                try:
                    expert_affinity = json.loads(profile["expert_affinity"])
                except:
                    pass
            
            return {
                "user_id": user_id,
                "profile": profile,
                "recent_sessions": recent_sessions,
                "past_insights": past_insights,
                "expert_affinity": expert_affinity,
                "tool": self.name
            }
        except Exception as e:
            print(f"⚠️ UserMemoryTool.get_user_context error: {str(e)}")
            return self._empty_context(user_id)
        finally:
            if conn:
                await conn.close()
    
    def _empty_context(self, user_id: str) -> Dict[str, Any]:
        """Fallback empty context when DB unavailable"""
        return {
            "user_id": user_id,
            "profile": None,
            "recent_sessions": [],
            "past_insights": [],
            "expert_affinity": {},
            "tool": self.name
        }
    
    async def save_insight(
        self,
        user_id: str,
        insight: str,
        expert_name: str,
        category: str,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Save a valuable insight from expert analysis
        
        Args:
            user_id: User identifier
            insight: The insight text
            expert_name: Which expert provided it
            category: Type of insight (strategy, tactic, warning, etc.)
            session_id: Optional council session ID
        
        Returns:
            Success boolean
        """
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return False
        
        conn = None
        try:
            conn = await asyncpg.connect(database_url)
            
            # Insert insight into council_insights table
            await conn.execute(
                """INSERT INTO council_insights 
                   (session_id, user_id, expert_name, insight, category) 
                   VALUES ($1, $2, $3, $4, $5)""",
                session_id or "standalone",
                user_id,
                expert_name,
                insight,
                category
            )
            
            return True
        except Exception as e:
            print(f"⚠️ UserMemoryTool.save_insight error: {str(e)}")
            return False
        finally:
            if conn:
                await conn.close()
    
    def get_prompt_instruction(self) -> str:
        """
        Returns instruction text for including in agent system prompts
        """
        return (
            "\n\n## 💾 FERRAMENTA: User Memory\n"
            "Você tem acesso ao histórico de conversas e perfil do usuário. "
            "Use isso para fornecer recomendações contextualizadas e lembrar de "
            "interações passadas. Quando referir-se a conversas anteriores, "
            "seja específico: 'Como discutimos na sessão anterior sobre [tópico]...'\n\n"
            "O sistema automaticamente carrega contexto relevante do usuário "
            "antes de cada análise."
        )


# Global instance for easy import
user_memory_tool = UserMemoryTool()
