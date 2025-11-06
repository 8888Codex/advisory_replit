"""
Persona Enrichment Orchestrator for YouTube Research Integration

This module orchestrates the enrichment of user personas with YouTube research data,
including campaign references, video insights, and curated content recommendations.
"""

import asyncio
import os
from typing import List, Dict, Any
from anthropic import AsyncAnthropic
from models import UserPersona, PersonaEnrichmentResult
from tools.youtube_research import youtube_tool

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
    Extract key insights from YouTube research results using Claude.
    
    Analyzes YouTube research findings and synthesizes them into structured
    insights, campaign references, and curated video recommendations.
    
    Args:
        results: List of YouTube research results from Perplexity API
        persona: UserPersona object for context
        
    Returns:
        Dict containing:
            - key_insights: List[str] - Top insights across videos
            - campaigns: List[dict] - Structured campaign data (videoId, title, url, channel, insights)
            - top_videos: List[dict] - Top 3-5 curated videos
    """
    anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    combined_findings = "\n\n---\n\n".join([
        f"Query: {r['query']}\n{r['findings']}" 
        for r in results
    ])
    
    synthesis_prompt = f"""Você é um analista de marketing especializado em curadoria de conteúdo de vídeo.

Analise os resultados de pesquisa do YouTube abaixo e extraia insights acionáveis para uma empresa no setor de {persona.industry or 'marketing'}.

Contexto do cliente:
- Público-alvo: {persona.targetAudience or 'geral'}
- Objetivo principal: {persona.primaryGoal or 'crescimento'}
- Desafio principal: {persona.mainChallenge or 'aquisição de clientes'}

Resultados da Pesquisa:
{combined_findings}

Forneça sua análise em formato JSON com a seguinte estrutura:
{{
    "key_insights": [
        "Insight 1 - descrição breve e acionável",
        "Insight 2 - descrição breve e acionável",
        ...
    ],
    "campaigns": [
        {{
            "videoId": "ID do vídeo (extraído da URL)",
            "title": "Título do vídeo",
            "url": "URL completa do YouTube",
            "channel": "Nome do canal",
            "insights": ["Insight 1 específico deste vídeo", "Insight 2..."]
        }}
    ],
    "top_videos": [
        {{
            "videoId": "ID do vídeo",
            "title": "Título",
            "url": "URL",
            "channel": "Canal",
            "relevanceScore": 5,
            "reason": "Por que este vídeo é relevante"
        }}
    ]
}}

IMPORTANTE:
1. Extraia key_insights gerais que se aplicam ao cliente (5-8 insights)
2. Identifique campanhas/cases específicos nos vídeos (até 10 campanhas)
3. Selecione os 3-5 vídeos MAIS relevantes para o cliente
4. Para videoId, extraia da URL (youtube.com/watch?v=XXXX ou youtu.be/XXXX)
5. Atribua relevanceScore de 1-5 (5 = altamente relevante)
6. RETORNE APENAS O JSON, sem texto adicional."""

    response = await anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        temperature=0.2,
        messages=[{
            "role": "user",
            "content": synthesis_prompt
        }]
    )
    
    import json
    from anthropic.types import TextBlock
    
    text_block = next((block for block in response.content if isinstance(block, TextBlock)), None)
    if not text_block:
        raise ValueError("No text response from Claude")
    
    synthesis_text = text_block.text.strip()
    
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
    
    print(f"[ENRICHMENT] Executing {len(selected_queries)} YouTube queries in parallel...")
    
    tasks = [youtube_tool.run(query) for query in selected_queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[ENRICHMENT] Query {i+1} failed: {result}")
        else:
            valid_results.append(result)
    
    print(f"[ENRICHMENT] Completed {len(valid_results)}/{len(selected_queries)} queries successfully")
    
    if not valid_results:
        raise ValueError("All YouTube research queries failed. Cannot enrich persona.")
    
    print(f"[ENRICHMENT] Synthesizing insights with Claude...")
    synthesis = await synthesize_video_insights(valid_results, persona)
    
    completeness_score = min(100, 50 + (len(valid_results) * 5))
    
    youtube_data = {
        "youtubeResearch": [
            {
                "query": r["query"],
                "findings": r["findings"],
                "sources": r.get("sources", []),
                "videoCount": r.get("video_count", 0)
            }
            for r in valid_results
        ],
        "videoInsights": synthesis.get("key_insights", []),
        "campaignReferences": synthesis.get("campaigns", []),
        "inspirationVideos": synthesis.get("top_videos", []),
        "researchCompleteness": completeness_score
    }
    
    print(f"[ENRICHMENT] Updating persona in storage...")
    updated_persona = await storage.enrich_persona_youtube(persona_id, youtube_data)
    
    return PersonaEnrichmentResult(
        personaId=persona_id,
        videosFound=sum(r.get("video_count", 0) for r in valid_results),
        insightsExtracted=len(synthesis.get("key_insights", [])),
        campaignsIdentified=len(synthesis.get("campaigns", [])),
        completenessScore=completeness_score
    )
