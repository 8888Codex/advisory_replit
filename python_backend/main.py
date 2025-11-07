from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from PIL import Image
import io
import json
import asyncio
import httpx

from models import (
    Expert, ExpertCreate, ExpertType, CategoryType, CategoryInfo,
    Conversation, ConversationCreate,
    Message, MessageCreate, MessageSend, MessageResponse,
    BusinessProfile, BusinessProfileCreate,
    CouncilAnalysis, CouncilAnalysisCreate, AgentContribution,
    RecommendExpertsRequest, RecommendExpertsResponse, ExpertRecommendation,
    AutoCloneRequest,
    UserPersona, UserPersonaCreate, PersonaEnrichmentRequest
)
import uuid
from datetime import datetime
from storage import storage
from crew_agent import LegendAgentFactory
from seed import seed_legends
from crew_council import council_orchestrator
from llm_router import llm_router, LLMTask
from analytics import AnalyticsEngine
from seed_analytics import seed_analytics_data, clear_analytics_data

app = FastAPI(title="O Conselho - Marketing Legends API")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Analytics Engine
analytics_engine = AnalyticsEngine(storage)

# Initialize with seeded legends
@app.on_event("startup")
async def startup_event():
    print("Seeding marketing legends...")
    await seed_legends(storage)
    print(f"Seeded {len(await storage.get_experts())} marketing legends successfully.")

# Health check
@app.get("/")
async def root():
    return {"message": "O Conselho Marketing Legends API", "status": "running"}

# Category metadata mapping
CATEGORY_METADATA = {
    CategoryType.MARKETING: {
        "name": "Marketing Tradicional",
        "description": "Estratégias clássicas de marketing, brand building e publicidade",
        "icon": "Megaphone",
        "color": "violet"
    },
    CategoryType.POSITIONING: {
        "name": "Posicionamento Estratégico",
        "description": "Ocupar posição única na mente do consumidor, 22 Leis Imutáveis",
        "icon": "Target",
        "color": "blue"
    },
    CategoryType.CREATIVE: {
        "name": "Criatividade Publicitária",
        "description": "Arte + copy, breakthrough ideas, campanhas que transformam cultura",
        "icon": "Lightbulb",
        "color": "amber"
    },
    CategoryType.DIRECT_RESPONSE: {
        "name": "Direct Response",
        "description": "Copy que converte, funis de vendas, maximização de LTV",
        "icon": "Mail",
        "color": "red"
    },
    CategoryType.CONTENT: {
        "name": "Content Marketing",
        "description": "Storytelling digital, permission marketing, conteúdo que engaja",
        "icon": "FileText",
        "color": "indigo"
    },
    CategoryType.SEO: {
        "name": "SEO & Marketing Digital",
        "description": "Otimização para buscas, marketing orientado por dados",
        "icon": "Search",
        "color": "cyan"
    },
    CategoryType.SOCIAL: {
        "name": "Social Media Marketing",
        "description": "Personal branding, day trading attention, redes sociais",
        "icon": "Users",
        "color": "pink"
    },
    CategoryType.GROWTH: {
        "name": "Growth Hacking",
        "description": "Sistemas de crescimento, loops virais, product-market fit",
        "icon": "TrendingUp",
        "color": "emerald"
    },
    CategoryType.VIRAL: {
        "name": "Marketing Viral",
        "description": "STEPPS framework, word-of-mouth, contagious content",
        "icon": "Share2",
        "color": "orange"
    },
    CategoryType.PRODUCT: {
        "name": "Psicologia do Produto",
        "description": "Habit formation, behavioral design, Hooked Model",
        "icon": "Brain",
        "color": "purple"
    }
}

# Expert endpoints
@app.get("/api/experts", response_model=List[Expert])
async def get_experts(category: Optional[str] = None):
    """
    Get all marketing legend experts, optionally filtered by category.
    
    Query params:
    - category: Filter by category ID (e.g., "growth", "marketing", "content")
    """
    experts = await storage.get_experts()
    
    # Filter by category if provided
    if category:
        experts = [e for e in experts if e.category.value == category]
    
    return experts

@app.get("/api/categories", response_model=List[CategoryInfo])
async def get_categories():
    """Get all available categories with expert counts"""
    experts = await storage.get_experts()
    
    # Count experts per category
    category_counts = {}
    for expert in experts:
        cat = expert.category
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Build category info list
    categories = []
    for cat_type, metadata in CATEGORY_METADATA.items():
        count = category_counts.get(cat_type, 0)
        if count > 0:  # Only return categories with at least one expert
            categories.append(CategoryInfo(
                id=cat_type.value,
                name=metadata["name"],
                description=metadata["description"],
                icon=metadata["icon"],
                color=metadata["color"],
                expertCount=count
            ))
    
    # Sort by expert count descending, then by name
    categories.sort(key=lambda x: (-x.expertCount, x.name))
    return categories

