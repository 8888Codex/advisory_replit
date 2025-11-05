"""
UserMemoryTool - Access user's conversation history and profile for personalization
Enables continuity and context-aware recommendations
"""
from typing import Optional, Dict, Any, List


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
        # TODO: Implement PostgreSQL queries to fetch:
        # 1. user_profiles_extended table (psychographics, nicho, values)
        # 2. conversations_memory table (recent interactions)
        # 3. council_insights table (valuable outputs from past sessions)
        
        # Placeholder implementation - will be completed in db-schema-memory task
        return {
            "user_id": user_id,
            "profile": None,
            "recent_conversations": [],
            "past_insights": [],
            "expert_affinity": {},  # Which experts user engaged with most
            "tool": self.name
        }
    
    async def save_insight(
        self,
        user_id: str,
        insight: str,
        expert_name: str,
        category: str
    ) -> bool:
        """
        Save a valuable insight from expert analysis
        
        Args:
            user_id: User identifier
            insight: The insight text
            expert_name: Which expert provided it
            category: Type of insight (strategy, tactic, warning, etc.)
        
        Returns:
            Success boolean
        """
        # TODO: Implement PostgreSQL insert to council_insights table
        # Will be completed in db-schema-memory task
        return True
    
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
