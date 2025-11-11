"""
Persona Enrichment Orchestrator for YouTube Research Integration

This module orchestrates the enrichment of user personas with YouTube research data,
including campaign references, video insights, and curated content recommendations.

UPDATED: Now integrates 8-Module Deep Persona System (Quick/Strategic/Complete)
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Literal, Optional
from models import UserPersona, PersonaEnrichmentResult
from tools.youtube_api import YouTubeAPITool
from persona_generator import PersonaOrchestrator

RESEARCH_DEPTH = {
    "quick": 2,      # 2 YouTube queries
    "strategic": 5,  # 5 YouTube queries
    "complete": 10   # 10 YouTube queries
}


def generate_youtube_queries(persona: UserPersona) -> List[str]:
    """
    Generate 2-10 YouTube search queries based on persona data.
    
    Uses industry, targetAudience, primaryGoal, mainChallenge to create
    targeted search queries for finding relevant campaigns and case studies.
    
    Args:
        persona: UserPersona object with business context
        
    Returns:
        List[str] of YouTube search queries (2-10 queries)
        
    Examples:
        - "{industry} marketing campaigns 2024"
        - "{targetAudience} case studies"
        - "successful {primaryGoal} strategies {industry}"
    """
    queries = []
    
    industry = persona.industry or "marketing"
    target_audience = persona.targetAudience or "consumers"
    primary_goal = persona.primaryGoal or "growth"
    main_challenge = persona.mainChallenge or "customer acquisition"
    
    # Core campaign queries (always include)
    queries.append(f"{industry} marketing campaigns 2024")
    queries.append(f"{target_audience} case studies")
    
    # Goal-oriented queries
    if primary_goal:
        queries.append(f"successful {primary_goal} strategies {industry}")
        queries.append(f"{primary_goal} {industry} examples")
    
    # Challenge-focused queries
    if main_challenge:
        queries.append(f"solving {main_challenge} {industry}")
        queries.append(f"{main_challenge} solutions {industry}")
    
    # Audience-specific queries
    if target_audience:
        queries.append(f"marketing to {target_audience} best practices")
        queries.append(f"{target_audience} engagement campaigns")
    
    # Industry innovation queries
    queries.append(f"{industry} viral campaigns")
    queries.append(f"{industry} marketing innovation 2024")
    
    return queries[:10]


async def synthesize_video_insights(results: List[dict], persona: UserPersona) -> dict:
    """
    Extract key insights from real YouTube video data using LLM Router.
    
    Analyzes authentic YouTube videos with real statistics (views, likes, dates)
    and synthesizes them into structured insights and recommendations.
    
    Args:
        results: List of YouTube API results with real video data
        persona: UserPersona object for context
        
    Returns:
        Dict containing:
            - key_insights: List[str] - Top insights across videos
            - campaigns: List[dict] - Real videos with statistics (videoId, title, url, channel, views, likes, publishedAt)
            - top_videos: List[dict] - Top 3-5 curated videos with real metrics
    """
    
    # Format real YouTube data for Claude analysis
    video_summaries = []
    for result in results:
        query = result.get("query", "")
        videos = result.get("videos", [])
        
        if videos:
            video_list = []
            for v in videos[:5]:  # Top 5 videos per query
                video_list.append(
                    f"  - {v['title']}\n"
                    f"    Canal: {v['channelTitle']}\n"
                    f"    Views: {v['statistics']['viewCount']:,}\n"
                    f"    Likes: {v['statistics']['likeCount']:,}\n"
                    f"    Publicado: {v['publishedAt'][:10]}\n"
                    f"    URL: {v['url']}"
                )
            
            video_summaries.append(
                f"Query: {query}\n"
                f"Vídeos encontrados ({len(videos)} total):\n" + 
                "\n\n".join(video_list)
            )
    
    combined_data = "\n\n---\n\n".join(video_summaries)
    
    synthesis_prompt = f"""Você é um analista de marketing especializado em curadoria de vídeos do YouTube com dados REAIS.