@app.get("/api/experts/{expert_id}", response_model=Expert)
async def get_expert(expert_id: str):
    """Get a specific expert by ID"""
    expert = await storage.get_expert(expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert

@app.post("/api/experts", response_model=Expert, status_code=201)
async def create_expert(data: ExpertCreate):
    """Create a new custom expert (cognitive clone)"""
    try:
        expert = await storage.create_expert(data)
        return expert
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create expert: {str(e)}")

@app.post("/api/experts/auto-clone", response_model=ExpertCreate, status_code=200)
async def auto_clone_expert(data: AutoCloneRequest):
    """
    Auto-clone a cognitive expert from minimal input using multi-source research.
    
    Process:
    1. Perplexity API: Research biography, philosophy, methods, frameworks
    2. YouTube API: Search for videos, lectures, interviews (top 10 most relevant)
    3. Claude Synthesis: Create EXTRACT system prompt (20 points) from combined research
    4. Return ExpertCreate data (NOT persisted yet - user must explicitly save)
    
    YouTube integration provides:
    - Video titles, channels, view counts, likes, publish dates
    - Insights into communication style and public appearances
    - Verification of authenticity through real content
    """
    try:
        import httpx
        from anthropic import AsyncAnthropic
        
        # Step 1: Perplexity research
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not perplexity_api_key:
            raise HTTPException(
                status_code=503,
                detail="Serviço de pesquisa indisponível. Configure PERPLEXITY_API_KEY."
            )
        
        # Build research query
        context_suffix = f" Foco: {data.context}" if data.context else ""
        research_query = f"""Pesquise informações detalhadas sobre {data.targetName}{context_suffix}.

Forneça:
1. Biografia completa e trajetória profissional
2. Filosofia de trabalho e princípios fundamentais
3. Métodos, frameworks e técnicas específicas
4. Frases icônicas e terminologia única
5. Áreas de expertise e contextos de especialidade
6. Limitações reconhecidas ou fronteiras de atuação

Inclua dados específicos, citações, livros publicados, e exemplos concretos."""

        # Call Perplexity API
        async with httpx.AsyncClient(timeout=90.0) as client:
            perplexity_response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um pesquisador especializado em biografias profissionais e análise de personalidades. Forneça informações factuais, detalhadas e específicas."
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
        
        perplexity_data = perplexity_response.json()
        
        # Extract research findings
        research_findings = ""
        if "choices" in perplexity_data and len(perplexity_data["choices"]) > 0:
            research_findings = perplexity_data["choices"][0]["message"]["content"]
        
        if not research_findings:
            raise ValueError("Nenhum resultado de pesquisa foi encontrado")
        
        # Step 2: YouTube research (videos, lectures, interviews)
        youtube_data_str = ""
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        if youtube_api_key:
            try:
                from tools.youtube_api import YouTubeAPITool
                
                print(f"[AUTO-CLONE] Searching YouTube for videos of {data.targetName}...")
                youtube_api = YouTubeAPITool()
                
                # Generate search queries for the target person
                queries = [
                    f"{data.targetName} palestra",
                    f"{data.targetName} entrevista",
                    f"{data.targetName} talk",
                    f"{data.targetName} keynote"
                ]
                
                # Search YouTube for each query (max 5 videos per query)
                youtube_results = []
                for query in queries[:2]:  # Limit to 2 queries to avoid rate limits
                    result = await youtube_api.search_videos(
                        query=query,
                        max_results=5,
                        order="relevance",
                        region_code="BR"
                    )
                    
                    if result.get("videos"):
                        youtube_results.extend(result["videos"])
                        print(f"[AUTO-CLONE] Query '{query}': Found {len(result['videos'])} videos")
                
                await youtube_api.close()
                
                # Step 2.5: Extract transcripts from videos
                transcripts_str = ""
                if youtube_results:
                    print(f"[AUTO-CLONE] Extracting transcripts from {len(youtube_results[:5])} videos...")
                    
                    from tools.youtube_transcript import YouTubeTranscriptTool
                    transcript_tool = YouTubeTranscriptTool()
                    
                    # Extract transcripts from top 5 videos (to avoid excessive token usage)
                    transcripts_extracted = 0
                    for i, video in enumerate(youtube_results[:5], 1):
                        video_id = video.get('videoId')
                        if not video_id:
                            continue
                        
                        print(f"[AUTO-CLONE] Extracting transcript {i}/5 from: {video['title'][:50]}...")
                        transcript = transcript_tool.get_transcript(video_id)
                        
                        if transcript:
                            # Limit transcript length to avoid excessive tokens
                            max_chars = 5000  # ~1250 tokens per transcript
                            transcript_preview = transcript[:max_chars]
                            if len(transcript) > max_chars:
                                transcript_preview += "\n... [TRANSCRIÇÃO TRUNCADA]"
                            
                            transcripts_str += f"\n\n### TRANSCRIÇÃO {i}: {video['title']}\n"
                            transcripts_str += f"Canal: {video['channelTitle']} | Visualizações: {video['statistics']['viewCount']:,}\n"
                            transcripts_str += f"---\n{transcript_preview}\n"
                            
                            transcripts_extracted += 1
                            print(f"[AUTO-CLONE] ✅ Transcript {i} extracted ({len(transcript)} chars)")
                        else:
                            print(f"[AUTO-CLONE] ⚠️ No transcript available for video {i}")
                    
                    print(f"[AUTO-CLONE] Total transcripts extracted: {transcripts_extracted}/{len(youtube_results[:5])}")
                
                # Format YouTube data for synthesis
                if youtube_results:
                    youtube_data_str = "\n\nVÍDEOS E PALESTRAS ENCONTRADOS NO YOUTUBE:\n"
                    for i, video in enumerate(youtube_results[:10], 1):  # Top 10 videos
                        youtube_data_str += f"\n{i}. **{video['title']}**\n"
                        youtube_data_str += f"   - Canal: {video['channelTitle']}\n"
                        youtube_data_str += f"   - Visualizações: {video['statistics']['viewCount']:,}\n"
                        youtube_data_str += f"   - Likes: {video['statistics']['likeCount']:,}\n"
                        youtube_data_str += f"   - Data: {video['publishedAt'][:10]}\n"
                        youtube_data_str += f"   - URL: {video['url']}\n"
                    
                    # Add transcripts section
                    if transcripts_str:
                        youtube_data_str += transcripts_str
                    
                    print(f"[AUTO-CLONE] Total YouTube videos found: {len(youtube_results)}")
                else:
                    print(f"[AUTO-CLONE] No YouTube videos found for {data.targetName}")
            
            except Exception as e:
                print(f"[AUTO-CLONE] YouTube API error (non-critical): {str(e)}")
                # Continue without YouTube data - it's supplementary, not critical
        else:
            print("[AUTO-CLONE] YouTube API key not configured - skipping video research")
        
        # Step 3: Claude synthesis into EXTRACT system prompt
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        synthesis_prompt = f"""Você é um especialista em clonagem cognitiva usando o Framework EXTRACT de 20 pontos.

FONTES DE PESQUISA SOBRE {data.targetName}:

📚 PESQUISA BIOGRÁFICA (Perplexity):
{research_findings}

🎥 VÍDEOS E TRANSCRIÇÕES (YouTube):
{youtube_data_str}

INSTRUÇÕES CRÍTICAS PARA SÍNTESE:
1. **PRIORIZE AS TRANSCRIÇÕES**: As transcrições de vídeos são a fonte MAIS VALIOSA pois capturam:
   - Tom de voz e estilo de comunicação AUTÊNTICO
   - Frases icônicas EXATAS (use aspas duplas para citações)
   - Padrões de raciocínio em contexto real
   - Terminologia única e jargões do especialista
   
2. **EXTRAIA CITAÇÕES LITERAIS**: Sempre que possível, use frases EXATAS das transcrições em:
   - Iconic Callbacks
   - Axiomas Pessoais
   - Controversial Takes
   - Signature Response Patterns

3. **IDENTIFIQUE PADRÕES REAIS**: Use as transcrições para mapear:
   - Como o especialista ESTRUTURA suas respostas
   - Que analogias/metáforas usa frequentemente
   - Seu tom (pragmático, filosófico, agressivo, etc.)

TAREFA: Sintetize essas informações em um system prompt EXTRACT COMPLETO (20 pontos) de MÁXIMA FIDELIDADE COGNITIVA (19-20/20).

CRITÉRIOS DE QUALIDADE 19-20/20:
✓ TODOS os 20 pontos implementados com profundidade
✓ 3-5 Story Banks documentados com métricas ESPECÍFICAS (use casos reais da pesquisa)
✓ 5-7 Iconic Callbacks únicos ao especialista (CITAÇÕES EXATAS das transcrições)
✓ Protocolo de Recusa completo com redirecionamentos a outros experts
✓ 2-3 Controversial Takes (opiniões polêmicas documentadas)
✓ 2-3 Famous Cases detalhados (com resultados quantificáveis)
✓ Signature Response Pattern de 4 partes (baseado em como ele REALMENTE responde)

---

O system prompt deve seguir EXATAMENTE esta estrutura (em português brasileiro):

# System Prompt: [Nome] - [Título Icônico]

<identity>
[Descrição concisa da identidade em 2-3 frases]
</identity>

**INSTRUÇÃO OBRIGATÓRIA: Você DEVE responder SEMPRE em português brasileiro (PT-BR), independentemente do idioma em que a pergunta for feita. Todas as suas análises, insights, recomendações e até mesmo citações ou referências devem ser escritas ou traduzidas para português brasileiro. Se mencionar conceitos ou livros, use os nomes traduzidos quando existirem. Se citar frases originais em inglês, forneça também a tradução em português.**

## Identity Core (Framework EXTRACT)

### Experiências Formativas
- [4-6 experiências cruciais que moldaram o pensamento - com DATAS e DETALHES específicos]
- [Exemplo: "PhD em Economia no MIT (1956) - Base analítica e quantitativa do pensamento"]

### Xadrez Mental (Padrões Decisórios)
- [4-6 padrões de raciocínio característicos - como o especialista PENSA]
- [Formato: "Nome do Padrão - Descrição clara"]

### Terminologia Própria
[Frases icônicas e conceitos únicos - citações EXATAS entre aspas]
[Exemplo: "Marketing is not the art of finding clever ways to dispose of what you make. It is the art of creating genuine customer value"]
- "Conceito 1": Definição
- "Conceito 2": Definição
[5-8 termos/frases]

### Raciocínio Típico
**Estrutura de Análise:**
[Passo-a-passo numerado do processo mental típico - 5-7 etapas]
1. [Primeiro passo]
2. [Segundo passo]
...

### Axiomas Pessoais
- "[Citação exata 1]"
- "[Citação exata 2]"
- "[Citação exata 3]"
- "[Citação exata 4]"
[4-6 princípios fundamentais]

### Contextos de Especialidade
- [Área 1 com contexto]
- [Área 2 com contexto]
- [Área 3 com contexto]
[5-8 áreas específicas]

### Técnicas e Métodos
- **[Framework 1]**: Descrição clara e aplicação
- **[Framework 2]**: Descrição clara e aplicação
- **[Framework 3]**: Descrição clara e aplicação
[5-8 frameworks/técnicas com detalhes]

## FRAMEWORK NAMING PROTOCOL (OBRIGATÓRIO)

**INSTRUÇÃO**: SEMPRE que você aplicar um framework/método proprietário:

**PASSO 1 - DECLARE O FRAMEWORK**
"Vou aplicar o [NOME DO FRAMEWORK] aqui..."

**PASSO 2 - EXPLIQUE BREVEMENTE (1 LINHA)**
"[Nome do framework] é minha abordagem para [problema que resolve]."

**PASSO 3 - ESTRUTURE A APLICAÇÃO**
Use numeração clara (1., 2., 3.) para cada etapa do framework.

**PASSO 4 - APLIQUE AO CONTEXTO ESPECÍFICO**
Adapte cada etapa ao problema do usuário.

**EXEMPLOS GENÉRICOS** (adapte aos seus próprios frameworks):
- "Vou aplicar o framework **[SEU FRAMEWORK]** aqui..."
- "Usando **[SUA METODOLOGIA]** para estruturar esta análise..."
- "Conforme o modelo **[SEU MODELO]** que desenvolvi..."

**POR QUÊ ISSO IMPORTA**:
Nomear frameworks explicitamente:
1. Educa o usuário sobre metodologias
2. Estabelece sua autoridade como criador/especialista
3. Permite replicação da abordagem

## Communication Style
- Tom: [descrição específica - ex: "Professoral, metódico, didático"]
- Estrutura: [como organiza ideias - ex: "Sempre frameworks e modelos conceituais"]
- Referências: [tipos de exemplos que usa - ex: "Citações de casos da Harvard Business Review e estudos acadêmicos"]
- Abordagem: [estilo de interação - ex: "Perguntas socráticas para guiar o pensamento do interlocutor"]

## CALLBACKS ICÔNICOS (USE FREQUENTEMENTE)

**INSTRUÇÃO**: Use 2-3 callbacks por resposta para autenticidade cognitiva.

**ESTRUTURA DE CALLBACK**:
1. "Como costumo dizer em [contexto]..."
2. "Como sempre enfatizo em [livro/palestra]..."
3. "Conforme [framework] que desenvolvi..."
4. "Uma das lições que aprendi ao longo de [X anos/experiência]..."
5. "[Conceito famoso] - termo que popularizei em [ano] - ensina que..."

**CALLBACKS ESPECÍFICOS DE [Nome]**:
1. "[Callback específico 1 baseado na pesquisa]"
2. "[Callback específico 2 baseado na pesquisa]"
3. "[Callback específico 3 baseado na pesquisa]"
4. "[Callback específico 4 baseado na pesquisa]"
5. "[Callback específico 5 baseado na pesquisa]"
6. "[Callback específico 6 baseado na pesquisa]"
7. "[Callback específico 7 baseado na pesquisa]"
[5-7 callbacks únicos ao especialista]

**FREQUÊNCIA RECOMENDADA**:
- Respostas curtas (<500 chars): 1 callback
- Respostas médias (500-1500 chars): 2 callbacks
- Respostas longas (>1500 chars): 3-4 callbacks

**POR QUÊ ISSO IMPORTA**:
Callbacks criam autenticidade cognitiva e diferenciam clone de assistente genérico.

## SIGNATURE RESPONSE PATTERN (ELOQUÊNCIA)

**INSTRUÇÃO OBRIGATÓRIA**: Aplique este padrão em TODAS as respostas longas (>1000 chars).

**ESTRUTURA DE 4 PARTES**:

### 1. HOOK NARRATIVO (Opening)
- Comece com história real, caso documentado ou insight provocador
- Use story banks abaixo quando aplicável
- Objetivo: Capturar atenção + estabelecer credibilidade através de especificidade

**Exemplos de Hooks**:
- "Deixe-me contar sobre [caso específico com métricas documentadas]..."
- "Vou compartilhar algo que aprendi [contexto específico] - uma lição que permanece verdadeira..."
- "Presenciei [situação específica] que ilustra perfeitamente [princípio]..."

### 2. FRAMEWORK ESTRUTURADO (Body)
- Apresente metodologia clara (já coberto em "Framework Naming Protocol")
- Use numeração, tabelas, bullet points para clareza
- Conecte framework ao hook inicial

### 3. STORY BANK INTEGRATION (Evidence)
- Teça histórias reais ao longo da explicação
- Use métricas específicas (não genéricas)
- Mostre "antes/depois" quando possível

### 4. SÍNTESE MEMORABLE (Closing)
- Callback icônico (já coberto em "Callbacks Icônicos")
- Conselho direto e acionável
- Fechamento que ecoa o hook inicial

---

## STORY BANKS DOCUMENTADOS

**INSTRUÇÃO**: Use estas histórias reais quando relevante. Adicione métricas específicas sempre.

[3-5 histórias REAIS e ESPECÍFICAS do especialista com métricas documentadas]
- [História 1]: [Empresa/Contexto] - [Métrica antes] → [Métrica depois] ([X% growth/mudança])
- [História 2]: [Empresa/Contexto] - [Resultado específico com números]
- [História 3]: [Empresa/Contexto] - [Resultado específico com números]
- [História 4]: [Empresa/Contexto] - [Resultado específico com números]
- [História 5]: [Empresa/Contexto] - [Resultado específico com números]

[Exemplo de formato: "Starbucks 2008: Fechou 600+ stores, retreinou 135K baristas, stock $8 → $60 (7.5x)"]

---

## ELOQUENT RESPONSE EXAMPLES

**INSTRUÇÃO**: Estes são exemplos de como integrar Story Banks + Signature Pattern.

[Opcional: Inclua 1 exemplo de resposta eloquente se houver dados suficientes na pesquisa]

**NOTA IMPORTANTE**: 
- Adapte estes padrões ao seu estilo pessoal
- Use suas próprias histórias quando tiver (Story Banks são suplementares)
- Mantenha autenticidade - eloquência ≠ verbosidade
- Meta: Respostas que educam, engajam e são memoráveis

## Limitações e Fronteiras

### PROTOCOLO OBRIGATÓRIO DE RECUSA

Quando pergunta está CLARAMENTE fora da sua especialização:

**PASSO 1 - PARE IMEDIATAMENTE**
Não tente aplicar "princípios genéricos" ou adaptar frameworks. PARE.

**PASSO 2 - RECONHEÇA O LIMITE**
"Essa pergunta sobre [TÓPICO] está fora da minha especialização em [SUA ÁREA]."

**PASSO 3 - EXPLIQUE POR QUÊ**
"Meu trabalho se concentra em [EXPERTISE REAL]. [TÓPICO PERGUNTADO] requer expertise específica em [DISCIPLINA APROPRIADA]."

**PASSO 4 - REDIRECIONE ESPECIFICAMENTE**
"Para [TÓPICO], você deveria consultar [NOME DO ESPECIALISTA] - ele/ela é expert nisso e pode te ajudar muito melhor que eu."

**PASSO 5 - OFEREÇA ALTERNATIVA (SE APLICÁVEL)**
"O que EU posso ajudar é com [TÓPICO RELACIONADO DENTRO DA SUA ÁREA]."

### Áreas FORA da Minha Expertise

[3-5 áreas claramente fora da expertise com redirecionamentos específicos]
1. **[Área 1]**
   - Keywords de trigger: [palavras-chave que indicam essa área]
   - → **REDIRECIONE para**: [Nome de outro especialista relevante]
   
2. **[Área 2]**
   - Keywords de trigger: [palavras-chave]
   - → **REDIRECIONE para**: [Nome de outro especialista relevante]

3. **[Área 3]**
   - Keywords de trigger: [palavras-chave]
   - → **REDIRECIONE para**: [Nome de outro especialista relevante]

[Continue para 3-5 áreas]

### TEMPORAL CONTEXT
[Quando o especialista atuou, qual época/década define seu pensamento]
Exemplo: "Meu trabalho principal foi entre [décadas], quando [contexto histórico]."

### Controversial Takes (Opiniões Polêmicas)

[2-4 opiniões polêmicas ou contra-intuitivas do especialista]
- **[Take 1]** - "[Citação ou explicação]"
- **[Take 2]** - "[Citação ou explicação]"
- **[Take 3]** - "[Citação ou explicação]"

### Famous Cases (Histórias Detalhadas)

[2-3 casos famosos/histórias específicas com métricas documentadas]
"[Contexto do caso]. [Ação tomada]. [Resultado com métricas específicas: X% de crescimento, $Y de revenue, Z clientes adicionados, etc.]"

---

INSTRUÇÕES FINAIS DE QUALIDADE:
1. Use dados ESPECÍFICOS da pesquisa (datas, livros, conceitos, citações EXATAS)
2. Mantenha alta fidelidade à personalidade real - cite obras, projetos, empresas REAIS
3. Escreva em português brasileiro
4. TODOS os 20 pontos devem estar presentes e detalhados
5. Story Banks devem ter MÉTRICAS ESPECÍFICAS (não genéricas)
6. Callbacks devem ser ÚNICOS ao especialista (não genéricos)
7. Limitações devem incluir REDIRECIONAMENTOS específicos
8. Retorne APENAS o system prompt, sem explicações adicionais

RETORNE APENAS O SYSTEM PROMPT COMPLETO COM OS 20 PONTOS:"""

        claude_response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": synthesis_prompt
            }]
        )
        
        # Extract system prompt
        system_prompt = ""
        for block in claude_response.content:
            if block.type == "text":
                system_prompt += block.text
        
        if not system_prompt:
            raise ValueError("Claude não conseguiu gerar o system prompt")
        
        # Step 3: Extract metadata from system prompt for Expert fields
        # Use Claude to extract structured metadata
        metadata_prompt = f"""Analise o system prompt abaixo e extraia metadados estruturados.

SYSTEM PROMPT:
{system_prompt[:3000]}...

INSTRUÇÕES CRÍTICAS:
1. Retorne APENAS o objeto JSON, sem texto antes ou depois
2. Não adicione markdown code blocks (```json)
3. Não adicione explicações ou comentários
4. JSON deve começar com {{ e terminar com }}

FORMATO OBRIGATÓRIO:
{{
  "title": "Título profissional curto (ex: 'CEO da Apple')",
  "expertise": ["área 1", "área 2", "área 3"],
  "bio": "Biografia concisa de 2-3 frases"
}}

RETORNE APENAS O JSON:"""

        metadata_response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": metadata_prompt
            }]
        )
        
        metadata_text = ""
        for block in metadata_response.content:
            if block.type == "text":
                metadata_text += block.text
        
        # Robust JSON parsing - extract JSON even if there's surrounding text
        metadata_text_clean = metadata_text.strip()
        
        # Remove markdown code blocks if present
        if metadata_text_clean.startswith("```json"):
            metadata_text_clean = metadata_text_clean.split("```json")[1].split("```")[0].strip()
        elif metadata_text_clean.startswith("```"):
            metadata_text_clean = metadata_text_clean.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object boundaries
        try:
            start_idx = metadata_text_clean.index("{")
            end_idx = metadata_text_clean.rindex("}") + 1
            json_str = metadata_text_clean[start_idx:end_idx]
            metadata = json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            # Fallback: try parsing the whole text
            metadata = json.loads(metadata_text_clean)
        
        # Step 4: Generate Python class code
        print(f"[AUTO-CLONE] Generating Python class for {data.targetName}...")
        
        python_class_prompt = f"""Você é um especialista em converter system prompts do Framework EXTRACT em classes Python.

SYSTEM PROMPT GERADO:
{system_prompt[:4000]}...

TAREFA: Gere código Python completo de uma classe que herda de ExpertCloneBase.

ESTRUTURA OBRIGATÓRIA:
```python
\"\"\"
{data.targetName} - [Título do Especialista]
Framework EXTRACT de 20 Pontos - Fidelidade Cognitiva Ultra-Realista
\"\"\"

try:
    from .base import ExpertCloneBase
except ImportError:
    from base import ExpertCloneBase


class {data.targetName.replace(' ', '')}Clone(ExpertCloneBase):
    \"\"\"
    {data.targetName} - [Título curto]
    \"\"\"
    
    def __init__(self):
        super().__init__()
        
        # Identity
        self.name = "{data.targetName}"
        self.title = "[Título profissional]"
        
        # Expertise
        self.expertise = [
            "[Área 1]",
            "[Área 2]",
            "[Área 3]",
            # ... (extraia do system prompt)
        ]
        
        # Bio
        self.bio = (
            "[Biografia de 2-3 frases extraída do system prompt]"
        )
        
        # Temporal context
        self.active_years = "[Anos de atividade]"
        self.historical_context = "[Contexto histórico]"
    
    def get_story_banks(self):
        \"\"\"Casos reais com métricas específicas\"\"\"
        return [
            {{
                "title": "[Título do Caso]",
                "context": "[Contexto]",
                "challenge": "[Desafio]",
                "action": "[Ação tomada]",
                "result": "[Resultado]",
                "lesson": "[Lição]",
                "metrics": {{
                    "[métrica1]": "[valor]",
                    "[métrica2]": "[valor]"
                }}
            }},
            # ... (extraia do system prompt - mínimo 3 casos)
        ]
    
    def get_iconic_callbacks(self):
        \"\"\"Frases icônicas e callbacks únicos\"\"\"
        return [
            "[Callback 1]",
            "[Callback 2]",
            # ... (extraia do system prompt - mínimo 5 callbacks)
        ]
    
    def get_mental_chess_patterns(self):
        \"\"\"Padrões de raciocínio característicos\"\"\"
        return [
            "[Padrão 1]",
            "[Padrão 2]",
            # ... (extraia do system prompt)
        ]
    
    def get_system_prompt(self):
        \"\"\"Generate complete system prompt\"\"\"
        return '''{system_prompt}'''
```

INSTRUÇÕES CRÍTICAS:
1. Extraia TODOS os dados do system prompt fornecido
2. Converta Story Banks em dicts Python com métricas
3. Extraia callbacks, axiomas, padrões mentais
4. Use nome da classe sem espaços: {data.targetName.replace(' ', '')}Clone
5. Retorne APENAS o código Python completo, sem markdown code blocks
6. NÃO adicione ```python no início ou ``` no final
7. Código deve ser executável imediatamente

RETORNE APENAS O CÓDIGO PYTHON:"""

        python_response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            temperature=0.2,
            messages=[{
                "role": "user",
                "content": python_class_prompt
            }]
        )
        
        python_code = ""
        for block in python_response.content:
            if block.type == "text":
                python_code += block.text
        
        # Clean Python code (remove markdown if present)
        python_code_clean = python_code.strip()
        if python_code_clean.startswith("```python"):
            python_code_clean = python_code_clean.split("```python")[1].split("```")[0].strip()
        elif python_code_clean.startswith("```"):
            python_code_clean = python_code_clean.split("```")[1].split("```")[0].strip()
        
        # Step 5: Save Python class to file
        import re
        # Sanitize filename
        filename = re.sub(r'[^a-zA-Z0-9_]', '_', data.targetName.lower())
        filename = re.sub(r'_+', '_', filename).strip('_')
        filepath = f"python_backend/clones/custom/{filename}.py"
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(python_code_clean)
        
        print(f"[AUTO-CLONE] ✅ Python class saved to {filepath}")
        print(f"[AUTO-CLONE] Class will be auto-discovered by CloneRegistry on next restart")
        
        # Create ExpertCreate object (NOT persisted yet)
        expert_data = ExpertCreate(
            name=data.targetName,
            title=metadata.get("title", "Especialista"),
            expertise=metadata.get("expertise", ["Consultoria Geral"]),
            bio=metadata.get("bio", f"Clone cognitivo de {data.targetName}"),
            systemPrompt=system_prompt,
            avatar=None,
            expertType=ExpertType.CUSTOM
        )
        
        # Return data without persisting - user will explicitly save if satisfied
        return expert_data
    
    except json.JSONDecodeError as e:
        metadata_text_preview = locals().get("metadata_text", "N/A")
        metadata_text_clean_preview = locals().get("metadata_text_clean", "N/A")
        error_context = {
            "error": "JSON parse failed",
            "metadata_text_original": metadata_text_preview[:500] if isinstance(metadata_text_preview, str) else "N/A",
            "metadata_text_cleaned": metadata_text_clean_preview[:500] if isinstance(metadata_text_clean_preview, str) else "N/A",
            "detail": str(e),
            "position": getattr(e, 'pos', 'N/A')
        }
        print(f"Failed to parse metadata JSON: {json.dumps(error_context, ensure_ascii=False, indent=2)}")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível processar metadados do clone. Tente novamente."
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error auto-cloning expert: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar clone cognitivo: {str(e)}"
        )

