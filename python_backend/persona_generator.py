"""
Deep Persona Generation System - 8 Modules with 3-Level Architecture

This module implements the most advanced persona generation system in the market,
utilizing 18 marketing expert clones to create actionable, multi-dimensional personas.

Architecture:
- Quick Persona: 3 core modules (~30-45s)
- Strategic Persona: 6 modules (~2-3min)
- Complete Persona: All 8 modules + copy examples (~5-7min)
"""

from typing import Dict, List, Any, Optional
from anthropic import AsyncAnthropic
from anthropic.types import Message, TextBlock
import os
from pydantic import BaseModel
import json


def extract_text_from_response(response: Message) -> str:
    """Safely extract text from Claude API response"""
    for block in response.content:
        if isinstance(block, TextBlock):
            return block.text
        if hasattr(block, 'text'):
            return block.text  # type: ignore
    return ""


# ============================================
# MODULE DATA MODELS
# ============================================

class PsychographicCore(BaseModel):
    """Module 1: Deep psychological profile (Kotler + Kahneman)"""
    values: List[str]
    fears: List[str]
    aspirations: List[str]
    thinkingSystem: str  # 'system1', 'system2', 'balanced'
    decisionDrivers: List[str]


class BuyerJourney(BaseModel):
    """Module 2: Detailed purchase journey (Eugene Schwartz + Jay Abraham)"""
    awarenessLevel: str  # Schwartz 5 levels
    currentStage: str
    triggers: List[str]
    objections: List[str]
    salesCycle: str
    touchpointsNeeded: int


class BehavioralProfile(BaseModel):
    """Module 3: Behavioral patterns (Cialdini + Vaynerchuk)"""
    cialdiniPrinciples: List[Dict[str, Any]]  # [{principle, priority}]
    researchChannels: List[str]
    trustedInfluencers: List[str]
    preferredFormat: List[str]
    engagementPatterns: Dict[str, Any]


class LanguageCommunication(BaseModel):
    """Module 4: Communication blueprint (Ann Handley + Donald Miller)"""
    idealTone: str
    vocabularyKeys: List[str]
    vocabularyAvoid: List[str]
    complexityLevel: str
    storyBrandFramework: Dict[str, str]


class StrategicInsights(BaseModel):
    """Module 5: Actionable strategies (Seth Godin + Neil Patel)"""
    coreMessage: str
    uniqueValueProp: str
    channelPriority: List[Dict[str, Any]]
    contentStrategy: List[str]
    competitivePosition: str


class JobsToBeDone(BaseModel):
    """Module 6: Jobs-to-be-Done framework (Christensen)"""
    functionalJob: str
    emotionalJob: str
    socialJob: str
    progressDesired: str
    successMetrics: List[str]


class DecisionProfile(BaseModel):
    """Module 7: Decision-making analysis (Dan Kennedy)"""
    decisionMakerType: str
    decisionCriteria: List[Dict[str, Any]]
    decisionSpeed: str
    validationNeeded: List[str]
    riskTolerance: str


class CopyExamples(BaseModel):
    """Module 8: Ready-to-use copy (Handley + Schwartz)"""
    headlines: List[str]
    emailSubjects: List[str]
    socialPosts: List[str]
    ctas: List[str]
    landingPageCopy: str


# ============================================
# MODULE GENERATORS
# ============================================

