"""
TrendAnalysisTool - Analyze Google Trends and market trends
Identifies rising/declining search terms and market movements
"""
import os
import httpx
from typing import Dict, Any


class TrendAnalysisTool:
    """
    Tool that analyzes Google Trends data and market trends to identify
    rising/declining search terms, seasonal patterns, and market movements.
    
    Benefits for "Disney Experience":
    - Experts can validate timing recommendations with trend data
    - Provides growth metrics and seasonal insights
    - Grounds strategy in search behavior patterns
    """
    
    def __init__(self):
        self.name = "trend_analysis"
        self.description = (
            "Analyzes Google Trends and market trends for specific topics, keywords, "
            "or industries. Returns growth metrics, seasonal patterns, related queries, "
            "and trending insights. Use when timing or trend validation is critical."
        )
        self._api_key = None
        self._base_url = None
        self._model = None
    
    def _ensure_initialized(self):
        """Lazy initialization - validates API key only when needed"""
        if self._api_key is None:
            self._api_key = os.getenv("PERPLEXITY_API_KEY")
            if not self._api_key:
                raise ValueError("PERPLEXITY_API_KEY required for trend analysis")
            
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
    
    async def run(self, query: str, region: str = "BR") -> Dict[str, Any]:
        """
        Execute trend analysis query
        
        Args:
            query: Topic or keyword to analyze (e.g., "marketing digital")
            region: Region code (default: "BR" for Brazil)
        
        Returns:
            Dict with trend findings, growth metrics, sources
        """
        self._ensure_initialized()
        
        # Build specialized trends analysis prompt
        research_query = (
            f"Analise tendências do Google Trends e mercado para: {query} "
            f"(região: {region})\n\n"
            f"Forneça análise detalhada incluindo:\n"
            f"1. Tendência atual (crescendo, estável, ou declinando)\n"
            f"2. Métricas de crescimento percentual (últimos 3-12 meses)\n"
            f"3. Padrões sazonais identificados\n"
            f"4. Termos relacionados em alta\n"
            f"5. Insights sobre comportamento de busca do público\n"
            f"6. Comparação com termos similares ou concorrentes\n\n"
            f"Inclua dados específicos e números sempre que possível. "
            f"Foque em tendências de 2024-2025."
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
                                "Você é um analista de tendências de mercado especializado em "
                                "Google Trends e comportamento de busca. SEMPRE responda em português brasileiro. "
                                "Forneça análises quantitativas com métricas específicas, "
                                "identificando padrões sazonais e oportunidades de timing. "
                                "Sempre inclua comparações e contexto competitivo."
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
            "region": region,
            "tool": self.name
        }
    
    def get_prompt_instruction(self) -> str:
        """Returns instruction text for agent system prompts"""
        return (
            "\n\n## 📊 FERRAMENTA: Trend Analysis\n"
            "Você tem acesso a análise de tendências do Google Trends e mercado. "
            "Quando precisar validar timing, identificar oportunidades sazonais, "
            "ou entender comportamento de busca, sinalize:\n"
            "**[TREND_ANALYSIS: termo ou tópico]**\n\n"
            "Exemplo: [TREND_ANALYSIS: marketing de influência]\n\n"
            "Você receberá métricas de crescimento, padrões sazonais, e termos relacionados."
        )


# Global instance
trend_tool = TrendAnalysisTool()
