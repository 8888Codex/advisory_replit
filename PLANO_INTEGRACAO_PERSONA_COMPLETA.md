# Plano: Integração Completa de Persona em Todo o Sistema

**Data:** 10 de novembro de 2025  
**Status:** 🔄 EM PLANEJAMENTO

---

## OBJETIVO

Expandir a integração de persona para que **todos os especialistas e conselhos** tenham acesso completo aos dados enriquecidos da persona ativa do usuário, permitindo:

- ✅ Conselhos ultra-personalizados baseados no público-alvo real
- ✅ Estratégias específicas para a indústria e desafios do cliente
- ✅ Uso de linguagem autêntica do público (Reddit insights)
- ✅ Alinhamento com Jobs-to-be-Done e Buyer Journey

---

## SITUAÇÃO ATUAL

### O que JÁ está integrado ✅

**Chat 1:1 (linhas 3028-3075 em main.py):**
```python
persona = await storage.get_user_persona(user_id)
if persona:
    persona_context = """
    [CONTEXTO DO NEGÓCIO DO CLIENTE]:
    • Empresa: {companyName}
    • Indústria: {industry}
    • Público-alvo: {targetAudience}
    • Objetivo: {primaryGoal}
    • Desafio: {mainChallenge}
    """
    enriched_system_prompt = expert.systemPrompt + persona_context
```

**Council Chat Follow-up (linhas 4281-4292, 4421-4454):**
```python
persona = await storage.get_user_persona(user_id)
context = await _build_council_context(analysis, history, message, persona)
```

### O que FALTA ❌

1. **Dados Enriquecidos Não São Usados:**
   - psychographicCore (valores, motivações, medos)
   - behavioralProfile (comportamento online, padrões de compra)
   - buyerJourney (5 estágios: awareness → advocacy)
   - jobsToBeDone (functional, emotional, social jobs)
   - redditInsights (sentiment, trending topics, communities)
   - strategicInsights (oportunidades, ameaças, recommendations)
   - languageCommunication (vocabulário, tom, estilo)
   - decisionProfile (critérios de decisão)

2. **Council Analyze Inicial Não Usa Persona:**
   - `/api/council/analyze` (não-streaming)
   - `/api/council/analyze-stream` (streaming inicial)
   - Apenas o follow-up (`/council/chat/{session_id}/stream`) usa

3. **Recomendações de Experts Não Usam Persona:**
   - `/api/recommend-experts` poderia recomendar experts mais alinhados

---

## FUNCIONALIDADES A IMPLEMENTAR

### FASE 1: Expandir Contexto da Persona (PRIORIDADE ALTA)

**Arquivo:** `python_backend/main.py`

**Função para criar:** `_build_enriched_persona_context(persona)`

```python
def _build_enriched_persona_context(persona: UserPersona) -> str:
    """
    Build comprehensive persona context including all enriched data.
    Returns formatted string to inject in system prompts.
    """
    context = f"""
---
[PERSONA INTELLIGENCE HUB - Público-Alvo Detalhado]:

📊 DADOS BÁSICOS:
• Empresa: {persona.companyName}
• Indústria: {persona.industry}
• Tamanho: {persona.companySize}
• Público-alvo: {persona.targetAudience}
• Objetivo Principal: {persona.primaryGoal}
• Desafio Principal: {persona.mainChallenge}

"""
    
    # Reddit Insights (se disponível)
    if persona.redditInsights:
        context += """
🌐 REDDIT INSIGHTS:
• Comunidades: {communities}
• Sentiment: {sentiment} ({summary})
• Trending Topics: {topics}
• Pain Points do Reddit: {painPoints}
• Language Autêntica: {language}

"""
    
    # Psychographic Core
    if persona.psychographicCore:
        context += """
🧠 CORE PSICOGRÁFICO:
• Valores: {values}
• Motivações: {motivations}
• Medos: {fears}
• Aspirações: {aspirations}

"""
    
    # Jobs-to-be-Done
    if persona.jobsToBeDone:
        context += """
🎯 JOBS-TO-BE-DONE:
Functional Jobs: {functionalJobs}
Emotional Jobs: {emotionalJobs}
Social Jobs: {socialJobs}
Success Criteria: {successCriteria}

"""
    
    # Buyer Journey
    if persona.buyerJourney:
        context += """
🛒 BUYER JOURNEY:
• Awareness: {awareness}
• Consideration: {consideration}
• Decision: {decision}
• Retention: {retention}
• Advocacy: {advocacy}

"""
    
    # Strategic Insights
    if persona.strategicInsights:
        context += """
💡 STRATEGIC INSIGHTS:
• Oportunidades: {opportunities}
• Quick Wins: {quickWins}
• Recomendações: {recommendations}

"""
    
    context += """
---
INSTRUÇÃO CRÍTICA: Use TODOS esses dados da persona para:
1. Falar a LINGUAGEM AUTÊNTICA do público (Reddit insights)
2. Endereçar os JOBS-TO-BE-DONE específicos
3. Considerar o estágio da BUYER JOURNEY
4. Alinhar com os VALORES e MOTIVAÇÕES psicográficas
5. Aproveitar OPORTUNIDADES estratégicas identificadas

NÃO mencione que tem acesso à persona - simplesmente demonstre através de recomendações ultra-personalizadas.
---
"""
    
    return context
```

