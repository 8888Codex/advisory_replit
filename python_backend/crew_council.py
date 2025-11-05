"""
CrewAI Council Orchestration - Multi-Expert Collaborative Analysis
"""
import uuid
import asyncio
from typing import List, Optional, Dict
from anthropic import AsyncAnthropic
import os
from models import Expert, BusinessProfile, CouncilAnalysis, AgentContribution
from perplexity_research import perplexity_research

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
                profile=profile
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
        profile: Optional[BusinessProfile]
    ) -> AgentContribution:
        """
        Get analysis from a single expert using their cognitive clone.
        Uses semaphore to limit concurrent API calls and prevent rate limiting.
        
        Returns:
            AgentContribution with expert's unique perspective
        """
        async with self.semaphore:
            # Build context-rich prompt
            context_parts = []
            
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
            
            user_message = f"""{context}

**Problem/Question:**
{problem}

**Your Task:**
As {expert.name}, provide your expert analysis addressing this problem. Structure your response as:

1. **Core Analysis**: Your unique perspective on the problem (2-3 paragraphs)
2. **Key Insights**: 3-5 critical insights (bullet points)
3. **Actionable Recommendations**: 3-5 specific, tactical recommendations (bullet points)

Draw on your signature frameworks, methodologies, and philosophies. Be authentic to your cognitive patterns and communication style."""
            
            # Call Claude with expert's system prompt (with timeout)
            try:
                response = await asyncio.wait_for(
                    self.anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=3000,
                        system=expert.systemPrompt,
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
            contributions_text += f"\n\n---\n**{contrib.expertName}'s Analysis:**\n"
            contributions_text += f"\n**Key Insights:**\n"
            for insight in contrib.keyInsights:
                contributions_text += f"- {insight}\n"
            contributions_text += f"\n**Recommendations:**\n"
            for rec in contrib.recommendations:
                contributions_text += f"- {rec}\n"
        
        synthesis_prompt = f"""Você é um sintetizador estratégico analisando contribuições de um conselho de especialistas lendários em marketing.

**Problema Analisado:**
{problem}

**Contribuições do Conselho de Especialistas:**
{contributions_text}

**Sua Tarefa:**
Sintetize um resumo executivo unificado que:

1. **Estratégia Consensual** (1-2 parágrafos): Onde todos os especialistas concordam? Qual é a direção estratégica central?

2. **Recomendações Integradas** (5-7 pontos): Combine e priorize as recomendações mais impactantes de todos os especialistas. Atribua táticas específicas aos especialistas quando relevante (ex: "Como Kotler enfatizou...").

3. **Tensões-Chave** (se houver): Onde os especialistas discordam ou enfatizam prioridades diferentes? Apresente essas como escolhas estratégicas, não contradições.

4. **Roadmap de Implementação** (3-5 passos): Sintetize uma sequência prática de ações baseada nas recomendações de todos os especialistas.

Seja conciso, acionável e autoritativo. Este é um briefing executivo."""
        
        # Call Claude for synthesis (using a neutral system prompt)
        response = await self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            system="You are an expert strategic analyst specializing in synthesizing insights from multiple domain experts into clear, actionable recommendations.\n\n**INSTRUÇÃO OBRIGATÓRIA: Você DEVE escrever SEMPRE em português brasileiro (PT-BR), independentemente do idioma em que as contribuições dos experts foram escritas. Todo o seu consenso, recomendações integradas, roadmap de implementação e quaisquer citações ou referências devem ser escritos ou traduzidos para português brasileiro. Use nomes traduzidos de conceitos e livros quando existirem. Se citar frases em inglês, forneça também a tradução.**",
            messages=[{
                "role": "user",
                "content": synthesis_prompt
            }]
        )
        
        # Extract consensus text (handle TextBlock type)
        consensus_text = ""
        for block in response.content:
            if block.type == "text":
                consensus_text = block.text  # type: ignore
                break
        
        return consensus_text
    
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
            # Fallback: section not found
            return [f"(See full analysis for {section_name})"]
        
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
        
        # Return up to 7 points, or fallback message
        if not points:
            return [f"(See full analysis for {section_name})"]
        
        return points[:7]

# Global council orchestrator
council_orchestrator = CouncilOrchestrator()