Analise os vídeos REAIS do YouTube abaixo (com estatísticas verificadas) e extraia insights acionáveis para uma empresa no setor de {persona.industry or 'marketing'}.

Contexto do cliente:
- Público-alvo: {persona.targetAudience or 'geral'}
- Objetivo principal: {persona.primaryGoal or 'crescimento'}
- Desafio principal: {persona.mainChallenge or 'aquisição de clientes'}

Vídeos Reais do YouTube:
{combined_data}

Forneça sua análise em formato JSON com a seguinte estrutura:
{{
    "key_insights": [
        "Insight baseado em tendências dos vídeos de alta performance",
        "Insight sobre estratégias que geraram mais engajamento",
        "Insight sobre padrões de conteúdo bem-sucedido",
        ...
    ],
    "campaigns": [
        {{
            "videoId": "ID real extraído da URL",
            "title": "Título do vídeo",
            "url": "URL completa",
            "channel": "Nome do canal",
            "viewCount": 123456,
            "likeCount": 5000,
            "publishedAt": "2024-01-15",
            "insights": ["Insight específico baseado nas métricas deste vídeo"]
        }}
    ],
    "top_videos": [
        {{
            "videoId": "ID do vídeo",
            "title": "Título",
            "url": "URL",
            "channel": "Canal",
            "viewCount": 123456,
            "likeCount": 5000,
            "publishedAt": "2024-01-15",
            "relevanceScore": 5,
            "reason": "Relevância baseada em métricas e alinhamento com objetivos"
        }}
    ]
}}