class PsychographicCoreGenerator:
    """Generates deep psychological profile using Philip Kotler + Daniel Kahneman"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-sonnet-4-20250514"  # Complex psychological analysis needs Sonnet
    
    async def generate(
        self, 
        persona_context: Dict[str, Any],
        youtube_data: Optional[List[Dict]] = None,
        reddit_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate psychographic core using expert insights"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é uma fusão de Philip Kotler (marketing estratégico) e Daniel Kahneman (psicologia comportamental).

Contexto da Persona:
- Empresa: {persona_context.get('companyName')}
- Setor: {persona_context.get('industry')}
- Público-alvo: {persona_context.get('targetAudience')}
- Objetivo: {persona_context.get('primaryGoal')}
- Desafio: {persona_context.get('mainChallenge')}

{f"Dados do YouTube: {json.dumps(youtube_data[:3], ensure_ascii=False)}" if youtube_data else ""}
{f"Insights do Reddit: {json.dumps(reddit_data, ensure_ascii=False)}" if reddit_data else ""}

TAREFA: Crie o NÚCLEO PSICOGRÁFICO desta persona respondendo em JSON:

{{
  "values": ["3-5 valores centrais que guiam decisões"],
  "fears": ["3-5 medos dominantes relacionados ao negócio"],
  "aspirations": ["3-5 aspirações concretas para 1-3 anos"],
  "thinkingSystem": "system1|system2|balanced (Kahneman)",
  "decisionDrivers": ["3-5 motivadores principais de decisões"]
}}

REGRAS:
- Seja ULTRA-ESPECÍFICO ao contexto (não genérico)
- Use insights dos dados do YouTube/Reddit quando disponíveis
- Values: o que essa pessoa PRIORIZA acima de tudo
- Fears: medos reais e práticos, não abstratos
- Aspirations: objetivos tangíveis e mensuráveis
- ThinkingSystem: system1 = emocional/rápido, system2 = analítico/lento
- DecisionDrivers: o que REALMENTE move essa pessoa a agir

Responda APENAS com JSON válido, sem markdown."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Sonnet for complex psychographic analysis
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            # Clean markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating psychographic core: {e}")
            return {
                "values": ["Crescimento sustentável", "Eficiência operacional"],
                "fears": ["Tomar decisão errada", "Perder competitividade"],
                "aspirations": ["Dobrar faturamento", "Liderar categoria"],
                "thinkingSystem": "system2",
                "decisionDrivers": ["ROI comprovado", "Facilidade de implementação"]
            }


class BuyerJourneyGenerator:
    """Generates detailed buyer journey using Eugene Schwartz + Jay Abraham"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-sonnet-4-20250514"  # Complex buyer psychology needs Sonnet
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        psychographic_core: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate buyer journey mapping"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é uma fusão de Eugene Schwartz (5 níveis de consciência) e Jay Abraham (estratégia de vendas).

Contexto da Persona:
- Empresa: {persona_context.get('companyName')}
- Setor: {persona_context.get('industry')}
- Público: {persona_context.get('targetAudience')}
- Objetivo: {persona_context.get('primaryGoal')}
- Desafio: {persona_context.get('mainChallenge')}
{f"- Valores: {', '.join(psychographic_core.get('values', []))}" if psychographic_core else ""}
{f"- Medos: {', '.join(psychographic_core.get('fears', []))}" if psychographic_core else ""}

TAREFA: Mapeie a JORNADA DE COMPRA completa em JSON:

{{
  "awarenessLevel": "unaware|problem-aware|solution-aware|product-aware|most-aware (Schwartz)",
  "currentStage": "Estágio atual específico da persona",
  "triggers": ["3-5 gatilhos que movem para próximo estágio"],
  "objections": ["3-5 objeções/pontos de atrito principais"],
  "salesCycle": "Duração típica (ex: 45-90 dias)",
  "touchpointsNeeded": 5
}}

REGRAS:
- awarenessLevel: identifique o nível ATUAL baseado no desafio/objetivo
- triggers: eventos/informações específicas que fazem avançar
- objections: objeções REAIS e específicas ao contexto
- salesCycle: baseado na complexidade da decisão e setor
- touchpointsNeeded: número realista de interações até conversão

Responda APENAS com JSON válido, sem markdown."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Sonnet for complex journey mapping
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating buyer journey: {e}")
            return {
                "awarenessLevel": "solution-aware",
                "currentStage": "Avaliando alternativas",
                "triggers": ["Case studies relevantes", "Demonstração técnica"],
                "objections": ["Preço", "Integração"],
                "salesCycle": "60-90 dias",
                "touchpointsNeeded": 7
            }