**Usar em 3 lugares:**
1. Chat 1:1 (linha 3033)
2. Council Analyze Inicial (linhas 3838-3856)
3. Council Chat Follow-up (linha 4432)

### FASE 2: Integrar no Council Analyze Inicial

**Arquivo:** `python_backend/main.py` (função `create_council_analysis`)

**Antes:**
```python
# Get user's business profile (optional)
profile = await storage.get_business_profile(user_id)

# Run council analysis
analysis = await council_orchestrator.analyze(
    problem=data.problem,
    experts=experts,
    profile=profile,
    user_id=user_id
)
```

**Depois:**
```python
# Get user's business profile (optional)
profile = await storage.get_business_profile(user_id)

# Get user's persona for deep context (PRIORITY over business profile)
persona = await storage.get_user_persona(user_id)

# Run council analysis with persona context
analysis = await council_orchestrator.analyze(
    problem=data.problem,
    experts=experts,
    profile=profile,
    user_id=user_id,
    persona=persona  # NEW
)
```

### FASE 3: Atualizar CouncilOrchestrator

**Arquivo:** `python_backend/crew_council.py`

**Modificar método `analyze()`:**
```python
async def analyze(
    self,
    problem: str,
    experts: List[Expert],
    profile: Optional[BusinessProfile] = None,
    user_id: str = "demo_user",
    persona: Optional[UserPersona] = None  # NEW
) -> CouncilAnalysis:
```

**No loop de experts:**
```python
contribution = await self._get_expert_analysis(
    expert=expert,
    problem=problem,
    research_findings=research_findings,
    profile=profile,
    user_id=user_id,
    user_context=user_context,
    colleague_contributions=current_round_contributions,
    persona=persona  # NEW - passa para cada expert
)
```

**Atualizar `_get_expert_analysis()`:**
```python
async def _get_expert_analysis(
    self,
    expert: Expert,
    problem: str,
    research_findings: Optional[str],
    profile: Optional[BusinessProfile],
    user_id: str = "demo_user",
    user_context: Optional[Dict[str, Any]] = None,
    colleague_contributions: Optional[List[Dict[str, str]]] = None,
    persona: Optional[UserPersona] = None  # NEW
) -> AgentContribution:
    
    # Build enriched prompt with persona
    if persona:
        persona_context = _build_enriched_persona_context(persona)
        enriched_prompt = expert.systemPrompt + persona_context
    else:
        enriched_prompt = expert.systemPrompt
```

### FASE 4: Melhorar Recomendações de Experts (BONUS)

**Endpoint:** `/api/recommend-experts`

**Adicionar:**
```python
# Get persona to recommend experts aligned with target audience
persona = await storage.get_user_persona("default_user")

if persona:
    # Add persona context to Claude analysis
    analysis_prompt += f"""
    
CONTEXTO DA PERSONA DO CLIENTE:
• Público-alvo: {persona.targetAudience}
• Indústria: {persona.industry}
• Objetivo: {persona.primaryGoal}

Recomende especialistas que sejam ESPECIALMENTE relevantes para este público e indústria.
"""
```

