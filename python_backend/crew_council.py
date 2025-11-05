"""
CrewAI Council Orchestration - Multi-Expert Collaborative Analysis
"""
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic
import os
from models import Expert, BusinessProfile, CouncilAnalysis, AgentContribution
from perplexity_research import perplexity_research
from tools.perplexity_tool import PerplexityResearchTool
from tools.user_memory_tool import UserMemoryTool
from tools.story_bank_tool import StoryBankTool
from tools.youtube_research import YouTubeResearchTool
from tools.trend_analysis import TrendAnalysisTool
from tools.news_monitor import NewsMonitorTool

class CouncilOrchestrator:
    """
    Orchestrates collaborative analysis by a council of marketing legend experts.
    
    Flow:
    1. Conduct Perplexity research (if BusinessProfile available)
    2. Each expert analyzes the problem concurrently (with semaphore for rate limiting)
    3. Synthesize consensus from all expert contributions
    """
    
    def __init__(self):
        self._anthropic_client: Optional[AsyncAnthropic] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        
        # Initialize custom tools for expert enrichment
        self.perplexity_tool = PerplexityResearchTool()
        self.user_memory_tool = UserMemoryTool()
        self.story_bank_tool = StoryBankTool()
        self.youtube_tool = YouTubeResearchTool()
        self.trend_tool = TrendAnalysisTool()
        self.news_tool = NewsMonitorTool()
        
        # Build tools dict for easy access
        self.tools: Dict[str, Any] = {
            "perplexity_research": self.perplexity_tool,
            "user_memory": self.user_memory_tool,
            "story_bank": self.story_bank_tool,
            "youtube_research": self.youtube_tool,
            "trend_analysis": self.trend_tool,
            "news_monitor": self.news_tool
        }
    
    def _ensure_initialized(self):
        """Lazy initialization - validates API key only when needed"""
        if self._anthropic_client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is required for council analysis. "
                    "Please configure your API key in environment variables."
                )
            
            self._anthropic_client = AsyncAnthropic(api_key=api_key)
            self._semaphore = asyncio.Semaphore(3)  # Max 3 concurrent Claude calls
    
    @property
    def anthropic_client(self) -> AsyncAnthropic:
        self._ensure_initialized()
        if self._anthropic_client is None:
            raise RuntimeError("Anthropic client failed to initialize")
        return self._anthropic_client
    
    @property
    def semaphore(self) -> asyncio.Semaphore:
        self._ensure_initialized()
        if self._semaphore is None:
            raise RuntimeError("Semaphore failed to initialize")
        return self._semaphore
    
    async def analyze(
        self,
        problem: str,
        experts: List[Expert],
        profile: Optional[BusinessProfile] = None,
        user_id: str = "demo_user"
    ) -> CouncilAnalysis:
        """
        Run collaborative council analysis with all experts.
        
        Args:
            problem: User's business problem/question
            experts: List of Expert models to consult
            profile: Optional BusinessProfile for context
            user_id: User identifier
        
        Returns:
            CouncilAnalysis with all expert contributions and consensus
        """
        analysis_id = str(uuid.uuid4())
        
        # Step 0: Load user context via UserMemoryTool (psychographics, past insights, sessions)
        user_context = await self.user_memory_tool.get_user_context(user_id, limit=5)
        
        # Step 1: Conduct market research using Perplexity (if profile available)
        research_findings = None
        citations = []
        
        if profile:
            research_result = await perplexity_research.research(
                problem=problem,
                profile=profile
            )
            research_findings = research_result["findings"]
            citations = research_result["sources"]
        
        # Step 2: Get individual expert analyses concurrently with rate limiting
        tasks = [
            self._get_expert_analysis(
                expert=expert,
                problem=problem,
                research_findings=research_findings,
                profile=profile,
                user_id=user_id,
                user_context=user_context
            )
            for expert in experts
        ]
        
        # Run concurrently but respect rate limits via semaphore
        contributions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failures and log them
        valid_contributions = []
        for i, contrib in enumerate(contributions):
            if isinstance(contrib, Exception):
                print(f"⚠️ Expert {experts[i].name} analysis failed: {str(contrib)}")
            else:
                valid_contributions.append(contrib)
        
        if not valid_contributions:
            raise Exception("All expert analyses failed - unable to generate council analysis")
        
        contributions = valid_contributions
        
        # Step 3: Synthesize consensus from all contributions
        consensus = await self._synthesize_consensus(
            problem=problem,
            contributions=contributions,
            research_findings=research_findings
        )
        
        # Build final analysis
        analysis = CouncilAnalysis(
            id=analysis_id,
            userId=user_id,
            problem=problem,
            profileId=profile.id if profile else None,
            marketResearch=research_findings,
            contributions=contributions,
            consensus=consensus,
            citations=citations
        )
        
        return analysis
    
    async def _get_expert_analysis(
        self,
        expert: Expert,
        problem: str,
        research_findings: Optional[str],
        profile: Optional[BusinessProfile],
        user_id: str = "demo_user",
        user_context: Optional[Dict[str, Any]] = None,
        colleague_contributions: Optional[List[Dict[str, str]]] = None
    ) -> AgentContribution:
        """
        Get analysis from a single expert using their cognitive clone with tool support.
        Uses semaphore to limit concurrent API calls and prevent rate limiting.
        
        Args:
            colleague_contributions: List of {"expert_name": str, "contribution": str} 
                                    from colleagues who already spoke in this round (for roundtable)
        
        Returns:
            AgentContribution with expert's unique perspective
        """
        async with self.semaphore:
            # Build enhanced system prompt with tool instructions
            enhanced_system = self._build_enhanced_system_prompt(expert, user_id)
            
            # Build context-rich prompt
            context_parts = []
            
            # Add colleague contributions for roundtable discussion (Council Room only)
            if colleague_contributions and len(colleague_contributions) > 0:
                colleagues_text = "**SEUS COLEGAS JÁ FALARAM (ouça e dialogue com eles):**\n\n"
                for idx, colleague in enumerate(colleague_contributions, 1):
                    colleagues_text += f"--- {colleague['expert_name']} ---\n"
                    colleagues_text += f"{colleague['contribution']}\n\n"
                
                context_parts.append(colleagues_text)
            
            # Add user context (psychographics, past insights) if available
            if user_context and user_context.get("profile"):
                user_profile = user_context["profile"]
                context_parts.append(
                    f"**User Profile & Context:**\n"
                    f"- Business Stage: {user_profile.get('business_stage', 'Unknown')}\n"
                    f"- Niche: {user_profile.get('niche', 'Unknown')}\n"
                    f"- Marketing Maturity: {user_profile.get('marketing_maturity', 'Unknown')}\n"
                    f"- Communication Style: {user_profile.get('preferred_communication_style', 'Unknown')}\n"
                )
                
                # Add past insights if available
                if user_context.get("past_insights"):
                    insights_summary = [
                        f"  • {insight['expert_name']}: {insight['insight'][:100]}..."
                        for insight in user_context["past_insights"][:3]
                    ]
                    context_parts.append(
                        f"**Past Insights (Continuity):**\n" + "\n".join(insights_summary) + "\n"
                    )
            
            # Add analysis context for follow-up questions (Council Room)
            if user_context and user_context.get("analysis_context"):
                context_parts.append(user_context["analysis_context"])
            
            # Add business context if available
            if profile:
                context_parts.append(
                    f"**Business Context:**\n"
                    f"- Company: {profile.companyName} ({profile.companySize} employees)\n"
                    f"- Industry: {profile.industry}\n"
                    f"- Target Audience: {profile.targetAudience}\n"
                    f"- Products: {profile.mainProducts}\n"
                    f"- Channels: {', '.join(profile.channels)}\n"
                    f"- Budget: {profile.budgetRange}\n"
                    f"- Primary Goal: {profile.primaryGoal}\n"
                    f"- Main Challenge: {profile.mainChallenge}\n"
                    f"- Timeline: {profile.timeline}\n"
                )
            
            # Add market research if available
            if research_findings:
                context_parts.append(
                    f"**Market Research & Intelligence:**\n{research_findings}\n"
                )
            
            # Build final user message
            context = "\n\n".join(context_parts) if context_parts else ""
            
            # Build dialogue instructions if colleagues have spoken
            dialogue_instructions = ""
            if colleague_contributions and len(colleague_contributions) > 0:
                colleague_names = [c['expert_name'] for c in colleague_contributions]
                colleagues_str = ", ".join(colleague_names[:-1]) + f" e {colleague_names[-1]}" if len(colleague_names) > 1 else colleague_names[0]
                
                dialogue_instructions = f"""
**ROUNDTABLE DISCUSSION - DIALOGUE COM SEUS COLEGAS:**
{colleagues_str} já {'falaram' if len(colleague_names) > 1 else 'falou'}. Você está em uma mesa redonda de consultoria.

**OBRIGATÓRIO:**
1. **COMENTE** o que seus colegas disseram:
   - "Concordo com o [nome] sobre..."
   - "Interessante o ponto do/da [nome], mas eu adicionaria..."
   - "O [nome] levantou [X], e isso me faz pensar em..."
   - "Diferente do que o/a [nome] sugeriu, eu vejo..."

2. **CONSTRUA** em cima das contribuições deles:
   - Complemente pontos que eles levantaram
   - Ofereça perspectiva diferente quando discordar
   - Conecte sua experiência com o que foi dito

3. **NÃO IGNORE** seus colegas - esta é uma CONVERSA entre vocês, não opiniões paralelas

**Exemplo de como começar:**
"Olha, concordo com o [nome] sobre [ponto X]. E baseado na minha experiência com [Y], eu adicionaria que..."
"""

            user_message = f"""**IMPORTANTE: Responda SEMPRE em português brasileiro (PT-BR) natural e coloquial.**

{context}

**Pergunta do usuário:**
{problem}
{dialogue_instructions}
**Sua Tarefa - CONVERSA de Acompanhamento:**
Você está no Council Room, em uma conversa de follow-up. O usuário já recebeu sua análise completa inicial e agora está fazendo perguntas adicionais.

RESPONDA de forma:
- **CONVERSACIONAL e DIRETA** - Como se estivesse em uma call de consultoria, não em uma apresentação formal
- **CONCISA** - 2-4 parágrafos curtos, máximo 500-600 palavras total
- **FOCADA** - Responda a pergunta específica, não repita toda a análise inicial
- **COM MEMÓRIA** - Referencie explicitamente a conversa anterior usando frases como:
  • "Como eu mencionei sobre..."
  • "Voltando ao que discutimos sobre..."
  • "Baseado naquele ponto que levantei..."
  • "Complementando a análise anterior..."

**Tom brasileiro autêntico:**
- Use expressões naturais BR: "O lance é...", "Olha só...", "Vou direto ao ponto..."
- Evite anglicismos e tom acadêmico
- Fale como você falaria em uma conversa real de consultoria

**Evite:**
- Headers formais (## CORE ANALYSIS)
- Listas extensas de bullet points
- Repetir contexto já fornecido
- Tom professoral ou apresentação de slides

Seja você mesmo, mas numa conversa natural."""
            
            # Call Claude with expert's enhanced system prompt (with timeout)
            try:
                response = await asyncio.wait_for(
                    self.anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=800,  # Reduced from 3000 to force concise responses
                        system=enhanced_system,
                        messages=[{
                            "role": "user",
                            "content": user_message
                        }]
                    ),
                    timeout=60.0  # 60 second timeout per expert
                )
                
                # Extract text response (handle TextBlock type)
                response_text = ""
                for block in response.content:
                    if block.type == "text":
                        response_text = block.text  # type: ignore
                        break
                
                # Parse structured response with robust parser
                insights = self._extract_bullet_points(response_text, "Key Insights")
                recommendations = self._extract_bullet_points(response_text, "Actionable Recommendations")
                
                return AgentContribution(
                    expertId=expert.id,
                    expertName=expert.name,
                    analysis=response_text,
                    keyInsights=insights,
                    recommendations=recommendations
                )
            
            except asyncio.TimeoutError:
                raise Exception(f"{expert.name} analysis timed out after 60 seconds")
            except Exception as e:
                raise Exception(f"{expert.name} analysis failed: {str(e)}")
    
    async def _synthesize_consensus(
        self,
        problem: str,
        contributions: List[AgentContribution],
        research_findings: Optional[str]
    ) -> str:
        """
        Synthesize a unified consensus from all expert contributions.
        
        Uses a meta-analyst prompt to find common ground and synthesize
        insights from all experts.
        """
        # Build synthesis prompt with all contributions
        contributions_text = ""
        for contrib in contributions:
            contributions_text += f"\n\n---\n**{contrib.expertName}:**\n"
            # For conversational responses, use full analysis instead of structured insights/recommendations
            if contrib.keyInsights or contrib.recommendations:
                # Structured response (legacy format)
                contributions_text += f"\n**Key Insights:**\n"
                for insight in contrib.keyInsights:
                    contributions_text += f"- {insight}\n"
                contributions_text += f"\n**Recommendations:**\n"
                for rec in contrib.recommendations:
                    contributions_text += f"- {rec}\n"
            else:
                # Conversational response - use full analysis (truncate to 800 chars for synthesis)
                contributions_text += contrib.analysis[:800] + ("..." if len(contrib.analysis) > 800 else "") + "\n"
        
        synthesis_prompt = f"""Você é um moderador experiente sintetizando uma CONVERSA ROUNDTABLE entre especialistas.

**Pergunta discutida:**
{problem}

**CONVERSA que rolou (experts dialogando entre si):**
{contributions_text}

**Sua tarefa - CONCLUSÃO DE REUNIÃO ROUNDTABLE:**
Você acabou de moderar uma mesa redonda onde os especialistas CONVERSARAM ENTRE SI, comentando e construindo em cima das falas dos colegas.

Agora sintetize essa CONVERSA, destacando:
1. **Pontos de CONCORDÂNCIA** - onde experts concordaram e reforçaram ideias uns dos outros
2. **Pontos de DIVERGÊNCIA** - onde houve perspectivas diferentes e complementares
3. **EVOLUÇÃO do pensamento** - como a conversa foi construindo consenso ao longo do diálogo

FORMATO:
- **Tom**: Natural e coloquial, como "Ok, rolou uma conversa interessante aqui..."
- **Tamanho**: 2-3 parágrafos curtos (máximo 150-200 palavras)
- **Estrutura**: Informal, fluxo de conversa, não use números ou bullets
- **Foco**: Sintetize a CONVERSA, não apenas liste opiniões paralelas

EXEMPLOS de como começar:
- "Olha, foi interessante ver que todo mundo convergiu em..."
- "Teve uma discussão boa aqui - o [Nome] começou falando de X, aí o/a [Nome] complementou com Y..."
- "O consenso foi se formando: primeiro [Nome] sugeriu X, depois [Nome] reforçou..."
- "Rolou divergência em um ponto - [Nome] defendeu X enquanto [Nome] prefere Y, mas..."

**Evite:**
- Estruturas numeradas (1., 2., 3.)
- Bullets extensos
- Tratar como opiniões isoladas ("Expert 1 disse isso, Expert 2 disse aquilo")
- Tom formal ou de apresentação
- Mais de 200 palavras

Sintetize o DIÁLOGO que rolou, mostrando como os experts conversaram entre si."""
        
        # Call Claude for synthesis (using a neutral system prompt) with timeout
        try:
            response = await asyncio.wait_for(
                self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,  # Reduced from 2500 for concise synthesis
                    system="Você é um moderador experiente de reuniões de consultoria. Fale em português brasileiro natural e coloquial.",
                    messages=[{
                        "role": "user",
                        "content": synthesis_prompt
                    }]
                ),
                timeout=60.0  # 60 second timeout for synthesis
            )
            
            # Extract consensus text (handle TextBlock type)
            consensus_text = ""
            for block in response.content:
                if block.type == "text":
                    consensus_text = block.text  # type: ignore
                    break
            
            return consensus_text
            
        except asyncio.TimeoutError:
            # Fallback synthesis if API times out
            return f"""**Síntese do Conselho (Gerada Automaticamente)**

Aguardo as contribuições dos especialistas para realizar a síntese estratégica.

**Contribuições Recebidas:**
{len(contributions)} especialistas compartilharam suas análises sobre: {problem}

Para continuar, por favor reformule sua pergunta ou aguarde um momento."""
        except Exception as e:
            # Fallback synthesis on any error
            print(f"[Synthesis Error] {str(e)}")
            return f"""**Síntese Parcial**

Não foi possível completar a síntese completa no momento. Aqui está um resumo das contribuições:

{len(contributions)} especialistas analisaram: {problem}

Por favor, tente reformular sua pergunta."""
    
    def _build_enhanced_system_prompt(self, expert: Expert, user_id: str) -> str:
        """
        Build expert system prompt enriched with tool instructions
        
        Args:
            expert: Expert model with systemPrompt
            user_id: User identifier for personalization
        
        Returns:
            Enhanced system prompt with tool capabilities
        """
        enhanced = expert.systemPrompt
        
        # Add tool instructions if tools are available
        if self.tools:
            enhanced += "\n\n## AVAILABLE CAPABILITIES\n"
            enhanced += "You have access to the following research and personalization capabilities:\n\n"
            
            for tool_name, tool in self.tools.items():
                if hasattr(tool, 'get_prompt_instruction'):
                    enhanced += f"### {tool_name}\n"
                    enhanced += tool.get_prompt_instruction() + "\n\n"
            
            enhanced += "\nUse these capabilities to enrich your analysis with contextual data, user preferences, and relevant case studies.\n"
        
        return enhanced
    
    def _extract_bullet_points(self, text: str, section_name: str) -> List[str]:
        """
        Extract bullet points from a markdown section with robust parsing.
        Handles various markdown formats, case variations, and punctuation differences.
        """
        import re
        
        points = []
        
        # Normalize section name for matching (case-insensitive, remove special chars)
        normalized_section = re.sub(r'[^\w\s]', '', section_name.lower())
        
        # Build regex pattern to find section header (case-insensitive)
        # Matches: ## Key Insights, **Key Insights:**, Key Insights, etc.
        pattern = r'(?:^|\n)\s*(?:#{1,3}\s+|\*\*)?(?P<header>' + re.escape(normalized_section) + r')(?:\*\*)?:?\s*(?:\n|$)'
        
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if not match:
            # Section not found - return empty list (conversational responses don't have structured sections)
            return []
        
        # Extract text after section header until next section or end
        start_pos = match.end()
        remaining_text = text[start_pos:]
        
        # Find next section header (## or ** at line start)
        next_section = re.search(r'\n\s*(?:#{1,3}\s+|\*\*\w)', remaining_text)
        if next_section:
            section_text = remaining_text[:next_section.start()]
        else:
            section_text = remaining_text
        
        # Extract bullet points (support -, •, *, numbered lists)
        bullet_pattern = r'^\s*(?:[-•*]|\d+\.)\s+(.+)$'
        
        for line in section_text.split('\n'):
            match = re.match(bullet_pattern, line, re.MULTILINE)
            if match:
                point = match.group(1).strip()
                
                # Clean up markdown formatting
                point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)  # Remove bold
                point = re.sub(r'__(.+?)__', r'\1', point)      # Remove underline
                point = re.sub(r'\*(.+?)\*', r'\1', point)      # Remove italic
                
                # Only include substantial points (min 15 chars to avoid noise)
                if len(point) >= 15:
                    points.append(point)
        
        # Return up to 7 points, or empty list for conversational responses
        if not points:
            return []
        
        return points[:7]

# Global council orchestrator
council_orchestrator = CouncilOrchestrator()