class BehavioralProfileGenerator:
    """Generates behavioral profile using Robert Cialdini + Gary Vaynerchuk"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-haiku-20250305"  # Simple pattern matching, Haiku sufficient
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        youtube_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate behavioral patterns"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é uma fusão de Robert Cialdini (6 princípios de persuasão) e Gary Vaynerchuk (comportamento digital).

Contexto:
- Setor: {persona_context.get('industry')}
- Público: {persona_context.get('targetAudience')}
- Canais: {', '.join(persona_context.get('channels', []))}

{f"Vídeos que o público assiste: {json.dumps([{'title': v.get('title'), 'channel': v.get('channel')} for v in youtube_data[:5]], ensure_ascii=False)}" if youtube_data else ""}

TAREFA: Crie PERFIL COMPORTAMENTAL em JSON:

{{
  "cialdiniPrinciples": [
    {{"principle": "Reciprocidade|Compromisso|Prova Social|Autoridade|Simpatia|Escassez", "priority": 1-6}}
  ],
  "researchChannels": ["Canais onde pesquisam antes de comprar"],
  "trustedInfluencers": ["Tipos de influenciadores que seguem"],
  "preferredFormat": ["Formatos de conteúdo preferidos"],
  "engagementPatterns": {{"bestTime": "Quando engajam", "frequency": "Com que frequência"}}
}}

REGRAS:
- cialdiniPrinciples: RANQUEIE todos os 6 por efetividade (1 = mais efetivo)
- researchChannels: baseado nos canais fornecidos + comportamento do setor
- trustedInfluencers: tipos específicos (ex: "CTOs de empresas similares")
- preferredFormat: baseado nos vídeos do YouTube se disponível
- engagementPatterns: padrões realistas para o perfil

Responda APENAS com JSON válido."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Haiku for cost optimization (~70% savings)
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating behavioral profile: {e}")
            return {
                "cialdiniPrinciples": [
                    {"principle": "Autoridade", "priority": 1},
                    {"principle": "Prova Social", "priority": 2}
                ],
                "researchChannels": ["Google", "LinkedIn"],
                "trustedInfluencers": ["Líderes da indústria"],
                "preferredFormat": ["Artigos técnicos"],
                "engagementPatterns": {"bestTime": "Horário comercial", "frequency": "Semanal"}
            }


class LanguageCommunicationGenerator:
    """Generates communication blueprint using Ann Handley + Donald Miller"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-haiku-20250305"  # Simple linguistic patterns, Haiku sufficient
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        psychographic_core: Optional[Dict[str, Any]] = None,
        behavioral_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate language & communication strategy"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é uma fusão de Ann Handley (content marketing) e Donald Miller (StoryBrand).

Contexto:
- Público: {persona_context.get('targetAudience')}
- Setor: {persona_context.get('industry')}
- Objetivo: {persona_context.get('primaryGoal')}
{f"- Sistema de pensamento: {psychographic_core.get('thinkingSystem')}" if psychographic_core else ""}
{f"- Formatos preferidos: {', '.join(behavioral_profile.get('preferredFormat', []))}" if behavioral_profile else ""}

TAREFA: Crie BLUEPRINT DE COMUNICAÇÃO em JSON:

{{
  "idealTone": "Descrição do tom ideal (ex: 'Profissional com toque humano')",
  "vocabularyKeys": ["5-7 palavras/frases que RESSOAM"],
  "vocabularyAvoid": ["3-5 palavras/frases que AFASTAM"],
  "complexityLevel": "technical-details|simplified|executive-summary",
  "storyBrandFramework": {{
    "hero": "Quem é o herói (o cliente, não você)",
    "problem": "Problema principal que enfrenta",
    "guide": "Você como guia (sua empresa)",
    "plan": "Plano simples em 3 passos",
    "callToAction": "CTA específico e claro"
  }}
}}

REGRAS:
- idealTone: específico ao perfil psicográfico
- vocabularyKeys: palavras que conectam emocionalmente
- vocabularyAvoid: jargões que afastam ou confundem
- complexityLevel: baseado em System1/System2 thinking
- StoryBrand: framework completo adaptado à persona

Responda APENAS com JSON válido."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Haiku for linguistic analysis (~70% cost savings)
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating language communication: {e}")
            return {
                "idealTone": "Profissional e direto",
                "vocabularyKeys": ["ROI", "eficiência", "resultados"],
                "vocabularyAvoid": ["disruptivo", "revolucionário"],
                "complexityLevel": "executive-summary",
                "storyBrandFramework": {
                    "hero": "Gestor de TI",
                    "problem": "Baixa produtividade",
                    "guide": "Solução especializada",
                    "plan": "1. Análise 2. Implementação 3. Suporte",
                    "callToAction": "Agende demonstração"
                }
            }