IMPORTANTE:
1. Use APENAS dados REAIS dos vídeos fornecidos (nunca invente exemplos)
2. Baseie insights nas métricas reais (views, likes, data de publicação)
3. Identifique padrões de alta performance (vídeos com mais engajamento)
4. Selecione 3-5 vídeos MAIS relevantes baseado em métricas + alinhamento com objetivos
5. Inclua viewCount, likeCount, publishedAt em TODOS os vídeos
6. RETORNE APENAS O JSON, sem texto adicional."""

    from llm_router import llm_router, LLMTask
    import json
    
    synthesis_text = await llm_router.generate_text(
        task=LLMTask.SYNTHESIS,
        prompt=synthesis_prompt,
        max_tokens=4000,
        temperature=0.2
    )
    
    synthesis_text = synthesis_text.strip()
    
    if synthesis_text.startswith("```json"):
        synthesis_text = synthesis_text[7:]
    if synthesis_text.startswith("```"):
        synthesis_text = synthesis_text[3:]
    if synthesis_text.endswith("```"):
        synthesis_text = synthesis_text[:-3]
    synthesis_text = synthesis_text.strip()
    
    try:
        synthesis = json.loads(synthesis_text)
    except json.JSONDecodeError:
        synthesis = {
            "key_insights": ["Análise de vídeos em andamento"],
            "campaigns": [],
            "top_videos": []
        }
    
    return synthesis


async def enrich_persona_with_youtube(
    persona_id: str, 
    mode: str, 
    storage
) -> PersonaEnrichmentResult:
    """
    Main orchestrator function for YouTube enrichment.
    
    Executes the complete enrichment workflow:
    1. Load persona from storage
    2. Generate search queries
    3. Execute parallel YouTube research
    4. Synthesize insights with Claude
    5. Update persona in storage
    6. Return enrichment results
    
    Args:
        persona_id: ID of the persona to enrich
        mode: Research depth - "quick" (2), "strategic" (5), "complete" (10)
        storage: Storage instance with persona operations
        
    Returns:
        PersonaEnrichmentResult with stats and updated completeness score
        
    Raises:
        ValueError: If persona not found or invalid mode
    """
    if mode not in RESEARCH_DEPTH:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {list(RESEARCH_DEPTH.keys())}")
    
    persona = await storage.get_user_persona_by_id(persona_id)
    if not persona:
        raise ValueError(f"Persona with id '{persona_id}' not found")
    
    queries = generate_youtube_queries(persona)
    max_queries = RESEARCH_DEPTH[mode]
    selected_queries = queries[:max_queries]
    
    print(f"[ENRICHMENT] Executing {len(selected_queries)} REAL YouTube API queries in parallel...")
    
    # Initialize YouTube API client
    youtube_api = YouTubeAPITool()
    
    try:
        # Execute parallel YouTube API searches
        tasks = [
            youtube_api.search_videos(
                query=query,
                max_results=10,
                order="relevance",
                published_after="2023-01-01T00:00:00Z"  # Last 2 years
            )
            for query in selected_queries
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[ENRICHMENT] Query {i+1} failed: {result}")
            elif isinstance(result, dict):
                if result.get("error"):
                    print(f"[ENRICHMENT] Query {i+1} error: {result['error']}")
                elif result.get("videos"):
                    valid_results.append(result)
                    print(f"[ENRICHMENT] Query {i+1}: Found {len(result['videos'])} REAL videos")
                else:
                    print(f"[ENRICHMENT] Query {i+1}: No videos found")
        
        print(f"[ENRICHMENT] Completed {len(valid_results)}/{len(selected_queries)} queries successfully")
        
        if not valid_results:
            raise ValueError("All YouTube API queries failed or returned no videos. Cannot enrich persona.")
    finally:
        await youtube_api.close()
    
    print(f"[ENRICHMENT] Synthesizing insights with Claude...")
    synthesis = await synthesize_video_insights(valid_results, persona)
    
    completeness_score = min(100, 50 + (len(valid_results) * 5))
    
    # Store real YouTube data with statistics
    youtube_data = {
        "youtubeResearch": [
            {
                "query": r["query"],
                "videosFound": len(r.get("videos", [])),
                "totalResults": r.get("totalResults", 0),
                "videos": [
                    {
                        "videoId": v["videoId"],
                        "title": v["title"],
                        "channel": v["channelTitle"],
                        "url": v["url"],
                        "viewCount": v["statistics"]["viewCount"],
                        "likeCount": v["statistics"]["likeCount"],
                        "publishedAt": v["publishedAt"][:10]
                    }
                    for v in r.get("videos", [])[:10]
                ]
            }
            for r in valid_results
        ],
        "videoInsights": synthesis.get("key_insights", []),
        "campaignReferences": synthesis.get("campaigns", []),
        "inspirationVideos": synthesis.get("top_videos", []),
        "researchCompleteness": completeness_score
    }
    
    print(f"[ENRICHMENT] Updating persona in storage with REAL video data...")
    updated_persona = await storage.enrich_persona_youtube(persona_id, youtube_data)
    
    total_videos = sum(len(r.get("videos", [])) for r in valid_results)
    
    return PersonaEnrichmentResult(
        personaId=persona_id,
        videosFound=total_videos,
        insightsExtracted=len(synthesis.get("key_insights", [])),
        campaignsIdentified=len(synthesis.get("campaigns", [])),
        completenessScore=completeness_score
    )


async def enrich_persona_with_deep_modules(
    persona_id: str,
    level: Literal["quick", "strategic", "complete"],
    storage,
    existing_modules: Optional[Dict[str, Any]] = None
) -> UserPersona:
    """
    COMPREHENSIVE PERSONA ENRICHMENT - YouTube + 8-Module Deep Analysis
    
    This function combines:
    1. Real YouTube research (videos, statistics, insights)
    2. Deep persona modules (psychographic, buyer journey, behavioral, etc.)
    3. Multi-LLM optimization (Haiku for simple, Sonnet for complex)
    
    Args:
        persona_id: ID of persona to enrich
        level: "quick" (3 modules, ~30s) | "strategic" (6 modules, ~2min) | "complete" (8 modules + copy, ~5min)
        storage: Storage instance
        existing_modules: Optional existing modules for upgrade flow
        
    Returns:
        UserPersona: Fully enriched persona with all modules
    """
    print(f"[DEEP ENRICHMENT] Starting {level.upper()} persona generation...")
    
    # Step 1: Get persona
    persona = await storage.get_user_persona_by_id(persona_id)
    if not persona:
        raise ValueError(f"Persona with id '{persona_id}' not found")
    
    # Step 2: Execute YouTube research (reuse existing function)
    print(f"[DEEP ENRICHMENT] Phase 1: YouTube Research...")
    mode_mapping = {"quick": "quick", "strategic": "strategic", "complete": "complete"}
    await enrich_persona_with_youtube(persona_id, mode_mapping[level], storage)
    
    # Refresh persona to get YouTube data
    persona = await storage.get_user_persona_by_id(persona_id)
    
    # Step 3: Prepare context for PersonaOrchestrator
    persona_context = {
        "companyName": persona.companyName,
        "industry": persona.industry,
        "companySize": persona.companySize,
        "targetAudience": persona.targetAudience,
        "mainProducts": persona.mainProducts,
        "channels": persona.channels or [],
        "primaryGoal": persona.primaryGoal,
        "mainChallenge": persona.mainChallenge,
        "timeline": persona.timeline
    }
    
    # Extract YouTube videos for context
    youtube_videos = []
    if persona.youtubeResearch:
        for research in persona.youtubeResearch:
            for video in research.get("videos", []):
                youtube_videos.append({
                    "videoId": video.get("videoId"),
                    "title": video.get("title"),
                    "channel": video.get("channel"),
                    "viewCount": video.get("viewCount"),
                    "likeCount": video.get("likeCount"),
                    "publishedAt": video.get("publishedAt"),
                    "url": video.get("url")
                })
    
    # Step 4: Generate deep persona modules using PersonaOrchestrator
    print(f"[DEEP ENRICHMENT] Phase 2: Generating {level.upper()} modules with 18 experts...")
    orchestrator = PersonaOrchestrator()
    
    if level == "quick":
        modules = await orchestrator.generate_quick_persona(
            persona_context,
            youtube_data=youtube_videos[:10] if youtube_videos else [],
            reddit_data={}  # TODO: Add Perplexity Reddit research
        )
    elif level == "strategic":
        modules = await orchestrator.generate_strategic_persona(
            persona_context,
            youtube_data=youtube_videos[:15] if youtube_videos else [],
            reddit_data={},
            existing_modules=existing_modules or {}
        )
    else:  # complete
        modules = await orchestrator.generate_complete_persona(
            persona_context,
            youtube_data=youtube_videos[:20] if youtube_videos else [],
            reddit_data={},
            existing_modules=existing_modules or {}
        )
    
    # Step 5: Save modules to database
    print(f"[DEEP ENRICHMENT] Phase 3: Saving {level.upper()} modules to database...")
    update_data = {
        "psychographicCore": modules.get("psychographicCore"),
        "buyerJourney": modules.get("buyerJourney"),
        "behavioralProfile": modules.get("behavioralProfile"),
        "languageCommunication": modules.get("languageCommunication"),
        "strategicInsights": modules.get("strategicInsights"),
        "jobsToBeDone": modules.get("jobsToBeDone"),
        "decisionProfile": modules.get("decisionProfile"),
        "copyExamples": modules.get("copyExamples"),
        "enrichmentLevel": modules.get("enrichmentLevel"),
        "enrichmentStatus": "completed",  # Mark as completed
        "researchCompleteness": modules.get("researchCompleteness"),
        "lastEnrichedAt": datetime.utcnow()  # Update enrichment timestamp
    }
    
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    # Update persona in storage
    updated_persona = await storage.update_user_persona(persona_id, update_data)
    
    print(f"[DEEP ENRICHMENT] ✅ {level.upper()} enrichment complete! Status: completed, Completeness: {modules.get('researchCompleteness')}%")
    
    return updated_persona