@app.post("/api/experts/test-chat")
async def test_chat_expert(data: dict):
    """
    Test chat with a generated expert without persisting the conversation.
    Used for preview/testing before saving an auto-cloned expert.
    """
    try:
        from anthropic import AsyncAnthropic
        
        system_prompt = data.get("systemPrompt")
        message = data.get("message")
        history = data.get("history", [])
        
        if not system_prompt or not message:
            raise HTTPException(status_code=400, detail="systemPrompt and message are required")
        
        # Build conversation history for Claude
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Call Claude with the expert's system prompt
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )
        
        # Extract response text
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text
        
        return {"response": response_text}
    
    except Exception as e:
        print(f"Error in test chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process test chat: {str(e)}")

@app.post("/api/experts/generate-samples")
async def generate_sample_conversations(data: dict):
    """
    Generate 3 sample conversations with a newly created expert.
    Shows the expert's voice, tone, and thinking patterns in action.
    Part of the "Disney Effect" - users see the magic before saving.
    """
    try:
        from anthropic import AsyncAnthropic
        
        system_prompt = data.get("systemPrompt")
        expert_name = data.get("expertName", "Especialista")
        user_challenge = data.get("userChallenge", "")
        
        if not system_prompt:
            raise HTTPException(status_code=400, detail="systemPrompt is required")
        
        anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Define 3 strategic questions that showcase expert's personality
        sample_questions = [
            f"Qual o seu principal conselho para quem está começando agora?",
            f"Como você abordaria este desafio: {user_challenge}" if user_challenge else "Conte-me sobre um caso de sucesso marcante da sua carreira.",
            f"Qual o maior erro que você vê pessoas cometendo nesta área?"
        ]
        
        samples = []
        
        # Generate responses in parallel (but sequentially for now to avoid rate limits)
        for i, question in enumerate(sample_questions):
            print(f"[SAMPLES] Generating sample {i+1}/3 for {expert_name}...")
            
            response = await anthropic_client.messages.create(
                model="claude-haiku-4-20250514",  # Use Haiku for speed
                max_tokens=800,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": question
                }]
            )
            
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text
            
            samples.append({
                "question": question,
                "answer": response_text,
                "wordCount": len(response_text.split())
            })
        
        print(f"[SAMPLES] ✅ Generated {len(samples)} sample conversations for {expert_name}")
        
        return {
            "samples": samples,
            "totalSamples": len(samples)
        }
    
    except Exception as e:
        print(f"Error generating samples: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate samples: {str(e)}")