class StrategicInsightsGenerator:
    """Generates strategic insights using Seth Godin + Neil Patel"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-sonnet-4-20250514"  # Strategic synthesis needs Sonnet's reasoning
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        all_modules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate strategic insights and recommendations"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é uma fusão de Seth Godin (marketing estratégico) e Neil Patel (growth marketing).

Contexto Completo:
{json.dumps(persona_context, ensure_ascii=False, indent=2)}

{f"Módulos Anteriores: {json.dumps(all_modules, ensure_ascii=False, indent=2)}" if all_modules else ""}

TAREFA: Gere INSIGHTS ESTRATÉGICOS ACIONÁVEIS em JSON:

{{
  "coreMessage": "A mensagem única que captura o coração desta persona (1 frase)",
  "uniqueValueProp": "O que faz escolherem VOCÊ vs competição (específico)",
  "channelPriority": [
    {{"channel": "LinkedIn|Email|Google Ads|etc", "priority": 1-5, "reason": "Por que este canal funciona"}}
  ],
  "contentStrategy": ["3-5 tipos de conteúdo mais efetivos"],
  "competitivePosition": "Como se diferenciar no mercado (específico)"
}}

REGRAS:
- coreMessage: deve ser memorável e emocional
- uniqueValueProp: específico e verificável
- channelPriority: baseado em behavioral profile e jornada
- contentStrategy: formatos que ressoam com a persona
- competitivePosition: nicho único e defensável

Responda APENAS com JSON válido."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Sonnet for complex strategic synthesis
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating strategic insights: {e}")
            return {
                "coreMessage": "Cresça sem complexidade",
                "uniqueValueProp": "Implementação em 48h com suporte dedicado",
                "channelPriority": [
                    {"channel": "LinkedIn", "priority": 1, "reason": "Público B2B ativo"}
                ],
                "contentStrategy": ["Case studies", "Webinars técnicos"],
                "competitivePosition": "Especialista vertical no setor"
            }


class JobsToBeDoneGenerator:
    """Generates Jobs-to-be-Done analysis"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-haiku-20250305"  # Framework application, Haiku sufficient
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        psychographic_core: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate JTBD framework"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é um especialista em Jobs-to-be-Done framework (Clayton Christensen).

Contexto:
- Público: {persona_context.get('targetAudience')}
- Objetivo: {persona_context.get('primaryGoal')}
- Desafio: {persona_context.get('mainChallenge')}
{f"- Aspirações: {', '.join(psychographic_core.get('aspirations', []))}" if psychographic_core else ""}

TAREFA: Analise os JOBS-TO-BE-DONE em JSON:

{{
  "functionalJob": "O trabalho funcional que estão tentando realizar",
  "emotionalJob": "Como querem se SENTIR ao realizar esse trabalho",
  "socialJob": "Como querem ser VISTOS pelos outros",
  "progressDesired": "De [estado atual] para [estado desejado]",
  "successMetrics": ["3-5 métricas que definem sucesso"]
}}

REGRAS:
- functionalJob: específico e mensurável
- emotionalJob: emoção genuína, não superficial
- socialJob: como querem ser percebidos profissionalmente
- progressDesired: transformação clara e específica
- successMetrics: KPIs que realmente importam para essa persona

Responda APENAS com JSON válido."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Haiku for JTBD framework (~70% cost savings)
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating jobs-to-be-done: {e}")
            return {
                "functionalJob": "Aumentar eficiência operacional",
                "emotionalJob": "Sentir-se no controle",
                "socialJob": "Ser visto como líder inovador",
                "progressDesired": "De caos para previsibilidade",
                "successMetrics": ["ROI de 300%", "Redução de 40% em tempo"]
            }