---

## BENEFÍCIOS ESPERADOS

### Para o Usuário:
- 🎯 **Conselhos ultra-personalizados** (não genéricos)
- 💬 **Linguagem alinhada** com seu público-alvo
- 🎨 **Estratégias específicas** para sua indústria
- 🚀 **Recomendações acionáveis** baseadas em dados reais
- 📊 **ROI maior** (conselhos mais relevantes)

### Para o Sistema:
- 🧠 **Diferencial competitivo** único
- 🔗 **Persona e Council integrados** (não silos)
- 📈 **Enriquecimento tem valor** (dados são usados)
- ✨ **UX premium** (personalização total)

---

## EXEMPLO DE DIFERENÇA

### ANTES (sem persona):
```
Usuário: "Como aumentar vendas?"
Dan Kennedy: "Faça marketing de resposta direta, 
teste headlines, meça ROI..." [genérico]
```

### DEPOIS (com persona completa):
```
Usuário: "Como aumentar vendas?"
Dan Kennedy: "Para o público de pequenos empresários 
de e-commerce que você atende, focariam newsletter 
transacional. Vejo que eles valorizam eficiência e ROI 
mensurável (Reddit insights). 

Baseado nos trending topics que identificamos (abandoned 
cart recovery), recomendo:
1. Sequência de 3 emails para carrinho abandonado
2. Teste A/B de subject lines focadas em economia de tempo
3. Landing page com linguagem direta (como o público fala)

Isso alinha com o Functional Job 'aumentar conversão' 
e o Emotional Job 'reduzir ansiedade sobre desperdício'."
```

**A diferença é BRUTAL!** 🚀

---

## PRIORIZAÇÃO

### Implementar AGORA (Alto Impacto):
1. ✅ Criar `_build_enriched_persona_context()` com TODOS os dados
2. ✅ Integrar no Chat 1:1 (expandir contexto atual)
3. ✅ Integrar no Council Analyze Inicial
4. ✅ Verificar Council Chat Follow-up (já existe, mas expandir)

### Implementar DEPOIS (Médio Impacto):
5. ⏳ Recomendações de experts baseadas em persona
6. ⏳ Sugestões de perguntas baseadas em persona
7. ⏳ Analytics mostrando alinhamento com persona

---

## ARQUIVOS A MODIFICAR

1. **`python_backend/main.py`**
   - Criar função `_build_enriched_persona_context(persona)`
   - Atualizar `send_message` (chat 1:1) - linha 3033
   - Atualizar `create_council_analysis` - linha ~3838
   - Atualizar `create_council_analysis_stream` - linha ~3902
   - Atualizar `_build_council_context` - linha 4429

2. **`python_backend/crew_council.py`**
   - Adicionar parâmetro `persona` em `analyze()`
   - Adicionar parâmetro `persona` em `_get_expert_analysis()`
   - Injetar contexto da persona no system prompt dos experts

3. **`python_backend/models.py`** (opcional)
   - Adicionar `persona: Optional[UserPersona]` nos tipos relevantes

---

## RISCOS E MITIGAÇÕES

### Risco 1: Contexto Muito Grande
**Problema:** System prompt + persona = >8K tokens  
**Mitigação:** Resumir dados enriquecidos (top 3-5 itens por categoria)

### Risco 2: Persona Não Existe
**Problema:** Usuário sem persona = erro  
**Mitigação:** Fallback gracioso (funciona sem persona)

### Risco 3: Performance
**Problema:** Buscar persona em cada mensagem  
**Mitigação:** Cache de 5 minutos da persona ativa

---

## ESTIMATIVA

**Tempo:** 2-3 horas  
**Complexidade:** Média  
**Impacto:** MUITO ALTO 🚀  

---

## PRÓXIMO PASSO

Você quer que eu:
- **a) Implemente tudo agora** (Fase 1: contexto enriquecido nos 3 lugares)
- **b) Comece com Chat 1:1** e valide antes de expandir
- **c) Crie um plano mais detalhado** antes de implementar

**Minha recomendação:** Opção A - Implementar tudo agora para maximizar valor!

