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
    
    all_modules = {}
    
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
    # PHASE 2: DEEP PERSONA MODULES
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
            level=level
        )
        
        all_modules[module_name] = module_data
        
        # Save to database incrementally
        await save_module_to_db(conn, persona_id, module_name, module_data)
    
    # ========================================================================
    # PHASE 3: BASE FIELDS (pain points, goals, values)
    # ========================================================================
    print(f"[STANDALONE ENRICHMENT] Phase 3: Base Fields...")
    
    base_fields_prompt = f"""Com base nesta persona:

Empresa: {persona_data['company_name']}
Indústria: {persona_data['industry']}
Público: {persona_data['target_audience']}
Objetivo: {persona_data['primary_goal']}
Desafio: {persona_data['main_challenge']}

Contexto YouTube:
{json.dumps(youtube_insights[:3], indent=2)}

Gere dados estruturados:
- painPoints: lista de 8 pontos de dor específicos e detalhados
- goals: lista de 8 objetivos e aspirações claras
- values: lista de 8 valores importantes que guiam decisões
- communities: lista de 5 comunidades/grupos que este público frequenta

Retorne apenas JSON válido.
"""
    
    response = anthropic_client.messages.create(
        model="claude-3-5-haiku-20241022",  # Using Haiku (Sonnet not available)
        max_tokens=2000,
        messages=[{"role": "user", "content": base_fields_prompt}]
    )
    
    # Parse JSON robustly
    response_text = response.content[0].text
    try:
        base_data = json.loads(response_text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            base_data = json.loads(json_match.group(0))
        else:
            print(f"[ERROR] Could not parse base fields JSON")
            print(f"[ERROR] Response: {response_text[:500]}")
            base_data = {
                'painPoints': [],
                'goals': [],
                'values': [],
                'communities': []
            }
    
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
    level: str
) -> Dict[str, Any]:
    """Generate a single persona module using Claude"""
    
    # Module-specific prompts
    prompts = {
        'psychographicCore': f"""Crie o PSYCHOGRAPHIC CORE para esta persona:

Empresa: {persona_data['company_name']}
Indústria: {persona_data['industry']}
Público: {persona_data['target_audience']}
Objetivo: {persona_data['primary_goal']}

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

Contexto YouTube: {json.dumps(youtube_context[:3], indent=2)}

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