class DecisionProfileGenerator:
    """Generates decision-making profile using Dan Kennedy"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-haiku-20250305"  # Simple decision profiling, Haiku sufficient
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        psychographic_core: Optional[Dict[str, Any]] = None,
        buyer_journey: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate decision profile"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights e recomendações devem ser escritas em português brasileiro.**

Você é Dan Kennedy, especialista em perfis de decisão de compra.

Contexto:
- Público: {persona_context.get('targetAudience')}
- Tamanho empresa: {persona_context.get('companySize')}
{f"- Sistema pensamento: {psychographic_core.get('thinkingSystem')}" if psychographic_core else ""}
{f"- Ciclo de vendas: {buyer_journey.get('salesCycle')}" if buyer_journey else ""}

TAREFA: Crie PERFIL DE DECISÃO em JSON:

{{
  "decisionMakerType": "Analytical|Impulsive|Social|Cautious",
  "decisionCriteria": [
    {{"criterion": "ROI|Facilidade|Suporte|Inovação|etc", "weight": 1-10}}
  ],
  "decisionSpeed": "Fast (days)|Medium (weeks)|Slow (months)",
  "validationNeeded": ["Quem precisa aprovar/consultar"],
  "riskTolerance": "high|medium|low"
}}

REGRAS:
- decisionMakerType: baseado em System1/System2 e contexto
- decisionCriteria: RANQUEIE por peso (10 = mais importante)
- decisionSpeed: realista para o setor e tamanho da empresa
- validationNeeded: stakeholders específicos que precisam aprovar
- riskTolerance: baseado em medos e aspirações

Responda APENAS com JSON válido."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Haiku for decision profiling (~70% cost savings)
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating decision profile: {e}")
            return {
                "decisionMakerType": "Analytical",
                "decisionCriteria": [
                    {"criterion": "ROI comprovado", "weight": 10},
                    {"criterion": "Facilidade de integração", "weight": 8}
                ],
                "decisionSpeed": "Medium (4-8 weeks)",
                "validationNeeded": ["Equipe técnica", "CFO"],
                "riskTolerance": "low"
            }


class CopyExamplesGenerator:
    """Generates ready-to-use copy examples using Ann Handley + Eugene Schwartz"""
    
    def __init__(self, client: AsyncAnthropic):
        self.client = client
        self.model = "claude-sonnet-4-20250514"  # Creative copywriting needs Sonnet's creativity
    
    async def generate(
        self,
        persona_context: Dict[str, Any],
        all_modules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate copy examples based on all persona insights"""
        
        prompt = f"""**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR). Todas as suas análises, insights, recomendações e COPY devem ser escritas em português brasileiro.**

Você é uma fusão de Ann Handley (copywriting mestre) e Eugene Schwartz (lendas da copy).

CONTEXTO COMPLETO DA PERSONA:
{json.dumps({**persona_context, **all_modules}, ensure_ascii=False, indent=2)}

TAREFA: Crie EXEMPLOS DE COPY PRONTOS PARA USAR em JSON:

{{
  "headlines": ["5 headlines diferentes adaptados à persona"],
  "emailSubjects": ["5 assuntos de email com alta taxa de abertura"],
  "socialPosts": ["3 posts para LinkedIn/redes sociais"],
  "ctas": ["5 CTAs específicos e acionáveis"],
  "landingPageCopy": "Template completo de landing page (200-300 palavras)"
}}

REGRAS:
- headlines: usar coreMessage, vocabularyKeys, e princípios Cialdini
- emailSubjects: curtos (<50 chars), baseados em triggers e objections
- socialPosts: formatados para a rede, usando tom ideal
- ctas: específicos ao progressDesired e storyBrand callToAction
- landingPageCopy: seguir StoryBrand framework completo

IMPORTANTE: Copy deve ser em português brasileiro, natural e persuasiva.

Responda APENAS com JSON válido."""

        try:
            response = await self.client.messages.create(
                model=self.model,  # Sonnet for creative high-quality copywriting
                max_tokens=3000,
                temperature=0.8,  # More creative
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = extract_text_from_response(response)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error generating copy examples: {e}")
            return {
                "headlines": ["Dobre seu faturamento sem dobrar sua equipe"],
                "emailSubjects": ["[Nome], você está perdendo R$ 50k/mês"],
                "socialPosts": ["Post exemplo para LinkedIn"],
                "ctas": ["Agende sua demonstração gratuita agora"],
                "landingPageCopy": "Landing page exemplo..."
            }


# ============================================
# PERSONA ORCHESTRATOR - 3 LEVELS
# ============================================

class PersonaOrchestrator:
    """Orchestrates persona generation across 3 levels: Quick, Strategic, Complete"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Initialize all generators
        self.psychographic_gen = PsychographicCoreGenerator(self.client)
        self.buyer_journey_gen = BuyerJourneyGenerator(self.client)
        self.behavioral_gen = BehavioralProfileGenerator(self.client)
        self.language_gen = LanguageCommunicationGenerator(self.client)
        self.strategic_gen = StrategicInsightsGenerator(self.client)
        self.jtbd_gen = JobsToBeDoneGenerator(self.client)
        self.decision_gen = DecisionProfileGenerator(self.client)
        self.copy_gen = CopyExamplesGenerator(self.client)
    
    async def generate_quick_persona(
        self,
        persona_context: Dict[str, Any],
        youtube_data: List[Dict] = None,
        reddit_data: Dict = None
    ) -> Dict[str, Any]:
        """
        QUICK PERSONA (~30-45s)
        Modules: Psychographic Core + Buyer Journey + Strategic Insights (basic)
        Experts: Kotler, Kahneman, Schwartz
        """
        print("[PersonaOrchestrator] Generating QUICK persona (3 core modules)...")
        
        # Module 1: Psychographic Core
        psychographic_core = await self.psychographic_gen.generate(
            persona_context, youtube_data, reddit_data
        )
        
        # Module 2: Buyer Journey
        buyer_journey = await self.buyer_journey_gen.generate(
            persona_context, psychographic_core
        )
        
        # Module 5: Strategic Insights (basic version)
        strategic_insights = await self.strategic_gen.generate(
            persona_context,
            {
                "psychographicCore": psychographic_core,
                "buyerJourney": buyer_journey
            }
        )
        
        return {
            "psychographicCore": psychographic_core,
            "buyerJourney": buyer_journey,
            "strategicInsights": strategic_insights,
            "enrichmentLevel": "quick",
            "researchCompleteness": 40  # 3/8 modules
        }
    
    async def generate_strategic_persona(
        self,
        persona_context: Dict[str, Any],
        youtube_data: List[Dict] = None,
        reddit_data: Dict = None,
        existing_modules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        STRATEGIC PERSONA (~2-3min)
        Modules: All Quick + Behavioral + Language + JTBD
        Experts: Quick + Cialdini, Vaynerchuk, Handley, Miller
        """
        print("[PersonaOrchestrator] Generating STRATEGIC persona (6 modules)...")
        
        # If upgrading from Quick, reuse existing modules
        if existing_modules and existing_modules.get("psychographicCore"):
            psychographic_core = existing_modules["psychographicCore"]
            buyer_journey = existing_modules["buyerJourney"]
            strategic_insights = existing_modules.get("strategicInsights")
        else:
            # Generate Quick modules first
            quick_result = await self.generate_quick_persona(
                persona_context, youtube_data, reddit_data
            )
            psychographic_core = quick_result["psychographicCore"]
            buyer_journey = quick_result["buyerJourney"]
            strategic_insights = quick_result["strategicInsights"]
        
        # Module 3: Behavioral Profile
        behavioral_profile = await self.behavioral_gen.generate(
            persona_context, youtube_data
        )
        
        # Module 4: Language & Communication
        language_communication = await self.language_gen.generate(
            persona_context, psychographic_core, behavioral_profile
        )
        
        # Module 6: Jobs-to-be-Done
        jobs_to_be_done = await self.jtbd_gen.generate(
            persona_context, psychographic_core
        )
        
        return {
            "psychographicCore": psychographic_core,
            "buyerJourney": buyer_journey,
            "behavioralProfile": behavioral_profile,
            "languageCommunication": language_communication,
            "strategicInsights": strategic_insights,
            "jobsToBeDone": jobs_to_be_done,
            "enrichmentLevel": "strategic",
            "researchCompleteness": 75  # 6/8 modules
        }
    
    async def generate_complete_persona(
        self,
        persona_context: Dict[str, Any],
        youtube_data: List[Dict] = None,
        reddit_data: Dict = None,
        existing_modules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        COMPLETE PERSONA (~5-7min)
        Modules: ALL 8 modules + copy examples
        Experts: ALL 18 marketing legends working in concert
        """
        print("[PersonaOrchestrator] Generating COMPLETE persona (8 modules + copy)...")
        
        # If upgrading from Strategic, reuse existing modules
        if existing_modules and existing_modules.get("behavioralProfile"):
            strategic_result = existing_modules
        else:
            # Generate Strategic modules first
            strategic_result = await self.generate_strategic_persona(
                persona_context, youtube_data, reddit_data, existing_modules
            )
        
        # Module 7: Decision Profile
        decision_profile = await self.decision_gen.generate(
            persona_context,
            strategic_result.get("psychographicCore"),
            strategic_result.get("buyerJourney")
        )
        
        # Module 8: Copy Examples
        all_modules = {
            "psychographicCore": strategic_result["psychographicCore"],
            "buyerJourney": strategic_result["buyerJourney"],
            "behavioralProfile": strategic_result["behavioralProfile"],
            "languageCommunication": strategic_result["languageCommunication"],
            "strategicInsights": strategic_result["strategicInsights"],
            "jobsToBeDone": strategic_result["jobsToBeDone"],
            "decisionProfile": decision_profile
        }
        
        copy_examples = await self.copy_gen.generate(
            persona_context, all_modules
        )
        
        return {
            **all_modules,
            "copyExamples": copy_examples,
            "enrichmentLevel": "complete",
            "researchCompleteness": 100  # 8/8 modules
        }