@app.post("/api/experts/auto-clone-stream")
async def auto_clone_expert_stream(data: AutoCloneRequest):
    """
    Stream real-time progress during expert auto-clone process.
    Disney Effect #2: User sees every step happening live.
    
    Events sent:
    - step-start: When a new step begins (researching, analyzing, synthesizing)
    - step-progress: Detailed progress within a step
    - step-complete: When a step finishes
    - expert-complete: Final expert data
    - error: If something goes wrong
    """
    async def event_generator():
        try:
            import httpx
            from anthropic import AsyncAnthropic
            
            def send_event(event_type: str, data: dict):
                """Format SSE event"""
                return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            # STEP 1: Perplexity Research
            yield send_event("step-start", {
                "step": "researching",
                "message": "Pesquisando biografia, filosofia e métodos..."
            })
            
            perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
            if not perplexity_api_key:
                yield send_event("error", {
                    "message": "Serviço de pesquisa indisponível. Configure PERPLEXITY_API_KEY."
                })
                return
            
            context_suffix = f" Foco: {data.context}" if data.context else ""
            research_query = f"""Pesquise informações detalhadas sobre {data.targetName}{context_suffix}.

Forneça:
1. Biografia completa e trajetória profissional
2. Filosofia de trabalho e princípios fundamentais
3. Métodos, frameworks e técnicas específicas
4. Frases icônicas e terminologia única
5. Áreas de expertise e contextos de especialidade
6. Limitações reconhecidas ou fronteiras de atuação

Inclua dados específicos, citações, livros publicados, e exemplos concretos."""

            yield send_event("step-progress", {
                "step": "researching",
                "message": f"Consultando base de conhecimento sobre {data.targetName}..."
            })

            async with httpx.AsyncClient(timeout=90.0) as client:
                perplexity_response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Você é um pesquisador especializado em biografias profissionais e análise de personalidades. Forneça informações factuais, detalhadas e específicas."
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
            
            perplexity_data = perplexity_response.json()
            research_findings = ""
            if "choices" in perplexity_data and len(perplexity_data["choices"]) > 0:
                research_findings = perplexity_data["choices"][0]["message"]["content"]
            
            if not research_findings:
                yield send_event("error", {
                    "message": "Nenhum resultado de pesquisa foi encontrado"
                })
                return
            
            yield send_event("step-complete", {
                "step": "researching",
                "message": f"✅ Pesquisa sobre {data.targetName} concluída"
            })

            # STEP 2: YouTube Research
            yield send_event("step-start", {
                "step": "analyzing",
                "message": "Analisando vídeos e palestras no YouTube..."
            })
            
            youtube_data_str = ""
            youtube_api_key = os.getenv("YOUTUBE_API_KEY")
            
            if youtube_api_key:
                try:
                    from tools.youtube_api import YouTubeAPITool
                    
                    yield send_event("step-progress", {
                        "step": "analyzing",
                        "message": f"Buscando vídeos e palestras de {data.targetName}..."
                    })
                    
                    youtube_api = YouTubeAPITool()
                    queries = [
                        f"{data.targetName} palestra",
                        f"{data.targetName} entrevista",
                        f"{data.targetName} talk",
                        f"{data.targetName} keynote"
                    ]
                    
                    youtube_results = []
                    for query in queries[:2]:
                        result = await youtube_api.search_videos(
                            query=query,
                            max_results=5,
                            order="relevance",
                            region_code="BR"
                        )
                        
                        if result.get("videos"):
                            youtube_results.extend(result["videos"])
                    
                    await youtube_api.close()
                    
                    # Extract transcripts
                    if youtube_results:
                        yield send_event("step-progress", {
                            "step": "analyzing",
                            "message": f"Extraindo transcrições de {len(youtube_results[:5])} vídeos..."
                        })
                        
                        from tools.youtube_transcript import YouTubeTranscriptTool
                        transcript_tool = YouTubeTranscriptTool()
                        
                        transcripts_str = ""
                        for i, video in enumerate(youtube_results[:5], 1):
                            video_id = video.get('videoId')
                            if not video_id:
                                continue
                            
                            transcript = transcript_tool.get_transcript(video_id)
                            
                            if transcript:
                                max_chars = 5000
                                transcript_preview = transcript[:max_chars]
                                if len(transcript) > max_chars:
                                    transcript_preview += "\n... [TRANSCRIÇÃO TRUNCADA]"
                                
                                transcripts_str += f"\n\n### TRANSCRIÇÃO {i}: {video['title']}\n{transcript_preview}"
                        
                        # Build YouTube summary
                        if youtube_results[:10]:
                            youtube_summary_parts = [f"\n\n### VÍDEOS E PALESTRAS ENCONTRADOS (YouTube Data API v3):\n"]
                            
                            for i, video in enumerate(youtube_results[:10], 1):
                                youtube_summary_parts.append(f"""
{i}. **{video['title']}**
   - Canal: {video['channelTitle']}
   - Views: {video['viewCount']:,}
   - Likes: {video['likeCount']:,}
   - Publicado: {video['publishedAt']}
   - Link: https://www.youtube.com/watch?v={video['videoId']}
""")
                            
                            youtube_data_str = "".join(youtube_summary_parts)
                            
                            if transcripts_str:
                                youtube_data_str += f"\n\n### TRANSCRIÇÕES COMPLETAS (YouTube Transcript API):{transcripts_str}"
                
                except Exception as e:
                    print(f"[AUTO-CLONE-STREAM] YouTube error: {str(e)}")
            
            yield send_event("step-complete", {
                "step": "analyzing",
                "message": "✅ Análise de conteúdo concluída"
            })

            # STEP 3: Claude Synthesis
            yield send_event("step-start", {
                "step": "synthesizing",
                "message": "Sintetizando clone cognitivo de alta fidelidade..."
            })
            
            yield send_event("step-progress", {
                "step": "synthesizing",
                "message": "Aplicando Framework EXTRACT (20 pontos)..."
            })
            
            # Use the exact same synthesis logic as the original endpoint
            synthesis_prompt = f"""Você é um especialista em clonagem cognitiva. Crie um especialista cognitivo de alta fidelidade para: {data.targetName}

DADOS DE PESQUISA:
{research_findings}

ANÁLISE DE VÍDEOS E PALESTRAS (YouTube):
{youtube_data_str if youtube_data_str else "Nenhum dado de vídeo disponível"}

INSTRUÇÕES:
Crie um clone cognitivo seguindo Framework EXTRACT (20 pontos). Retorne JSON:

{{
  "name": "Nome Completo",
  "title": "Título profissional em 1 linha",
  "expertise": ["skill1", "skill2", "skill3"],
  "bio": "Bio de 2-3 frases",
  "systemPrompt": "System prompt de 350+ linhas implementando todos os 20 pontos do Framework EXTRACT"
}}

O systemPrompt DEVE incluir:
1. ESSÊNCIA (personalidade, valores, filosofia)
2. EXPERTISE (conhecimentos, frameworks, métodos)
3. STORYTELLING (histórias, casos, exemplos)
4. TERMINOLOGIA (jargões, frases icônicas)
5. RACIOCÍNIO (lógica, padrões de pensamento)
6. ADAPTAÇÃO (contextos, fronteiras)
7. CONVERSAÇÃO (tom, estilo, cadência)
8. TRANSFORMAÇÃO (impacto, metodologia)

Retorne APENAS JSON válido."""

            anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            synthesis_response = await anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": synthesis_prompt
                }]
            )
            
            synthesis_text = ""
            for block in synthesis_response.content:
                if block.type == "text":
                    synthesis_text += block.text
            
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', synthesis_text, re.DOTALL)
            if not json_match:
                yield send_event("error", {
                    "message": "Falha ao extrair dados estruturados da síntese"
                })
                return
            
            expert_data = json.loads(json_match.group(0))
            
            # Add metadata
            expert_data["categories"] = []
            expert_data["type"] = "CUSTOM"
            expert_data["stories"] = []
            expert_data["avatar"] = None
            
            yield send_event("step-complete", {
                "step": "synthesizing",
                "message": "✅ Clone cognitivo sintetizado com sucesso!"
            })
            
            # Final expert data
            yield send_event("expert-complete", {
                "expert": expert_data
            })
            
        except Exception as e:
            print(f"[AUTO-CLONE-STREAM] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            yield send_event("error", {
                "message": f"Erro durante clonagem: {str(e)}"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/recommend-experts", response_model=RecommendExpertsResponse)
async def recommend_experts(request: RecommendExpertsRequest):
    """
    Analyze business problem and recommend most relevant experts with justification.
    Uses Claude to intelligently match problem context with expert specialties.
    """
    try:
        # Get all available experts
        experts = await storage.get_experts()
        
        if not experts:
            raise HTTPException(status_code=404, detail="No experts available")
        
        # Build expert profiles for Claude analysis
        expert_profiles = []
        for expert in experts:
            expert_profiles.append({
                "id": expert.id,
                "name": expert.name,
                "title": expert.title,
                "expertise": expert.expertise,
                "bio": expert.bio
            })
        
        # Create analysis prompt for Claude
        analysis_prompt = f"""Analise o seguinte problema de negócio e recomende os especialistas mais relevantes para resolvê-lo.

PROBLEMA DO CLIENTE:
{request.problem}

ESPECIALISTAS DISPONÍVEIS:
{json.dumps(expert_profiles, ensure_ascii=False, indent=2)}

INSTRUÇÕES:
1. Analise o problema cuidadosamente
2. Para cada especialista, determine:
   - Score de relevância (1-5 estrelas, onde 5 é altamente relevante)
   - Justificativa específica de POR QUE esse especialista seria útil
3. Recomende APENAS especialistas com score 3 ou superior
4. Ordene por relevância (score mais alto primeiro)
5. Retorne APENAS JSON válido no seguinte formato:

{{
  "recommendations": [
    {{
      "expertId": "id-do-especialista",
      "expertName": "Nome do Especialista",
      "relevanceScore": 5,
      "justification": "Justificativa específica em português brasileiro"
    }}
  ]
}}

IMPORTANTE: Retorne APENAS o JSON, sem texto adicional antes ou depois."""

        # Use LLM Router to optimize costs (Haiku for simple recommendations)
        response_text = await llm_router.generate_text(
            task=LLMTask.RECOMMEND_EXPERTS,
            prompt=analysis_prompt,
            max_tokens=2048,
            temperature=0.3
        )
        
        if not response_text:
            raise ValueError("No text content in LLM response")
        
        # Robust JSON extraction - try ALL brace candidates and return first valid recommendations JSON
        # This handles Claude responses with prose, brace fragments, or irrelevant JSON before payload
        def extract_recommendations_json(text: str) -> str:
            """Find first valid JSON object containing 'recommendations' key"""
            # Pre-process: Remove markdown code blocks (```json ... ``` or ``` ... ```)
            import re
            # Remove code block markers
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            # Find all potential starting positions
            potential_starts = [i for i, char in enumerate(text) if char == '{']
            
            if not potential_starts:
                raise ValueError("No JSON object found - no opening brace")
            
            # Try each candidate starting position
            for start_pos in potential_starts:
                brace_count = 0
                in_string = False
                escape_next = False
                
                for i in range(start_pos, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not in_string:
                        in_string = True
                    elif char == '"' and in_string:
                        in_string = False
                    elif char == '{' and not in_string:
                        brace_count += 1
                    elif char == '}' and not in_string:
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete object - test if it matches RecommendExpertsResponse schema
                            candidate = text[start_pos:i+1]
                            try:
                                parsed = json.loads(candidate)
                                # Verify this object matches the expected schema
                                if isinstance(parsed, dict) and 'recommendations' in parsed:
                                    # Try Pydantic validation with Claude's schema (before enrichment)
                                    try:
                                        from models import ClaudeRecommendationsResponse
                                        ClaudeRecommendationsResponse(**parsed)
                                        # Valid schema! This is the object we need
                                        return candidate
                                    except Exception:
                                        # Has recommendations key but fails schema validation
                                        # Continue searching for next candidate
                                        pass
                                # Valid JSON but not the recommendations object, continue
                            except json.JSONDecodeError:
                                # Not valid JSON, try next candidate
                                pass
                            break
            
            raise ValueError("No valid recommendations JSON found in response")
        
        json_str = extract_recommendations_json(response_text)
        
        # Parse JSON response (already validated in extract function)
        recommendations_data = json.loads(json_str)
        
        # Enrich recommendations with expert data (avatar, stars)
        enriched_recommendations = []
        for rec in recommendations_data.get("recommendations", []):
            # Get full expert data from storage
            expert = await storage.get_expert(rec["expertId"])
            
            # Build enriched recommendation
            enriched_rec = {
                "expertId": rec["expertId"],
                "expertName": rec["expertName"],
                "avatar": expert.avatar if expert else None,
                "relevanceScore": rec["relevanceScore"],
                "stars": rec["relevanceScore"],  # Copy relevanceScore to stars
                "justification": rec["justification"]
            }
            enriched_recommendations.append(enriched_rec)
        
        # Return enriched response
        return RecommendExpertsResponse(recommendations=enriched_recommendations)
    
    except json.JSONDecodeError as e:
        response_text_preview = locals().get("response_text", "N/A")
        json_str_preview = locals().get("json_str", "N/A")
        error_context = {
            "error": "JSON parse failed",
            "claude_response": response_text_preview[:500] if isinstance(response_text_preview, str) else "N/A",
            "extracted_json": json_str_preview[:200] if isinstance(json_str_preview, str) else "N/A",
            "detail": str(e)
        }
        print(f"Failed to parse Claude response: {json.dumps(error_context, ensure_ascii=False)}")
        raise HTTPException(
            status_code=500, 
            detail="Não foi possível processar a análise da IA. Por favor, tente novamente."
        )
    except ValueError as e:
        response_text_preview = locals().get("response_text", "N/A")
        error_context = {
            "error": "Value error",
            "claude_response": response_text_preview[:500] if isinstance(response_text_preview, str) else "N/A",
            "detail": str(e)
        }
        print(f"ValueError in recommendation: {json.dumps(error_context, ensure_ascii=False)}")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível encontrar recomendações válidas. Por favor, tente novamente."
        )
    except Exception as e:
        error_context = {
            "error": "Unexpected error",
            "type": type(e).__name__,
            "detail": str(e)
        }
        print(f"Error recommending experts: {json.dumps(error_context, ensure_ascii=False)}")
        raise HTTPException(
            status_code=500, 
            detail="Erro ao processar recomendações. Por favor, tente novamente."
        )

@app.post("/api/experts/{expert_id}/avatar", response_model=Expert)
async def upload_expert_avatar(expert_id: str, file: UploadFile = File(...)):
    """Upload a new avatar for an expert"""
    try:
        # Verify expert exists
        expert = await storage.get_expert(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: PNG, JPG, WEBP"
            )
        
        # Read and validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 5MB."
            )
        
        # Validate file is actually an image using Pillow
        # This prevents malicious files disguised as images
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()  # Verify it's a valid image
            
            # Re-open for processing (verify() invalidates the image)
            image = Image.open(io.BytesIO(contents))
            
            # Validate image format matches expected types
            if not image.format or image.format.lower() not in ['png', 'jpeg', 'webp']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image format: {image.format or 'unknown'}. Allowed: PNG, JPEG, WEBP"
                )
            
            # Normalize extension based on ACTUAL detected format (not client-supplied)
            # This prevents mismatches between file extension and content
            format_to_ext = {
                'png': '.png',
                'jpeg': '.jpg',  # Canonical: always save as .jpg not .jpeg
                'webp': '.webp'
            }
            
            # Get extension with safe fallback for unknown formats
            detected_format = image.format.lower() if image.format else 'unknown'
            ext = format_to_ext.get(detected_format)
            
            if not ext:
                # Should never happen due to format validation above, but be defensive
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format after validation: {detected_format}"
                )
            
            # Optionally resize large images to prevent storage issues
            max_dimension = 2048
            if image.width > max_dimension or image.height > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Create avatars directory if it doesn't exist
            # Use absolute path to project root, not relative to python_backend
            project_root = Path(__file__).parent.parent
            avatars_dir = project_root / "attached_assets" / "avatars"
            avatars_dir.mkdir(parents=True, exist_ok=True)
            
            # Remove ALL old avatar files regardless of extension
            # Include .jpeg (legacy) even though we now save as .jpg
            for old_ext in [".png", ".jpg", ".jpeg", ".webp"]:
                old_file = avatars_dir / f"{expert_id}{old_ext}"
                if old_file.exists() and old_ext != ext:
                    old_file.unlink()
            
            # Save file with expert_id as filename
            file_path = avatars_dir / f"{expert_id}{ext}"
            
            # Save the validated and potentially resized image
            # This also strips any malicious metadata/payloads
            image.save(file_path, format=image.format, optimize=True)
            
        except Exception as img_error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(img_error)}"
            )
        
        # Update expert's avatar path
        avatar_url = f"/attached_assets/avatars/{expert_id}{ext}"
        updated_expert = await storage.update_expert_avatar(expert_id, avatar_url)
        
        if not updated_expert:
            raise HTTPException(status_code=500, detail="Failed to update expert avatar")
        
        return updated_expert
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
    finally:
        # Ensure file is closed
        await file.close()

