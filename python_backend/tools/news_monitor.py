"""
NewsMonitorTool - Monitor recent news about markets, competitors, and industries
Provides breaking news and recent developments
"""
import os
import httpx
from typing import Dict, Any


class NewsMonitorTool:
    """
    Tool that monitors recent news about specific markets, competitors,
    industries, or topics. Returns headlines, URLs, and contextualized summaries.
    
    Benefits for "Disney Experience":
    - Experts can reference current events and breaking news
    - Provides competitive intelligence from news sources
    - Grounds recommendations in latest market developments
    """
    
    def __init__(self):
        self.name = "news_monitor"
        self.description = (
            "Monitors recent news about markets, competitors, industries, or topics. "
            "Returns headlines, article URLs, publication dates, and key takeaways. "
            "Use when current events or competitive intelligence is needed."
        )
        self._api_key = None
        self._base_url = None
        self._model = None
    
    def _ensure_initialized(self):
        """Lazy initialization - validates API key only when needed"""
        if self._api_key is None:
            self._api_key = os.getenv("PERPLEXITY_API_KEY")
            if not self._api_key:
                raise ValueError("PERPLEXITY_API_KEY required for news monitoring")
            
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
    
    async def run(self, query: str, days: int = 30) -> Dict[str, Any]:
        """
        Execute news monitoring query
        
        Args:
            query: Topic to monitor (e.g., "Nubank marketing strategy")
            days: How many days back to search (default: 30)
        
        Returns:
            Dict with news findings, headlines, sources
        """
        self._ensure_initialized()
        
        # Build specialized news monitoring prompt
        time_range = "últimos 7 dias" if days <= 7 else f"últimos {days} dias"
        
        research_query = (
            f"Busque notícias recentes ({time_range}) sobre: {query}\n\n"
            f"Para cada notícia relevante, forneça:\n"
            f"1. Headline/Título da notícia\n"
            f"2. Fonte e data de publicação\n"
            f"3. URL do artigo (quando disponível)\n"
            f"4. Resumo dos pontos principais (2-3 frases)\n"
            f"5. Implicações para marketing/negócios\n\n"
            f"Priorize fontes confiáveis de negócios e marketing. "
            f"Organize do mais recente para o mais antigo. "
            f"Foque em desenvolvimentos significativos, anúncios importantes, "
            f"ou mudanças de mercado relevantes."
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
                                "Você é um monitor de notícias especializado em marketing e negócios. "
                                "SEMPRE responda em português brasileiro. "
                                "Sua especialidade é identificar notícias relevantes e extrair "
                                "insights acionáveis para profissionais de marketing. "
                                "Priorize fontes confiáveis e foque em desenvolvimentos significativos."
                            )
                        },
                        {
                            "role": "user",
                            "content": research_query
                        }
                    ],
                    "temperature": 0.2,
                    "search_recency_filter": "week" if days <= 7 else "month",
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
            "time_range": time_range,
            "tool": self.name,
            "article_count": len(sources)
        }
    
    def get_prompt_instruction(self) -> str:
        """Returns instruction text for agent system prompts"""
        return (
            "\n\n## 📰 FERRAMENTA: News Monitor\n"
            "Você tem acesso a monitoramento de notícias recentes sobre mercados, "
            "concorrentes, e indústrias. Quando precisar de inteligência competitiva "
            "ou eventos atuais, sinalize:\n"
            "**[NEWS_MONITOR: tópico ou empresa]**\n\n"
            "Exemplo: [NEWS_MONITOR: Magazine Luiza estratégias de marketing 2024]\n\n"
            "Você receberá headlines recentes, fontes, e análise de implicações."
        )


# Global instance
news_tool = NewsMonitorTool()
