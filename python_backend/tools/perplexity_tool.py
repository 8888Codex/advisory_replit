"""
PerplexityResearchTool - Real-time market research capability for experts
Allows experts to conduct focused research during analysis
"""
from typing import Optional, Dict, Any
from models import BusinessProfile
from perplexity_research import perplexity_research


class PerplexityResearchTool:
    """
    Tool that allows marketing legend agents to conduct real-time market research
    during their analysis using Perplexity API.
    
    Benefits for "Disney Experience":
    - Experts can validate their recommendations with current data
    - Provides recent statistics and trends (2024-2025)
    - Grounds expert advice in factual market intelligence
    """
    
    def __init__(self):
        self.name = "perplexity_research"
        self.description = (
            "Conducts real-time market research using Perplexity AI. "
            "Provides current trends, statistics, competitive analysis, "
            "and industry benchmarks. Use when you need factual data to "
            "support your recommendations."
        )
    
    async def run(
        self,
        query: str,
        profile: Optional[BusinessProfile] = None
    ) -> Dict[str, Any]:
        """
        Execute market research query
        
        Args:
            query: Specific research question or topic
            profile: Optional BusinessProfile for contextualization
        
        Returns:
            Dict containing findings, sources, and metadata
        """
        result = await perplexity_research.research(
            problem=query,
            profile=profile
        )
        
        return {
            "findings": result["findings"],
            "sources": result["sources"],
            "query": result["query"],
            "tool": self.name
        }
    
    def get_prompt_instruction(self) -> str:
        """
        Returns instruction text for including in agent system prompts
        """
        return (
            "\n\n## 🔍 FERRAMENTA: Perplexity Research\n"
            "Você tem acesso a pesquisa de mercado em tempo real via Perplexity AI. "
            "Quando precisar validar suas recomendações com dados atuais, estatísticas, "
            "ou análise competitiva, sinalize claramente:\n"
            "**[PERPLEXITY_RESEARCH_NEEDED: sua pergunta específica]**\n\n"
            "Exemplo: [PERPLEXITY_RESEARCH_NEEDED: Tendências de marketing digital para "
            "e-commerce de moda no Brasil em 2025]\n\n"
            "O sistema irá conduzir a pesquisa e você receberá os insights para "
            "enriquecer sua resposta."
        )


# Global instance for easy import
perplexity_tool = PerplexityResearchTool()