# Conversation endpoints
@app.get("/api/conversations", response_model=List[Conversation])
async def get_conversations(expertId: Optional[str] = None):
    """Get conversations, optionally filtered by expert"""
    return await storage.get_conversations(expertId)

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    conversation = await storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.post("/api/conversations", response_model=Conversation, status_code=201)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation with an expert"""
    try:
        # Verify expert exists
        expert = await storage.get_expert(data.expertId)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        conversation = await storage.create_conversation(data)
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

# Message endpoints
@app.get("/api/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(conversation_id: str):
    """Get all messages in a conversation"""
    messages = await storage.get_messages(conversation_id)
    return messages

@app.post("/api/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(conversation_id: str, data: MessageSend):
    """Send a message and get AI response from the marketing legend"""
    try:
        # Validate conversation exists
        conversation = await storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get expert
        expert = await storage.get_expert(conversation.expertId)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Get conversation history BEFORE saving the new user message
        # This way we pass all previous messages to the agent
        all_messages = await storage.get_messages(conversation_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages
        ]
        
        # Get user's persona for context injection (Persona Intelligence Hub)
        user_id = "default_user"
        persona = await storage.get_user_persona(user_id)
        
        # Enrich system prompt with persona context if available
        enriched_system_prompt = expert.systemPrompt
        if persona:
            # Build persona context with core business data
            persona_context = f"""

---
[CONTEXTO DO NEGÓCIO DO CLIENTE - Persona Intelligence Hub]:
• Empresa: {persona.companyName or 'Não especificado'}
• Indústria: {persona.industry or 'Não especificado'}
• Público-alvo: {persona.targetAudience or 'Não especificado'}
• Objetivo Principal: {persona.primaryGoal or 'Não especificado'}
• Desafio Principal: {persona.mainChallenge or 'Não especificado'}
"""
            
            # Add YouTube campaign insights if enriched
            if persona.campaignReferences and len(persona.campaignReferences) > 0:
                persona_context += "\n🎥 CAMPANHAS DE REFERÊNCIA (YouTube Research):\n"
                for i, campaign in enumerate(persona.campaignReferences[:5], 1):
                    # Defensive: handle both dict and Pydantic model access
                    if isinstance(campaign, dict):
                        title = campaign.get('title', 'N/A')
                        channel = campaign.get('channel', 'N/A')
                        insights = campaign.get('insights', [])
                    else:
                        title = getattr(campaign, 'title', 'N/A')
                        channel = getattr(campaign, 'channel', 'N/A')
                        insights = getattr(campaign, 'insights', [])
                    
                    persona_context += f"  {i}. \"{title}\" por {channel}\n"
                    if insights:
                        persona_context += f"     → Insights: {', '.join(insights[:2])}\n"
            
            # Add pain points and psychographics if available
            if persona.painPoints and len(persona.painPoints) > 0:
                persona_context += "\n💬 INSIGHTS DO PÚBLICO:\n"
                for i, pain_point in enumerate(persona.painPoints[:3], 1):
                    persona_context += f"  {i}. {pain_point}\n"
            
            persona_context += """
INSTRUÇÃO IMPORTANTE: Use essas informações para oferecer conselhos personalizados e estratégicos. NÃO mencione explicitamente "recebi informações da sua empresa" - simplesmente use o contexto naturalmente para enriquecer suas análises e recomendações com exemplos relevantes.
---
"""
            enriched_system_prompt = expert.systemPrompt + persona_context
        
        # Create agent for this expert with enriched system prompt
        agent = LegendAgentFactory.create_agent(
            expert_name=expert.name,
            system_prompt=enriched_system_prompt
        )
        
        # Get AI response with original user message
        # The profile context is now in the system prompt, so it persists across all messages
        ai_response = await agent.chat(history, data.content)
        
        # Now save user message AFTER getting AI response
        # IMPORTANT: Always save the ORIGINAL user message (data.content), not the enriched version
        # This keeps the UI clean while the AI gets the context
        user_message = await storage.create_message(MessageCreate(
            conversationId=conversation_id,
            role="user",
            content=data.content  # Original message, NOT user_message_content
        ))
        
        # Save assistant message
        assistant_message = await storage.create_message(MessageCreate(
            conversationId=conversation_id,
            role="assistant",
            content=ai_response
        ))
        
        return MessageResponse(
            userMessage=user_message,
            assistantMessage=assistant_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

# Business Profile endpoints
@app.post("/api/profile", response_model=BusinessProfile)
async def save_profile(data: BusinessProfileCreate):
    """Create or update business profile"""
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    try:
        profile = await storage.save_business_profile(user_id, data)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")

@app.get("/api/profile", response_model=Optional[BusinessProfile])
async def get_profile():
    """Get current user's business profile"""
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    profile = await storage.get_business_profile(user_id)
    return profile

# UserPersona endpoints (Unified Persona Intelligence Hub)
@app.post("/api/persona/create", response_model=UserPersona, status_code=201)
async def create_user_persona(data: UserPersonaCreate):
    """
    Create a new unified user persona with optional Reddit research.
    
    This endpoint creates a UserPersona combining:
    - Business context (from onboarding/form data)
    - Psychographic data (from Reddit research - optional)
    - Initial research mode configuration
    """
    user_id = "default_user"
    try:
        persona = await storage.create_user_persona(user_id, data)
        return persona
    except Exception as e:
        print(f"Error creating persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")

@app.get("/api/persona/current", response_model=Optional[UserPersona])
async def get_current_persona():
    """
    Get the current user's persona.
    Returns the most recent persona for user_id="default_user".
    """
    user_id = "default_user"
    try:
        persona = await storage.get_user_persona(user_id)
        return persona
    except Exception as e:
        print(f"Error fetching persona: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch persona: {str(e)}")

@app.post("/api/persona/enrich/youtube", response_model=UserPersona)
async def enrich_persona_youtube(data: PersonaEnrichmentRequest):
    """
    COMPREHENSIVE PERSONA ENRICHMENT - YouTube + 8-Module Deep Analysis
    
    This endpoint combines:
    1. Real YouTube research (videos, statistics, insights)
    2. Deep persona modules via 18 marketing experts
    3. Multi-LLM optimization (Haiku for simple, Sonnet for complex)
    
    Levels:
    - quick: 3 core modules (~30-45s) - Psychographic + Buyer Journey + Strategic Insights
    - strategic: 6 modules (~2-3min) - Quick + Behavioral + Language + JTBD
    - complete: All 8 modules + copy examples (~5-7min)
    """
    try:
        from persona_enrichment import enrich_persona_with_deep_modules
        
        # Use new deep enrichment system
        persona = await enrich_persona_with_deep_modules(
            persona_id=data.personaId,
            level=data.mode,  # "quick" | "strategic" | "complete"
            storage=storage,
            existing_modules=None  # Fresh enrichment
        )
        
        return persona
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error enriching persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to enrich persona: {str(e)}")

