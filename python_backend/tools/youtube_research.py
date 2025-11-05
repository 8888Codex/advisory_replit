"""
YouTubeResearchTool - Find relevant marketing campaigns, case studies, and video content
Specializes in discovering YouTube videos with actionable insights
"""
import os
import httpx
from typing import Dict, Any, List


class YouTubeResearchTool:
    """
    Tool that finds relevant YouTube videos about marketing campaigns, case studies,
    and expert content. Returns video titles, URLs, summaries, and key metrics.
    
    Benefits for "Disney Experience":
    - Experts can reference real campaigns and case studies
    - Provides current video content with timestamps
    - Grounds recommendations in visual examples
    """
    
    def __init__(self):
        self.name = "youtube_research"
        self.description = (
            "Finds relevant YouTube videos about marketing campaigns, case studies, "
            "expert talks, and tutorials. Returns video titles, URLs, channel info, "
            "and summaries. Use when you need visual examples or case studies."
        )
        self._api_key = None
        self._base_url = None
        self._model = None
    
    def _ensure_initialized(self):
        """Lazy initialization - validates API key only when needed"""
        if self._api_key is None:
            self._api_key = os.getenv("PERPLEXITY_API_KEY")
            if not self._api_key:
                raise ValueError("PERPLEXITY_API_KEY required for YouTube research")
            
            self._base_url = "https://api.perplexity.ai/chat/completions"
            self._model = "sonar-pro"
    
    @property
    def api_key(self) -> str:
        self._ensure_initialized()
        assert self._api_key is not None
        return self._api_key
    
    @property
    def base_url(self) -> str:
        self._ensure_initialized()
        assert self._base_url is not None
        return self._base_url
    
    @property
    def model(self) -> str:
        self._ensure_initialized()
        assert self._model is not None
        return self._model
    
    async def run(self, query: str) -> Dict[str, Any]:
        """
        Execute YouTube research query
        
        Args:
            query: Research topic (e.g., "Nike marketing campaigns 2024")
        
        Returns:
            Dict with findings (formatted list of videos), sources, metadata
        """
        self._ensure_initialized()
        
        # Build specialized YouTube search prompt
        research_query = (
            f"Pesquise vídeos no YouTube sobre: {query}\n\n"
            f"Para cada vídeo relevante encontrado, forneça:\n"
            f"1. Título do vídeo\n"
            f"2. URL do YouTube\n"
            f"3. Canal/Criador\n"
            f"4. Resumo breve (2-3 frases) do conteúdo principal\n"
            f"5. Principais insights ou lições\n\n"
            f"Foque em conteúdo recente (2023-2025) e de alta qualidade. "
            f"Priorize vídeos com insights acionáveis, cases de sucesso, "
            f"ou análises profissionais de marketing."
        )
        
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
                                "Você é um especialista em curadoria de conteúdo de marketing. "
                                "SEMPRE responda em português brasileiro. "
                                "Sua especialidade é encontrar vídeos relevantes do YouTube "
                                "sobre campanhas, cases, tutoriais e análises de marketing. "
                                "Forneça informações estruturadas e acionáveis sobre cada vídeo."
                            )
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
            response.raise_for_status()
            data = response.json()
        
        findings = data["choices"][0]["message"]["content"]
        sources = []
        if "citations" in data:
            sources = data["citations"]
        elif "search_results" in data:
            sources = [result.get("url", "") for result in data["search_results"]]
        
        return {
            "findings": findings,
            "sources": sources,
            "query": query,
            "tool": self.name,
            "video_count": findings.count("youtube.com")  # Approximate count
        }
    
    def get_prompt_instruction(self) -> str:
        """Returns instruction text for agent system prompts"""
        return (
            "\n\n## 🎥 FERRAMENTA: YouTube Research\n"
            "Você tem acesso a busca de vídeos do YouTube sobre marketing, campanhas, "
            "e cases de sucesso. Quando quiser referenciar campanhas visuais, tutoriais, "
            "ou casos de estudo, sinalize:\n"
            "**[YOUTUBE_RESEARCH: seu tópico de pesquisa]**\n\n"
            "Exemplo: [YOUTUBE_RESEARCH: Campanhas virais de e-commerce 2024]\n\n"
            "Você receberá lista de vídeos relevantes com URLs e insights."
        )


# Global instance
youtube_tool = YouTubeResearchTool()
