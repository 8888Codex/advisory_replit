"""
Perplexity Research Module
Contextualizes market research using BusinessProfile data
"""
import os
import httpx
from typing import List, Dict, Optional, Any
from models import BusinessProfile

class PerplexityResearch:
    """Wrapper for Perplexity API with business context and lazy initialization"""
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._base_url: Optional[str] = None
        self._model: Optional[str] = None
    
    def _ensure_initialized(self):
        """Lazy initialization - validates API key only when needed"""
        if self._api_key is None:
            self._api_key = os.getenv("PERPLEXITY_API_KEY")
            if not self._api_key:
                raise ValueError(
                    "PERPLEXITY_API_KEY environment variable is required for market research. "
                    "Please configure your API key in environment variables."
                )
            
            self._base_url = "https://api.perplexity.ai/chat/completions"
            self._model = "sonar-pro"  # Advanced search with grounding for complex queries
    
    @property
    def api_key(self) -> str:
        self._ensure_initialized()
        if self._api_key is None:
            raise RuntimeError("API key failed to initialize")
        return self._api_key
    
    @property
    def base_url(self) -> str:
        self._ensure_initialized()
        if self._base_url is None:
            raise RuntimeError("Base URL failed to initialize")
        return self._base_url
    
    @property
    def model(self) -> str:
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Model failed to initialize")
        return self._model
    
    async def research(
        self,
        problem: str,
        profile: Optional[BusinessProfile] = None
    ) -> Dict[str, Any]:
        """
        Perform contextualized market research
        
        Args:
            problem: User's business problem/question
            profile: BusinessProfile for context (optional)
        
        Returns:
            Dict with findings and sources
        """
        # Build contextualized research query
        query = self._build_research_query(problem, profile)
        
        # Call Perplexity API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Você é um analista de pesquisa de mercado. SEMPRE responda em português brasileiro. "
                                "Forneça insights factuais e baseados em dados com estatísticas específicas, tendências e exemplos. "
                                "Foque em dados recentes (2024-2025). "
                                "Inclua análise competitiva e benchmarks do setor quando relevante."
                            )
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "temperature": 0.2,
                    "search_recency_filter": "month",
                    "return_related_questions": False
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract findings and citations
        findings = data["choices"][0]["message"]["content"]
        # Sources can be in 'citations' or 'search_results'
        sources = []
        if "citations" in data:
            sources = data["citations"]
        elif "search_results" in data:
            sources = [result.get("url", "") for result in data["search_results"]]
        
        return {
            "query": query,
            "findings": findings,
            "sources": sources,
            "model": data["model"]
        }
    
    def _build_research_query(
        self,
        problem: str,
        profile: Optional[BusinessProfile]
    ) -> str:
        """Build contextualized research query using business profile"""
        
        if not profile:
            # Generic research without context
            return f"Pesquisa de mercado e tendências para: {problem}"
        
        # Build rich context from profile (Pydantic uses camelCase attributes)
        context_parts = []
        
        # Industry and company size context
        context_parts.append(
            f"Setor: {profile.industry} "
            f"(porte da empresa: {profile.companySize})"
        )
        
        # Target audience context
        context_parts.append(f"Público-alvo: {profile.targetAudience}")
        
        # Channels context
        if profile.channels:
            channels_str = ", ".join(profile.channels)
            context_parts.append(f"Canais de venda: {channels_str}")
        
        # Primary goal context
        goal_map = {
            "growth": "focado em crescimento e aquisição de clientes",
            "positioning": "trabalhando em posicionamento e diferenciação de marca",
            "retention": "melhorando retenção e fidelização de clientes",
            "launch": "lançando novos produtos/serviços",
            "awareness": "construindo reconhecimento de marca"
        }
        goal_desc = goal_map.get(profile.primaryGoal, profile.primaryGoal)
        context_parts.append(f"Objetivo principal: {goal_desc}")
        
        # Build final query
        context = ". ".join(context_parts)
        
        query = (
            f"Contexto: {context}. "
            f"Problema/Pergunta: {problem}. "
            f"\n\nForneça pesquisa de mercado incluindo: "
            f"1) Tendências atuais da indústria e estatísticas para {profile.industry}, "
            f"2) Cenário competitivo e benchmarks, "
            f"3) Melhores práticas para empresas de porte similar ({profile.companySize}), "
            f"4) Dados específicos relevantes ao problema mencionado acima. "
            f"Foque em insights acionáveis com dados recentes (2024-2025)."
        )
        
        return query

# Global instance
perplexity_research = PerplexityResearch()