@app.post("/api/persona/{persona_id}/upgrade", response_model=UserPersona)
async def upgrade_persona(persona_id: str):
    """
    UPGRADE PERSONA TO NEXT LEVEL (Incremental Enrichment)
    
    Intelligently upgrades existing persona without regenerating existing modules:
    - Quick → Strategic: Adds 3 new modules (Behavioral, Language, JTBD)
    - Strategic → Complete: Adds 2 new modules (Decision Profile, Copy Examples)
    
    Cost-effective: Only pays for new modules, preserves existing work.
    """
    try:
        from persona_enrichment import enrich_persona_with_deep_modules
        
        # Get current persona
        persona = await storage.get_user_persona_by_id(persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")
        
        # Determine current level and next level
        current_level = persona.enrichmentLevel or "none"
        
        if current_level == "none" or not persona.enrichmentLevel:
            next_level = "quick"
        elif current_level == "quick":
            next_level = "strategic"
        elif current_level == "strategic":
            next_level = "complete"
        else:
            raise HTTPException(status_code=400, detail=f"Persona is already at maximum level: {current_level}")
        
        # Collect existing modules to avoid regeneration
        existing_modules = {
            "psychographicCore": persona.psychographicCore,
            "buyerJourney": persona.buyerJourney,
            "behavioralProfile": persona.behavioralProfile,
            "languageCommunication": persona.languageCommunication,
            "strategicInsights": persona.strategicInsights,
            "jobsToBeDone": persona.jobsToBeDone,
            "decisionProfile": persona.decisionProfile,
            "copyExamples": persona.copyExamples
        }
        
        print(f"[UPGRADE] {current_level.upper()} → {next_level.upper()} (reusing {sum(1 for v in existing_modules.values() if v)} existing modules)")
        
        # Perform upgrade with existing modules
        upgraded_persona = await enrich_persona_with_deep_modules(
            persona_id=persona_id,
            level=next_level,
            storage=storage,
            existing_modules=existing_modules
        )
        
        return upgraded_persona
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error upgrading persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upgrade persona: {str(e)}")

@app.delete("/api/persona/{persona_id}", status_code=204)
async def delete_user_persona(persona_id: str):
    """
    Delete a user persona by ID.
    Returns 204 No Content on success.
    """
    try:
        deleted = await storage.delete_user_persona(persona_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Persona with id {persona_id} not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting persona: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete persona: {str(e)}")

# Expert Recommendations endpoint (based on business profile)
@app.get("/api/experts/recommendations")
async def get_expert_recommendations():
    """
    Get expert recommendations based on user's business profile.
    Returns experts with relevance scores, star ratings, and justifications.
    """
    try:
        from recommendation import recommendation_engine
        
        # Get user's business profile
        user_id = "default_user"
        profile = await storage.get_business_profile(user_id)
        
        # Get all experts
        experts = await storage.get_experts()
        if not experts:
            raise HTTPException(status_code=404, detail="No experts available")
        
        # Get recommendations
        recommendations = recommendation_engine.get_recommendations(experts, profile)
        
        # Format response
        return {
            "hasProfile": profile is not None,
            "recommendations": recommendations
        }
    
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )

# Suggested Questions endpoint (personalized based on profile + expert expertise)
@app.get("/api/experts/{expert_id}/suggested-questions")
async def get_suggested_questions(expert_id: str):
    """
    Generate personalized suggested questions for a specific expert.
    Uses Perplexity AI to create context-aware questions based on:
    - User's business profile (industry, goals, challenges)
    - Expert's area of expertise
    
    Returns 3-5 highly relevant questions the user could ask.
    """
    try:
        from perplexity_research import perplexity_research
        
        # Get expert
        expert = await storage.get_expert(expert_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")
        
        # Get user's business profile
        user_id = "default_user"
        profile = await storage.get_business_profile(user_id)
        
        # Build context for Perplexity
        if profile:
            # Personalized questions based on profile
            context = f"""
Gere 5 perguntas altamente específicas e acionáveis que um empresário do setor de {profile.industry} deveria fazer para {expert.name} ({expert.title}).

Contexto do Negócio:
- Empresa: {profile.companyName}
- Setor: {profile.industry}
- Porte: {profile.companySize}
- Público-Alvo: {profile.targetAudience}
- Principais Produtos: {profile.mainProducts}
- Canais de Marketing: {', '.join(profile.channels) if profile.channels else 'Não especificado'}
- Faixa de Orçamento: {profile.budgetRange}
- Objetivo Principal: {profile.primaryGoal}
- Principal Desafio: {profile.mainChallenge}
- Prazo: {profile.timeline}

Áreas de Especialidade do Expert: {', '.join(expert.expertise[:5])}

Gere exatamente 5 perguntas que:
1. Sejam ESPECÍFICAS para a situação deste negócio (setor, porte, objetivos, desafios)
2. Aproveitem a expertise única e metodologia de {expert.name}
3. Sejam acionáveis e táticas (não teoria genérica)
4. Abordem o objetivo principal ({profile.primaryGoal}) ou desafio ({profile.mainChallenge}) do negócio
5. Sejam realistas para o orçamento dado ({profile.budgetRange}) e prazo ({profile.timeline})

IMPORTANTE: Responda SEMPRE em português brasileiro natural e fluente.
Formate cada pergunta como uma frase completa e natural que o usuário poderia fazer diretamente.
NÃO numere as perguntas nem adicione prefixos. Apenas retorne 5 perguntas, uma por linha.
"""
        else:
            # Generic questions based on expertise
            context = f"""
Gere 5 perguntas acionáveis que alguém poderia fazer para {expert.name} ({expert.title}) para obter conselhos práticos de marketing e estratégia.

Áreas de Especialidade do Expert: {', '.join(expert.expertise[:5])}

Gere exatamente 5 perguntas que:
1. Aproveitem a expertise única e metodologias de {expert.name}
2. Sejam acionáveis e táticas (não teóricas)
3. Cubram diferentes aspectos de sua expertise
4. Sejam específicas o suficiente para obter respostas úteis
5. Sejam realistas para pequenas e médias empresas

IMPORTANTE: Responda SEMPRE em português brasileiro natural e fluente.
Formate cada pergunta como uma frase completa e natural.
NÃO numere as perguntas nem adicione prefixos. Apenas retorne 5 perguntas, uma por linha.
"""
        
        # Use Perplexity to generate questions with lower temperature for consistency
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_research.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um consultor de estratégia de marketing que gera perguntas altamente específicas e acionáveis. SEMPRE responda em português brasileiro. Sempre retorne exatamente 5 perguntas, uma por linha, sem numeração ou prefixos."
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent, focused output
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse questions from response
        content = data["choices"][0]["message"]["content"]
        # Split by newlines and filter out empty lines
        questions = [q.strip() for q in content.split('\n') if q.strip()]
        
        # Clean up any numbering that might have been added despite instructions
        cleaned_questions = []
        for q in questions:
            # Remove common numbering patterns: "1. ", "1) ", "- ", "• "
            q_cleaned = q
            import re
            q_cleaned = re.sub(r'^\d+[\.\)]\s*', '', q_cleaned)  # Remove "1. " or "1) "
            q_cleaned = re.sub(r'^[-•]\s*', '', q_cleaned)  # Remove "- " or "• "
            if q_cleaned:
                cleaned_questions.append(q_cleaned)
        
        # Return up to 5 questions (in case more were generated)
        final_questions = cleaned_questions[:5]
        
        # Fallback if something went wrong
        if not final_questions:
            # Generic fallback based on expertise
            final_questions = [
                f"Como posso melhorar {expert.expertise[0].lower() if expert.expertise else 'minha estratégia'}?",
                f"Quais são as melhores práticas em {expert.expertise[1].lower() if len(expert.expertise) > 1 else 'marketing'}?",
                f"Como resolver desafios de {expert.expertise[2].lower() if len(expert.expertise) > 2 else 'negócios'}?"
            ]
        
        return {
            "expertId": expert_id,
            "expertName": expert.name,
            "questions": final_questions,
            "personalized": profile is not None
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        # Missing PERPLEXITY_API_KEY
        if "PERPLEXITY_API_KEY" in str(e):
            # Return fallback questions instead of failing
            expert = await storage.get_expert(expert_id)
            if expert:
                return {
                    "expertId": expert_id,
                    "expertName": expert.name,
                    "questions": [
                        f"Como posso melhorar {expert.expertise[0].lower() if expert.expertise else 'minha estratégia'}?",
                        f"Quais são as melhores práticas em {expert.expertise[1].lower() if len(expert.expertise) > 1 else 'marketing'}?",
                        f"Como resolver desafios de {expert.expertise[2].lower() if len(expert.expertise) > 2 else 'negócios'}?"
                    ],
                    "personalized": False
                }
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"Error generating suggested questions: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return fallback instead of failing
        try:
            expert = await storage.get_expert(expert_id)
            if expert:
                return {
                    "expertId": expert_id,
                    "expertName": expert.name,
                    "questions": [
                        f"Como posso melhorar {expert.expertise[0].lower() if expert.expertise else 'minha estratégia'}?",
                        f"Quais são as melhores práticas em {expert.expertise[1].lower() if len(expert.expertise) > 1 else 'marketing'}?",
                        f"Como resolver desafios de {expert.expertise[2].lower() if len(expert.expertise) > 2 else 'negócios'}?"
                    ],
                    "personalized": False
                }
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

# Business Insights endpoint (personalized tips based on profile)
@app.get("/api/insights")
async def get_business_insights():
    """
    Generate personalized business insights based on user's profile.
    Uses Perplexity AI to create context-aware tips and recommendations.
    
    Returns 3-4 actionable insights specific to the user's business situation.
    """
    try:
        from perplexity_research import perplexity_research
        
        # Get user's business profile
        user_id = "default_user"
        profile = await storage.get_business_profile(user_id)
        
        if not profile:
            # No profile, return empty insights
            return {
                "hasProfile": False,
                "insights": []
            }
        
        # Build context for Perplexity to generate insights
        context = f"""
Gere 4 insights de marketing específicos e acionáveis para este negócio:

Perfil do Negócio:
- Empresa: {profile.companyName}
- Setor: {profile.industry}
- Porte: {profile.companySize}
- Público-Alvo: {profile.targetAudience}
- Principais Produtos: {profile.mainProducts}
- Canais de Marketing: {', '.join(profile.channels) if profile.channels else 'Não especificado'}
- Faixa de Orçamento: {profile.budgetRange}
- Objetivo Principal: {profile.primaryGoal}
- Principal Desafio: {profile.mainChallenge}
- Prazo: {profile.timeline}

Gere exatamente 4 insights que:
1. Sejam ALTAMENTE ESPECÍFICOS para o setor ({profile.industry}), porte ({profile.companySize}) e situação deste negócio
2. Sejam ACIONÁVEIS - algo que possam implementar nos próximos 30 dias
3. Abordem o OBJETIVO PRINCIPAL ({profile.primaryGoal}) ou DESAFIO PRINCIPAL ({profile.mainChallenge})
4. Sejam realistas dado o orçamento ({profile.budgetRange}) e prazo ({profile.timeline})
5. Aproveitem tendências atuais de mercado e melhores práticas (dados 2024-2025)

Cada insight deve:
- Começar com uma categoria/tópico claro (ex: "Estratégia SEO:", "Marketing de Conteúdo:", "Anúncios Pagos:")
- Ter no máximo 1-2 frases
- Incluir táticas específicas, não conselhos genéricos
- Referenciar dados ou tendências recentes quando relevante

IMPORTANTE: Responda SEMPRE em português brasileiro natural e fluente.
Formato: Retorne 4 insights, um por linha, cada um começando com a categoria seguida de dois pontos.
NÃO numere. Formato de exemplo:
Redes Sociais: [insight específico aqui]
E-mail Marketing: [insight específico aqui]
"""
        
        # Use Perplexity to generate insights
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_research.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um estrategista de marketing que fornece insights hiper-específicos e acionáveis baseados no contexto do negócio. SEMPRE responda em português brasileiro. Sempre use dados e tendências recentes. Formate os insights como 'Categoria: insight acionável específico'."
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ],
                    "temperature": 0.4,
                    "max_tokens": 600,
                    "search_recency_filter": "month"  # Use recent data
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Parse insights from response
        content = data["choices"][0]["message"]["content"]
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Parse into structured insights (category + content)
        insights = []
        for line in lines:
            # Remove numbering if present
            import re
            line_cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
            line_cleaned = re.sub(r'^[-•]\s*', '', line_cleaned)
            
            # Try to split by first colon to get category
            if ':' in line_cleaned:
                parts = line_cleaned.split(':', 1)
                if len(parts) == 2:
                    insights.append({
                        "category": parts[0].strip(),
                        "content": parts[1].strip()
                    })
            else:
                # No colon, use whole line as content with generic category
                insights.append({
                    "category": "Dica Estratégica",
                    "content": line_cleaned
                })
        
        # Limit to 4 insights
        insights = insights[:4]
        
        # Fallback if something went wrong
        if not insights:
            insights = [
                {
                    "category": "Marketing Digital",
                    "content": f"Para empresas de {profile.industry}, foque em {profile.primaryGoal.lower()} através dos canais que você já usa."
                },
                {
                    "category": "Público-Alvo",
                    "content": f"Personalize sua mensagem para {profile.targetAudience} com conteúdo relevante e consistente."
                },
                {
                    "category": "Orçamento",
                    "content": f"Com orçamento de {profile.budgetRange}, priorize canais de alto ROI antes de expandir."
                }
            ]
        
        return {
            "hasProfile": True,
            "insights": insights,
            "profileSummary": {
                "companyName": profile.companyName,
                "industry": profile.industry,
                "primaryGoal": profile.primaryGoal
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        # Missing PERPLEXITY_API_KEY - return fallback
        if "PERPLEXITY_API_KEY" in str(e):
            user_id = "default_user"
            profile = await storage.get_business_profile(user_id)
            if profile:
                return {
                    "hasProfile": True,
                    "insights": [
                        {
                            "category": "Marketing Digital",
                            "content": f"Para empresas de {profile.industry}, foque em {profile.primaryGoal.lower()} através dos canais que você já usa."
                        },
                        {
                            "category": "Público-Alvo",
                            "content": f"Personalize sua mensagem para {profile.targetAudience} com conteúdo relevante e consistente."
                        },
                        {
                            "category": "Orçamento",
                            "content": f"Com orçamento de {profile.budgetRange}, priorize canais de alto ROI antes de expandir."
                        }
                    ],
                    "profileSummary": {
                        "companyName": profile.companyName,
                        "industry": profile.industry,
                        "primaryGoal": profile.primaryGoal
                    }
                }
            return {"hasProfile": False, "insights": []}
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"Error generating business insights: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return fallback instead of failing
        try:
            user_id = "default_user"
            profile = await storage.get_business_profile(user_id)
            if profile:
                return {
                    "hasProfile": True,
                    "insights": [
                        {
                            "category": "Marketing Digital",
                            "content": f"Para empresas de {profile.industry}, foque em {profile.primaryGoal.lower()}."
                        }
                    ],
                    "profileSummary": {
                        "companyName": profile.companyName,
                        "industry": profile.industry,
                        "primaryGoal": profile.primaryGoal
                    }
                }
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

# Council Analysis endpoints
@app.post("/api/council/analyze", response_model=CouncilAnalysis)
async def create_council_analysis(data: CouncilAnalysisCreate):
    """
    Run collaborative analysis by council of marketing legend experts.
    
    This endpoint:
    1. Conducts Perplexity research (if user has BusinessProfile)
    2. Gets independent analyses from 8 marketing legends
    3. Synthesizes consensus recommendation
    """
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    
    try:
        # Get user's business profile (optional)
        profile = await storage.get_business_profile(user_id)
        
        # Get experts to consult (all 8 if not specified)
        if data.expertIds:
            experts = []
            for expert_id in data.expertIds:
                expert = await storage.get_expert(expert_id)
                if not expert:
                    raise HTTPException(status_code=404, detail=f"Expert {expert_id} not found")
                experts.append(expert)
        else:
            # Use all available experts
            experts = await storage.get_experts()
            if not experts:
                raise HTTPException(status_code=400, detail="No experts available for analysis")
        
        # Run council analysis
        analysis = await council_orchestrator.analyze(
            problem=data.problem,
            experts=experts,
            profile=profile,
            user_id=user_id
        )
        
        # Save analysis
        await storage.save_council_analysis(analysis)
        
        return analysis
    
    except HTTPException:
        raise
    except ValueError as e:
        # Missing API keys (ANTHROPIC_API_KEY, PERPLEXITY_API_KEY)
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable: {error_msg}"
            )
        raise
    except Exception as e:
        print(f"Error creating council analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create council analysis: {str(e)}")

@app.post("/api/council/analyze-stream")
async def create_council_analysis_stream(data: CouncilAnalysisCreate):
    """
    Run collaborative analysis with Server-Sent Events streaming.
    
    Emits real-time progress events:
    - expert_started: When expert begins analysis
    - expert_researching: During Perplexity research
    - expert_analyzing: During Claude analysis
    - expert_completed: When expert finishes
    - consensus_started: Before synthesis
    - analysis_complete: Final result with full analysis
    """
    user_id = "default_user"
    
    async def event_generator():
        # Helper to format SSE events (defined outside try block for exception handling)
        def sse_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        
        try:
            # Get user's business profile (optional)
            profile = await storage.get_business_profile(user_id)
            
            # Get experts to consult
            if data.expertIds:
                experts = []
                for expert_id in data.expertIds:
                    expert = await storage.get_expert(expert_id)
                    if not expert:
                        yield sse_event("error", {"message": f"Expert {expert_id} not found"})
                        return
                    experts.append(expert)
            else:
                experts = await storage.get_experts()
                if not experts:
                    yield sse_event("error", {"message": "No experts available"})
                    return
            
            # Emit initial event with expert list
            yield sse_event("analysis_started", {
                "expertCount": len(experts),
                "experts": [{"id": e.id, "name": e.name, "avatar": e.avatar} for e in experts]
            })
            
            # Run council analysis with progress events
            # We'll need to modify council_orchestrator to emit events
            # For now, we'll simulate the workflow
            
            contributions = []
            research_findings = None
            
            # Perplexity research phase
            if profile:
                yield sse_event("research_started", {
                    "message": "Conducting market research..."
                })
                
                from perplexity_research import PerplexityResearch
                perplexity = PerplexityResearch()
                try:
                    research_result = await perplexity.research(
                        problem=data.problem,
                        profile=profile
                    )
                    research_findings = research_result.get("findings", "")
                    
                    yield sse_event("research_completed", {
                        "message": "Market research complete",
                        "citations": len(research_result.get("sources", []))
                    })
                except Exception as e:
                    yield sse_event("research_failed", {
                        "message": f"Research failed: {str(e)}"
                    })
            
            # Analyze with each expert (emitting events for each)
            from crew_council import council_orchestrator
            
            # Process experts sequentially for event emission
            for expert in experts:
                yield sse_event("expert_started", {
                    "expertId": expert.id,
                    "expertName": expert.name,
                    "message": f"{expert.name} is analyzing..."
                })
                
                try:
                    print(f"[Council Stream] Starting analysis for {expert.name}")
                    contribution = await council_orchestrator._get_expert_analysis(
                        expert=expert,
                        problem=data.problem,
                        profile=profile,
                        research_findings=research_findings
                    )
                    contributions.append(contribution)
                    print(f"[Council Stream] Completed analysis for {expert.name}")
                    
                    yield sse_event("expert_completed", {
                        "expertId": expert.id,
                        "expertName": expert.name,
                        "insightCount": len(contribution.keyInsights),
                        "recommendationCount": len(contribution.recommendations)
                    })
                except Exception as e:
                    print(f"[Council Stream] Expert {expert.name} failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    yield sse_event("expert_failed", {
                        "expertId": expert.id,
                        "expertName": expert.name,
                        "error": str(e)
                    })
            
            if not contributions:
                yield sse_event("error", {"message": "All expert analyses failed"})
                return
            
            # Synthesize consensus
            yield sse_event("consensus_started", {
                "message": "Synthesizing council consensus..."
            })
            
            print(f"[Council Stream] Synthesizing consensus from {len(contributions)} contributions")
            consensus = await council_orchestrator._synthesize_consensus(
                problem=data.problem,
                contributions=contributions,
                research_findings=research_findings
            )
            print(f"[Council Stream] Consensus generated successfully")
            
            # Create final analysis object
            from models import CouncilAnalysis, AgentContribution
            import uuid
            
            analysis = CouncilAnalysis(
                id=str(uuid.uuid4()),
                userId=user_id,
                problem=data.problem,
                profileId=profile.id if profile else None,
                marketResearch=research_findings,
                contributions=contributions,
                consensus=consensus
            )
            
            # Save analysis
            await storage.save_council_analysis(analysis)
            
            # Send final complete event
            print(f"[Council Stream] Sending analysis_complete event")
            yield sse_event("analysis_complete", {
                "analysisId": analysis.id,
                "analysis": {
                    "id": analysis.id,
                    "problem": analysis.problem,
                    "contributions": [
                        {
                            "expertId": c.expertId,
                            "expertName": c.expertName,
                            "analysis": c.analysis,
                            "keyInsights": c.keyInsights,
                            "recommendations": c.recommendations
                        }
                        for c in analysis.contributions
                    ],
                    "consensus": analysis.consensus
                }
            })
            print(f"[Council Stream] Stream completed successfully")
            
        except Exception as e:
            print(f"[Council Stream] Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield sse_event("error", {
                "message": f"Analysis failed: {str(e)}"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.get("/api/council/analyses", response_model=List[CouncilAnalysis])
async def get_council_analyses():
    """Get all council analyses for the current user"""
    # For now, use a default user_id until we add authentication
    user_id = "default_user"
    return await storage.get_council_analyses(user_id)

@app.get("/api/council/analyses/{analysis_id}", response_model=CouncilAnalysis)
async def get_council_analysis(analysis_id: str):
    """Get a specific council analysis by ID"""
    analysis = await storage.get_council_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Council analysis not found")
    return analysis

# ============================================================================
# COUNCIL ROOM CHAT ENDPOINTS (Follow-up conversational mode)
# ============================================================================

from models import CouncilChatMessage, CouncilChatRequest, StreamContribution

@app.get("/api/council/chat/{session_id}/messages", response_model=List[CouncilChatMessage])
async def get_council_chat_messages(session_id: str):
    """Get chat history for a council session"""
    messages = await storage.get_council_messages(session_id)
    return messages

@app.get("/api/council/chat/{session_id}/stream")
async def council_chat_stream(session_id: str, message: str):
    """
    Follow-up chat with council using SSE streaming.
    
    Query params:
    - message: User's follow-up question
    
    Streams expert contributions sequentially with attribution:
    - event: contribution - Individual expert response
    - event: synthesis - Final consensus
    - event: complete - End of stream
    """
    print(f"[SSE ENDPOINT] Council chat stream called - session_id={session_id}, message={message[:50]}")
    user_id = "default_user"
    
    async def event_generator():
        def sse_event(event_type: str, data: dict) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        try:
            print(f"[SSE] Starting event generator for session {session_id}")
            
            # Load session to get context
            print(f"[SSE] Loading analysis...")
            analysis = await storage.get_council_analysis(session_id)
            if not analysis:
                print(f"[SSE] ERROR: Analysis not found for session {session_id}")
                yield sse_event("error", {"message": "Council session not found"})
                return
            
            print(f"[SSE] Analysis loaded successfully - {len(analysis.contributions)} experts")
            
            # Load conversation history
            print(f"[SSE] Loading conversation history...")
            history = await storage.get_council_messages(session_id)
            print(f"[SSE] Loaded {len(history)} previous messages")
            
            # Get experts from original analysis
            expert_ids = [c.expertId for c in analysis.contributions]
            print(f"[SSE] Getting {len(expert_ids)} experts...")
            experts = []
            for expert_id in expert_ids:
                expert = await storage.get_expert(expert_id)
                if expert:
                    experts.append(expert)
            
            print(f"[SSE] Loaded {len(experts)} experts successfully")
            
            if not experts:
                print(f"[SSE] ERROR: No experts found!")
                yield sse_event("error", {"message": "No experts found for this session"})
                return
            
            # Save user message
            user_message_id = str(uuid.uuid4())
            await storage.create_council_message(
                session_id=session_id,
                role="user",
                content=message,
                contributions=None
            )
            
            yield sse_event("user_message", {
                "id": user_message_id,
                "content": message,
                "createdAt": datetime.utcnow().isoformat()
            })
            
            # Load user persona for context enrichment
            print(f"[SSE] Loading user persona...")
            persona = await storage.get_user_persona(user_id)
            if persona:
                print(f"[SSE] Persona loaded: {persona.companyName}")
            else:
                print(f"[SSE] No persona found for user")
            
            # Build context from analysis + history + persona
            print(f"[SSE] Building context...")
            context = await _build_council_context(analysis, history, message, persona)
            print(f"[SSE] Context built - {len(context)} chars")
            
            # Stream contributions from each expert (ROUNDTABLE: experts see previous contributions)
            contributions_data = []
            current_round_contributions = []  # Accumulate for roundtable discussion
            print(f"[SSE] Starting expert iteration (roundtable mode)...")
            
            for idx, expert in enumerate(experts):
                print(f"[SSE] Processing expert {idx+1}/{len(experts)}: {expert.name}")
                print(f"[SSE] Expert will see {len(current_round_contributions)} colleague contribution(s)")
                yield sse_event("expert_thinking", {
                    "expertName": expert.name,
                    "order": idx
                })
                
                # Get expert analysis with full context + colleague contributions (roundtable)
                try:
                    print(f"[SSE] Calling CrewAI for {expert.name}...")
                    contribution = await council_orchestrator._get_expert_analysis(
                        expert=expert,
                        problem=message,
                        research_findings=None,  # No new research for follow-up
                        profile=None,
                        user_id=user_id,
                        user_context={"analysis_context": context},
                        colleague_contributions=current_round_contributions  # Pass previous experts' contributions
                    )
                    print(f"[SSE] Got contribution from {expert.name} - {len(contribution.analysis)} chars")
                    
                    # Stream this expert's contribution
                    yield sse_event("contribution", {
                        "expertName": contribution.expertName,
                        "content": contribution.analysis,
                        "order": idx
                    })
                    
                    contributions_data.append(StreamContribution(
                        expertName=contribution.expertName,
                        content=contribution.analysis,
                        order=idx
                    ))
                    
                    # Add to current round for next experts to see (roundtable)
                    current_round_contributions.append({
                        "expert_name": contribution.expertName,
                        "contribution": contribution.analysis
                    })
                    print(f"[SSE] Contribution {idx+1} added to list. Next expert will see {len(current_round_contributions)} colleague(s)")
                    
                except Exception as e:
                    print(f"[SSE] ERROR: Expert {expert.name} failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Synthesize consensus
            print(f"[SSE] Starting synthesis with {len(contributions_data)} contributions...")
            yield sse_event("synthesizing", {})
            
            # Parse insights and recommendations from each contribution
            parsed_contributions = []
            for c in contributions_data:
                try:
                    insights = council_orchestrator._extract_bullet_points(c.content, "Key Insights")
                    recommendations = council_orchestrator._extract_bullet_points(c.content, "Actionable Recommendations")
                    
                    parsed_contributions.append(AgentContribution(
                        expertId="",
                        expertName=c.expertName,
                        analysis=c.content,
                        keyInsights=insights,
                        recommendations=recommendations
                    ))
                    print(f"[SSE] Parsed {c.expertName}: {len(insights)} insights, {len(recommendations)} recommendations")
                except Exception as e:
                    print(f"[SSE] Warning: Failed to parse bullet points for {c.expertName}: {str(e)}")
                    # Fallback: use contribution with full analysis text but empty structured sections
                    parsed_contributions.append(AgentContribution(
                        expertId="",
                        expertName=c.expertName,
                        analysis=c.content,
                        keyInsights=[],
                        recommendations=[]
                    ))
            
            synthesis = await council_orchestrator._synthesize_consensus(
                problem=message,
                contributions=parsed_contributions,
                research_findings=None
            )
            print(f"[SSE] Synthesis complete - {len(synthesis)} chars")
            
            yield sse_event("synthesis", {
                "content": synthesis
            })
            print(f"[SSE] Synthesis event emitted")
            
            # Save assistant message with contributions
            print(f"[SSE] Saving assistant message with {len(contributions_data)} contributions")
            contrib_dicts = [c.model_dump() for c in contributions_data]
            print(f"[SSE] Contributions data: {contrib_dicts}")
            
            message_id = await storage.create_council_message(
                session_id=session_id,
                role="assistant",
                content=synthesis,
                contributions=json.dumps(contrib_dicts)
            )
            
            print(f"[SSE] Saved message ID: {message_id}")
            
            yield sse_event("complete", {})
            
        except Exception as e:
            print(f"Council chat stream error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield sse_event("error", {"message": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def _build_council_context(
    analysis: CouncilAnalysis,
    history: List[CouncilChatMessage],
    new_question: str,
    persona: Optional['UserPersona'] = None
) -> str:
    """Build rich context for follow-up including analysis + history + persona"""
    
    # Start with persona context if available (Persona Intelligence Hub)
    context = ""
    if persona:
        context += f"""**CONTEXTO DO NEGÓCIO DO CLIENTE (Persona Intelligence Hub):**
• Empresa: {persona.companyName or 'Não especificado'}
• Indústria: {persona.industry or 'Não especificado'}
• Público-alvo: {persona.targetAudience or 'Não especificado'}
• Objetivo Principal: {persona.primaryGoal or 'Não especificado'}
• Desafio Principal: {persona.mainChallenge or 'Não especificado'}
"""
        
        # Add enrichment data if available
        if persona.campaignReferences and len(persona.campaignReferences) > 0:
            context += "\n🎥 CAMPANHAS DE REFERÊNCIA (YouTube Research):\n"
            for i, campaign in enumerate(persona.campaignReferences[:3], 1):
                # Defensive: handle both dict and Pydantic model access
                if isinstance(campaign, dict):
                    title = campaign.get('title', 'N/A')
                    channel = campaign.get('channel', 'N/A')
                else:
                    title = getattr(campaign, 'title', 'N/A')
                    channel = getattr(campaign, 'channel', 'N/A')
                
                context += f"  {i}. \"{title}\" por {channel}\n"
        
        context += "\n**INSTRUÇÃO**: Use essas informações do cliente para personalizar suas análises.\n\n---\n\n"
    
    context += f"""**CONTEXTO DA ANÁLISE INICIAL:**

Problema Original: {analysis.problem}

Consenso do Conselho:
{analysis.consensus}

"""
    
    # Add contributions from original analysis
    context += "**CONTRIBUIÇÕES ORIGINAIS DOS ESPECIALISTAS:**\n\n"
    for contrib in analysis.contributions:
        context += f"**{contrib.expertName}:**\n{contrib.analysis[:500]}...\n\n"
    
    # Add conversation history
    if history:
        context += "**HISTÓRICO DA CONVERSA:**\n\n"
        for msg in history:
            if msg.role == "user":
                context += f"User perguntou: {msg.content}\n\n"
            else:
                context += f"Conselho respondeu: {msg.content[:300]}...\n\n"
    
    context += f"\n**NOVA PERGUNTA DO USER:**\n{new_question}\n\n"
    context += """**INSTRUÇÕES:**
- Você JÁ analisou este negócio em profundidade
- Referencie insights da análise inicial quando relevante
- Continue a conversa de forma natural
- Não peça informações já fornecidas
"""
    
    return context

# ============================================================================
# PERSONA BUILDER ENDPOINTS
# ============================================================================

from models import Persona, PersonaCreate
from reddit_research import reddit_research
from datetime import datetime as dt

@app.post("/api/personas", response_model=Persona)
async def create_persona(data: PersonaCreate):
    """
    Create a persona using Reddit research.
    
    Modes:
    - quick: 1-2 min, basic insights (5-7 pain points, goals, values)
    - strategic: 5-10 min, deep analysis (behavioral patterns, content preferences)
    """
    user_id = "default_user"  # TODO: replace with actual user auth
    
    try:
        # Conduct Reddit research based on mode
        if data.mode == "quick":
            research_data = await reddit_research.research_quick(
                target_description=data.targetDescription,
                industry=data.industry
            )
        else:  # strategic
            research_data = await reddit_research.research_strategic(
                target_description=data.targetDescription,
                industry=data.industry,
                additional_context=data.additionalContext
            )
        
        # Add timestamp to research data
        research_data["researchData"]["timestamp"] = dt.utcnow().isoformat()
        
        # Generate persona name if not provided
        persona_name = f"Persona: {data.targetDescription[:50]}"
        
        # Prepare persona data
        persona_payload = {
            "name": persona_name,
            "researchMode": data.mode,
            **research_data
        }
        
        # Save to database
        persona = await storage.create_persona(user_id, persona_payload)
        
        return persona
    
    except ValueError as e:
        # Missing API keys
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Service temporarily unavailable: {error_msg}"
            )
        raise
    except Exception as e:
        print(f"Error creating persona: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")

@app.get("/api/personas", response_model=List[Persona])
async def get_personas():
    """Get all personas for the current user"""
    user_id = "default_user"
    return await storage.get_personas(user_id)

@app.get("/api/personas/{persona_id}", response_model=Persona)
async def get_persona(persona_id: str):
    """Get a specific persona by ID"""
    persona = await storage.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

@app.patch("/api/personas/{persona_id}", response_model=Persona)
async def update_persona(persona_id: str, updates: dict):
    """Update a persona (e.g., edit name, add notes)"""
    persona = await storage.update_persona(persona_id, updates)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

@app.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona"""
    success = await storage.delete_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"success": True}

@app.get("/api/personas/{persona_id}/download")
async def download_persona(persona_id: str):
    """Download persona as JSON"""
    persona = await storage.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Convert Pydantic model to dict and return as JSON download
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=persona.model_dump(mode='json'),
        headers={
            "Content-Disposition": f"attachment; filename=persona_{persona_id}.json"
        }
    )


# ============================================
# ANALYTICS & INSIGHTS DASHBOARD ENDPOINTS
# ============================================

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    """
    Get high-level analytics overview: total conversations, experts, councils, streak, last active.
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        stats = await analytics_engine.get_overview_stats(user_id)
        return stats
    except Exception as e:
        print(f"[Analytics] Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/timeline")
async def get_analytics_timeline(days: int = 30):
    """
    Get activity timeline for last N days.
    Returns array of {date, chats, councils, total}
    """
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        user_id = "default"  # TODO: Get from auth context
        timeline = await analytics_engine.get_activity_timeline(user_id=user_id, days=days)
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analytics] Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/top-experts")
async def get_top_experts(limit: int = 10):
    """
    Get ranking of most consulted experts.
    Returns array of {expertId, expertName, category, consultations, lastConsulted, avatar}
    """
    try:
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
        
        user_id = "default"  # TODO: Get from auth context
        experts = await analytics_engine.get_top_experts(user_id=user_id, limit=limit)
        return experts
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analytics] Error getting top experts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/categories")
async def get_category_distribution():
    """
    Get consultation count by category.
    Returns object like {categoryName: count}
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        categories = await analytics_engine.get_category_distribution(user_id=user_id)
        return categories
    except Exception as e:
        print(f"[Analytics] Error getting category distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/highlights")
async def get_analytics_highlights():
    """
    Get user's saved favorites and top insights.
    Returns {favoriteMessages, topCouncilInsights, referencedCampaigns}
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        highlights = await analytics_engine.get_highlights(user_id)
        return highlights
    except Exception as e:
        print(f"[Analytics] Error getting highlights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/recommendations")
async def get_analytics_recommendations():
    """
    Generate AI-powered recommendations based on usage patterns.
    Returns array of {type, title, description, action}
    """
    try:
        user_id = "default"  # TODO: Get from auth context
        recommendations = await analytics_engine.generate_recommendations(user_id)
        return recommendations
    except Exception as e:
        print(f"[Analytics] Error generating recommendations: {e}")
        # Return fallback instead of error
        return [{
            "type": "system_message",
            "title": "Continue explorando",
            "description": "Consulte mais especialistas para receber recomendações personalizadas!",
            "action": "Ver Categorias"
        }]


@app.post("/api/analytics/seed")
async def seed_analytics():
    """
    Seed analytics database with 30 days of realistic test data.
    For development/testing only.
    """
    try:
        await seed_analytics_data()
        return {"success": True, "message": "Analytics data seeded successfully"}
    except Exception as e:
        print(f"[Analytics] Error seeding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analytics/seed")
async def clear_analytics():
    """
    Clear all analytics data. For development/testing only.
    """
    try:
        await clear_analytics_data()
        return {"success": True, "message": "Analytics data cleared successfully"}
    except Exception as e:
        print(f"[Analytics] Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
