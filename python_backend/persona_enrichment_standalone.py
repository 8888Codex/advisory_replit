"""
STANDALONE PERSONA ENRICHMENT - Runs in background task with own connection

This module provides enrichment that works in a separate event loop
with its own database connection (no storage.pool dependency).
"""

import json
import os
from typing import Dict, Any, Literal
import anthropic
from googleapiclient.discovery import build
from datetime import datetime
import httpx


async def enrich_persona_complete_standalone(
    conn,  # asyncpg connection
    persona_id: str,
    persona_data: Dict[str, Any],
    level: Literal["quick", "strategic", "complete"]
) -> Dict[str, Any]:
    """
    COMPLETE PERSONA ENRICHMENT - Standalone version for background tasks
    
    Works with a dedicated asyncpg connection (no storage.pool dependency).
    Generates ALL 8 modules + YouTube research.
    
    Args:
        conn: asyncpg connection (dedicated to this task)
        persona_id: ID of persona to enrich
        persona_data: Dict with company_name, industry, target_audience, etc.
        level: "quick" (3 modules) | "strategic" (6 modules) | "complete" (8 modules)
    
    Returns:
        Dict with all enriched modules
    """
    
    print(f"[STANDALONE ENRICHMENT] Starting {level.upper()} enrichment...")
    print(f"[STANDALONE ENRICHMENT] Company: {persona_data['company_name']}")
    print(f"[STANDALONE ENRICHMENT] Industry: {persona_data['industry']}")
    
    # Initialize API clients
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    all_modules = {}
    
    # ========================================================================
    # PHASE 0: REDDIT RESEARCH (via Perplexity)
    # ========================================================================
    print(f"[STANDALONE ENRICHMENT] Phase 0: Reddit Research via Perplexity...")
    
    reddit_insights = {
        'communities': [],
        'painPoints': [],
        'goals': [],
        'values': [],
        'language': '',
        'sentiment': {
            'overall': 'neutral',
            'breakdown': {},
            'summary': ''
        },
        'trendingTopics': []
    }
    
    if perplexity_api_key:
        try:
            # Build Reddit research query with advanced analytics
            reddit_query = f"""
Analise o público-alvo descrito abaixo e identifique baseado em discussões reais do Reddit brasileiro e internacional:

**Empresa:** {persona_data['company_name']}
**Indústria:** {persona_data['industry']}
**Público-Alvo:** {persona_data['target_audience']}
**Objetivo:** {persona_data['primary_goal']}
**Desafio:** {persona_data['main_challenge']}

Identifique:

1. **Comunidades no Reddit** (5 subreddits relevantes)
2. **Pain Points** (8 frustrações específicas que esse público menciona)
3. **Goals** (8 objetivos que buscam alcançar)
4. **Values** (8 valores que guiam suas decisões)
5. **Linguagem Autêntica** (como eles se expressam, palavras-chave que usam)
6. **Sentiment Analysis** (analise o tom geral das discussões):
   - Tom geral: positive, neutral ou negative
   - Breakdown por comunidade (sentimento em cada subreddit)
   - Summary: descrição breve do sentimento geral observado
7. **Trending Topics** (5-8 tópicos em alta nas comunidades):
   - Topic: nome do tópico/assunto
   - Mentions: estimativa de frequência (high/medium/low)
   - Trend: rising, stable ou declining
   - Relevance: por que é relevante para este público

Retorne JSON estruturado:
{{
  "communities": ["r/subreddit1", "r/subreddit2", ...],
  "painPoints": ["dor 1", "dor 2", ...],
  "goals": ["objetivo 1", "objetivo 2", ...],
  "values": ["valor 1", "valor 2", ...],
  "language": "descrição de como se comunicam",
  "sentiment": {{
    "overall": "positive|neutral|negative",
    "breakdown": {{
      "r/subreddit1": "positive",
      "r/subreddit2": "neutral"
    }},
    "summary": "Descrição breve do sentimento geral"
  }},
  "trendingTopics": [
    {{
      "topic": "nome do tópico",
      "mentions": "high|medium|low",
      "trend": "rising|stable|declining",
      "relevance": "por que é relevante para o público"
    }}
  ]
}}
"""
            
            print(f"[REDDIT] Chamando Perplexity API...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar",
                        "messages": [
                            {"role": "system", "content": "Você é um especialista em pesquisa de audiência. Retorne APENAS JSON válido."},
                            {"role": "user", "content": reddit_query}
                        ],
                        "temperature": 0.2
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        findings_text = result["choices"][0]["message"]["content"]
                        
                        # Parse JSON from response
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', findings_text)
                        if json_match:
                            parsed_insights = json.loads(json_match.group(0))
                            
                            # Extract base fields
                            reddit_insights['communities'] = parsed_insights.get('communities', [])
                            reddit_insights['painPoints'] = parsed_insights.get('painPoints', [])
                            reddit_insights['goals'] = parsed_insights.get('goals', [])
                            reddit_insights['values'] = parsed_insights.get('values', [])
                            reddit_insights['language'] = parsed_insights.get('language', '')
                            
                            # Extract sentiment (with fallback)
                            if 'sentiment' in parsed_insights:
                                reddit_insights['sentiment'] = {
                                    'overall': parsed_insights['sentiment'].get('overall', 'neutral'),
                                    'breakdown': parsed_insights['sentiment'].get('breakdown', {}),
                                    'summary': parsed_insights['sentiment'].get('summary', '')
                                }
                            
                            # Extract trending topics (with fallback)
                            if 'trendingTopics' in parsed_insights:
                                reddit_insights['trendingTopics'] = parsed_insights['trendingTopics']
                            
                            # Logging
                            print(f"[REDDIT] ✅ Coletou {len(reddit_insights.get('communities', []))} comunidades")
                            print(f"[REDDIT] ✅ Coletou {len(reddit_insights.get('painPoints', []))} pain points")
                            print(f"[REDDIT] ✅ Sentiment: {reddit_insights['sentiment']['overall']}")
                            print(f"[REDDIT] ✅ Coletou {len(reddit_insights.get('trendingTopics', []))} trending topics")
                        else:
                            print(f"[REDDIT] ⚠️  Não conseguiu extrair JSON da resposta")
                else:
                    print(f"[REDDIT] ⚠️  Perplexity API retornou {response.status_code}")
        except Exception as e:
            print(f"[REDDIT] ⚠️  Erro ao buscar dados do Reddit: {str(e)}")
    else:
        print(f"[REDDIT] ⚠️  PERPLEXITY_API_KEY não configurada, pulando Reddit research")
    
    # Save Reddit insights to database
    await conn.execute("""
        UPDATE user_personas
        SET reddit_insights = $2::jsonb
        WHERE id = $1
    """,
        persona_id,
        json.dumps(reddit_insights)
    )
    print(f"[DB] Saved reddit_insights to database (with sentiment and trending topics)")
    
    # ========================================================================
    # PHASE 1: YOUTUBE RESEARCH
    # ========================================================================
    print(f"[STANDALONE ENRICHMENT] Phase 1: YouTube Research...")
    
    youtube_videos = []
    youtube_insights = []
    
    if youtube_api_key:
        try:
            youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            
            # Search queries based on industry
            search_queries = [
                f"{persona_data['industry']} marketing strategy",
                f"{persona_data['target_audience']} buyer persona",
                f"{persona_data['primary_goal']} case study"
            ]
            
            for query in search_queries[:2]:  # Limit for quick mode
                print(f"[YOUTUBE] Searching: {query}")
                search_response = youtube.search().list(
                    q=query,
                    part='id,snippet',
                    maxResults=5,
                    type='video',
                    order='relevance'
                ).execute()
                
                for item in search_response.get('items', []):
                    video_id = item['id']['videoId']
                    snippet = item['snippet']
                    
                    # Get video statistics
                    stats_response = youtube.videos().list(
                        part='statistics',
                        id=video_id
                    ).execute()
                    
                    stats = stats_response['items'][0]['statistics'] if stats_response.get('items') else {}
                    
                    youtube_videos.append({
                        'videoId': video_id,
                        'title': snippet['title'],
                        'channel': snippet['channelTitle'],
                        'viewCount': int(stats.get('viewCount', 0)),
                        'likeCount': int(stats.get('likeCount', 0)),
                        'publishedAt': snippet['publishedAt'],
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
            
            print(f"[YOUTUBE] Found {len(youtube_videos)} videos")
            
            # Generate insights from videos
            if youtube_videos:
                videos_summary = "\n".join([
                    f"- {v['title']} ({v['viewCount']:,} views, {v['channel']})"
                    for v in youtube_videos[:10]
                ])
                
                insights_prompt = f"""Analise estes vídeos do YouTube sobre {persona_data['industry']}:

{videos_summary}

Extraia 5 insights principais sobre:
1. O que funciona nesta indústria
2. Tendências emergentes
3. Pontos de dor comuns do público
4. Estratégias de sucesso
5. Erros comuns a evitar

Retorne JSON com lista de insights (cada um com title e description).
"""
                
                response = anthropic_client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": insights_prompt}]
                )
                
                insights_data = json.loads(response.content[0].text)
                youtube_insights = insights_data.get('insights', [])
                
        except Exception as e:
            print(f"[YOUTUBE] Warning: {str(e)}")
            youtube_videos = []
            youtube_insights = []
    
    # Save YouTube data
    await conn.execute("""
        UPDATE user_personas
        SET youtube_research = $2::jsonb,
            video_insights = $3::jsonb
        WHERE id = $1
    """,
        persona_id,
        json.dumps([{"query": "marketing", "videos": youtube_videos}]),
        json.dumps(youtube_insights)
    )
    
    all_modules['youtube'] = {
        'videos': youtube_videos,
        'insights': youtube_insights
    }
    
    # ========================================================================
    # PHASE 2: DEEP PERSONA MODULES (Com Reddit + YouTube Context)
    # ========================================================================
    print(f"[STANDALONE ENRICHMENT] Phase 2: Generating Deep Modules...")
    
    # Module configurations based on level
    modules_to_generate = {
        'quick': ['psychographicCore', 'buyerJourney', 'strategicInsights'],
        'strategic': ['psychographicCore', 'buyerJourney', 'behavioralProfile', 
                      'languageCommunication', 'strategicInsights', 'jobsToBeDone'],
        'complete': ['psychographicCore', 'buyerJourney', 'behavioralProfile',
                     'languageCommunication', 'strategicInsights', 'jobsToBeDone',
                     'decisionProfile', 'copyExamples']
    }
    
    modules_list = modules_to_generate[level]
    
    # Generate each module
    for module_name in modules_list:
        print(f"[MODULES] Generating: {module_name}...")
        
        module_data = await generate_persona_module(
            anthropic_client=anthropic_client,
            module_name=module_name,
            persona_data=persona_data,
            youtube_context=youtube_videos[:5],
            reddit_context=reddit_insights,
            level=level
        )
        
        all_modules[module_name] = module_data
        
        # Save to database incrementally
        await save_module_to_db(conn, persona_id, module_name, module_data)
    
    # ========================================================================
    # PHASE 3: BASE FIELDS (pain points, goals, values) - Com Reddit Data
    # ========================================================================
    print(f"[STANDALONE ENRICHMENT] Phase 3: Base Fields...")
    
    # Use Reddit data as starting point if available, then enrich with Claude
    base_data = {}
    
    if reddit_insights.get('painPoints') or reddit_insights.get('goals') or reddit_insights.get('values'):
        print(f"[BASE FIELDS] Usando dados do Reddit como base...")
        base_data = {
            'painPoints': reddit_insights.get('painPoints', []),
            'goals': reddit_insights.get('goals', []),
            'values': reddit_insights.get('values', []),
            'communities': reddit_insights.get('communities', [])
        }
        print(f"[BASE FIELDS] Reddit forneceu: {len(base_data['painPoints'])} pain points, {len(base_data['goals'])} goals, {len(base_data['values'])} values")
    
    # Enrich with Claude if needed (to reach 8 items each)
    if len(base_data.get('painPoints', [])) < 8 or len(base_data.get('goals', [])) < 8:
        print(f"[BASE FIELDS] Enriquecendo com Claude para completar dados...")
        
        base_fields_prompt = f"""Com base nesta persona:

Empresa: {persona_data['company_name']}
Indústria: {persona_data['industry']}
Público: {persona_data['target_audience']}
Objetivo: {persona_data['primary_goal']}
Desafio: {persona_data['main_challenge']}

Dados existentes do Reddit:
- Pain Points: {json.dumps(base_data.get('painPoints', []), ensure_ascii=False)}
- Goals: {json.dumps(base_data.get('goals', []), ensure_ascii=False)}
- Values: {json.dumps(base_data.get('values', []), ensure_ascii=False)}
- Communities: {json.dumps(base_data.get('communities', []), ensure_ascii=False)}

Contexto YouTube:
{json.dumps(youtube_insights[:3], indent=2) if youtube_insights else 'Não disponível'}

Complete para atingir 8 itens em cada lista (adicione apenas o que falta):
- painPoints: lista de 8 pontos de dor específicos e detalhados
- goals: lista de 8 objetivos e aspirações claras
- values: lista de 8 valores importantes que guiam decisões
- communities: lista de 5 comunidades/grupos que este público frequenta

Retorne apenas JSON válido com TODOS os itens (existentes + novos).
"""
    
        response = anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": base_fields_prompt}]
        )
        
        # Parse JSON robustly
        response_text = response.content[0].text
        try:
            claude_data = json.loads(response_text)
            base_data = claude_data
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                claude_data = json.loads(json_match.group(0))
                base_data = claude_data
            else:
                print(f"[ERROR] Could not parse base fields JSON")
                print(f"[ERROR] Response: {response_text[:500]}")
                # Keep Reddit data if parsing failed
    else:
        print(f"[BASE FIELDS] Dados do Reddit já completos, pulando Claude enrichment")
    
    await conn.execute("""
        UPDATE user_personas
        SET pain_points = $2::jsonb,
            goals = $3::jsonb,
            values = $4::jsonb,
            communities = $5::jsonb,
            research_completeness = 100
        WHERE id = $1
    """,
        persona_id,
        json.dumps(base_data.get('painPoints', [])),
        json.dumps(base_data.get('goals', [])),
        json.dumps(base_data.get('values', [])),
        json.dumps(base_data.get('communities', []))
    )
    
    all_modules['baseFields'] = base_data
    
    print(f"[STANDALONE ENRICHMENT] ✅ Enrichment COMPLETE!")
    print(f"[STANDALONE ENRICHMENT] Modules generated: {len(all_modules)}")
    print(f"[STANDALONE ENRICHMENT] YouTube videos: {len(youtube_videos)}")
    
    return all_modules


async def generate_persona_module(
    anthropic_client,
    module_name: str,
    persona_data: Dict[str, Any],
    youtube_context: list,
    reddit_context: dict,
    level: str
) -> Dict[str, Any]:
    """Generate a single persona module using Claude with Reddit + YouTube context"""
    
    # Build Reddit context string
    reddit_context_str = ""
    if reddit_context.get('communities'):
        reddit_context_str += f"\n\n**Comunidades no Reddit:** {', '.join(reddit_context['communities'])}"
    if reddit_context.get('painPoints'):
        reddit_context_str += f"\n\n**Pain Points do Reddit:**\n" + "\n".join([f"- {p}" for p in reddit_context['painPoints'][:5]])
    if reddit_context.get('language'):
        reddit_context_str += f"\n\n**Linguagem Autêntica:** {reddit_context['language']}"
    
    # Module-specific prompts
    prompts = {
        'psychographicCore': f"""Crie o PSYCHOGRAPHIC CORE para esta persona:

Empresa: {persona_data['company_name']}
Indústria: {persona_data['industry']}
Público: {persona_data['target_audience']}
Objetivo: {persona_data['primary_goal']}
{reddit_context_str}

Retorne JSON com:
{{
    "demographics": {{"age": "...", "location": "...", "education": "...", "income": "..."}},
    "psychographics": {{"personality": "...", "lifestyle": "...", "interests": [...]}},
    "motivations": {{"intrinsic": [...], "extrinsic": [...]}},
    "fears": [...],
    "aspirations": [...]
}}
""",
        
        'buyerJourney': f"""Mapeie a BUYER JOURNEY completa para:

Empresa: {persona_data['company_name']}
Indústria: {persona_data['industry']}
Público: {persona_data['target_audience']}
{reddit_context_str}

Retorne JSON com 5 estágios detalhados:
{{
    "awareness": {{"stage": "...", "painPoints": [...], "contentTypes": [...], "channels": [...]}},
    "consideration": {{"evaluationCriteria": [...], "competitors": [...], "objections": [...]}},
    "decision": {{"triggers": [...], "barriers": [...], "successFactors": [...]}},
    "retention": {{"onboarding": [...], "engagement": [...], "expansion": [...]}},
    "advocacy": {{"triggers": [...], "channels": [...], "rewards": [...]}}
}}
""",
        
        'behavioralProfile': f"""Crie o BEHAVIORAL PROFILE para:

Indústria: {persona_data['industry']}
Público: {persona_data['target_audience']}
{reddit_context_str}

Retorne JSON detalhado:
{{
    "onlineBehavior": {{"platforms": [...], "activityPatterns": [...], "contentConsumption": [...]}},
    "purchaseBehavior": {{"frequency": "...", "averageValue": "...", "triggers": [...]}},
    "decisionMaking": {{"style": "...", "timeframe": "...", "influencers": [...]}},
    "engagement": {{"preferredChannels": [...], "responsePatterns": [...], "optimalTiming": [...]}}
}}
""",
        
        'languageCommunication': f"""Analise LANGUAGE & COMMUNICATION para:

Público: {persona_data['target_audience']}
Indústria: {persona_data['industry']}
{reddit_context_str}

Retorne JSON:
{{
    "vocabulary": {{"preferredTerms": [...], "jargonLevel": "...", "avoidTerms": [...]}},
    "communicationStyle": {{"tone": "...", "formality": "...", "pace": "..."}},
    "contentPreferences": {{"formats": [...], "length": "...", "visualElements": [...]}},
    "messaging": {{"keyThemes": [...], "emotionalTriggers": [...], "proofPoints": [...]}}
}}
""",
        
        'strategicInsights': f"""Gere STRATEGIC INSIGHTS para:

Empresa: {persona_data['company_name']}
Indústria: {persona_data['industry']}
Objetivo: {persona_data['primary_goal']}
Desafio: {persona_data['main_challenge']}
{reddit_context_str}

Contexto YouTube: {json.dumps(youtube_context[:3], indent=2) if youtube_context else 'Não disponível'}

Retorne JSON:
{{
    "opportunities": [Lista de 8 oportunidades específicas],
    "threats": [Lista de 6 ameaças/riscos],
    "recommendations": [Lista de 10 recomendações acionáveis],
    "quickWins": [Lista de 5 ações rápidas],
    "longTermStrategy": [Lista de 5 iniciativas estratégicas]
}}
""",
        
        'jobsToBeDone': f"""Mapeie JOBS TO BE DONE para:

Público: {persona_data['target_audience']}
Indústria: {persona_data['industry']}
Objetivo: {persona_data['primary_goal']}
{reddit_context_str}

Retorne JSON:
{{
    "functionalJobs": [Lista de 6 jobs funcionais],
    "emotionalJobs": [Lista de 6 jobs emocionais],
    "socialJobs": [Lista de 4 jobs sociais],
    "contextualFactors": [Lista de fatores contextuais],
    "successCriteria": [Como sabem que job foi cumprido]
}}
""",
        
        'decisionProfile': f"""Crie DECISION PROFILE para:

Público: {persona_data['target_audience']}
Indústria: {persona_data['industry']}

Retorne JSON:
{{
    "decisionMakers": [Lista de envolvidos na decisão],
    "decisionCriteria": [Lista de critérios de avaliação],
    "decisionProcess": {{"steps": [...], "timeframe": "...", "approvalLevels": [...]}},
    "influencers": {{"internal": [...], "external": [...]}},
    "riskTolerance": "...",
    "budgetConsiderations": [...]
}}
""",
        
        'copyExamples': f"""Crie COPY EXAMPLES para:

Empresa: {persona_data['company_name']}
Público: {persona_data['target_audience']}
Objetivo: {persona_data['primary_goal']}

Retorne JSON com exemplos práticos:
{{
    "emailSubjects": [Lista de 8 subject lines],
    "headlines": [Lista de 8 headlines poderosas],
    "ctaButtons": [Lista de 8 CTAs],
    "socialPosts": [Lista de 6 posts para social media],
    "adCopy": [Lista de 4 ads curtos e persuasivos],
    "landingPageHero": [3 versões de hero section]
}}
"""
    }
    
    prompt = prompts.get(module_name, f"Generate {module_name} for {persona_data['company_name']}")
    
    # Use Haiku for all modules (Sonnet not available in this API key)
    model = "claude-3-5-haiku-20241022"
    
    # Use higher max_tokens for complex modules
    max_tokens = 3000 if module_name in ['copyExamples', 'strategicInsights', 'buyerJourney'] else 2000
    
    response = anthropic_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse JSON robustly (Claude sometimes adds text before/after JSON)
    response_text = response.content[0].text
    
    try:
        module_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            module_data = json.loads(json_match.group(0))
        else:
            print(f"[ERROR] Could not parse JSON for {module_name}")
            print(f"[ERROR] Response: {response_text[:500]}")
            # Return empty dict as fallback
            module_data = {}
    
    return module_data


async def save_module_to_db(conn, persona_id: str, module_name: str, module_data: Dict[str, Any]):
    """Save a module to the database"""
    
    # Map module names to database columns
    column_mapping = {
        'psychographicCore': 'psychographic_core',
        'buyerJourney': 'buyer_journey',
        'behavioralProfile': 'behavioral_profile',
        'languageCommunication': 'language_communication',
        'strategicInsights': 'strategic_insights',
        'jobsToBeDone': 'jobs_to_be_done',
        'decisionProfile': 'decision_profile',
        'copyExamples': 'copy_examples'
    }
    
    db_column = column_mapping.get(module_name)
    
    if db_column:
        await conn.execute(f"""
            UPDATE user_personas
            SET {db_column} = $2::jsonb
            WHERE id = $1
        """,
            persona_id,
            json.dumps(module_data)  # asyncpg converte para JSONB com ::jsonb cast
        )
        print(f"[DB] Saved {module_name} to database")

