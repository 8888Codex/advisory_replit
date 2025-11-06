"""
Analytics Engine - Calculate metrics and insights from user activity
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncpg
import os


class AnalyticsEngine:
    """Calculates analytics metrics and generates AI-powered recommendations"""
    
    def __init__(self, storage: Any):
        self.storage = storage
        self.database_url = os.environ.get("DATABASE_URL")
    
    async def _get_db_conn(self):
        """Get PostgreSQL connection for analytics queries"""
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        return await asyncpg.connect(self.database_url)
    
    async def get_overview_stats(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get high-level overview metrics.
        Returns: {
            totalConversations: int,
            totalExperts: int,
            totalCouncils: int,
            currentStreak: int,
            lastActive: str (ISO date)
        }
        """
        conn = await self._get_db_conn()
        
        try:
            # Total chat conversations from user_activity (FILTERED BY USER)
            total_convos = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT metadata->>'conversation_id') 
                FROM user_activity 
                WHERE user_id = $1
                AND activity_type = 'chat_message'
                AND metadata->>'conversation_id' IS NOT NULL
                """,
                user_id
            )
            
            # Unique experts consulted from user_activity metadata (FILTERED BY USER)
            total_experts = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT metadata->>'expertId') 
                FROM user_activity 
                WHERE user_id = $1
                AND metadata->>'expertId' IS NOT NULL
                """,
                user_id
            )
            
            # Total council sessions (FILTERED BY USER)
            total_councils = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT metadata->>'council_id') 
                FROM user_activity 
                WHERE user_id = $1
                AND activity_type = 'council_created'
                AND metadata->>'council_id' IS NOT NULL
                """,
                user_id
            )
            
            # Last active date from user_activity (FILTERED BY USER)
            last_active = await conn.fetchval(
                "SELECT MAX(created_at) FROM user_activity WHERE user_id = $1",
                user_id
            )
            
            # Calculate streak (consecutive days of activity) for this user
            current_streak = await self._calculate_streak(conn, user_id)
            
            return {
                "totalConversations": total_convos or 0,
                "totalExperts": total_experts or 0,
                "totalCouncils": total_councils or 0,
                "currentStreak": current_streak,
                "lastActive": last_active.isoformat() if last_active else None
            }
        finally:
            await conn.close()
    
    async def _calculate_streak(self, conn: asyncpg.Connection, user_id: str) -> int:
        """Calculate consecutive days of activity from user_activity for specific user"""
        # Get all unique activity dates for this user, sorted descending
        rows = await conn.fetch("""
            SELECT DISTINCT DATE(created_at) as activity_date
            FROM user_activity
            WHERE user_id = $1
            ORDER BY activity_date DESC
        """, user_id)
        
        if not rows:
            return 0
        
        dates = [row['activity_date'] for row in rows]
        today = datetime.now().date()
        
        # Check if most recent activity is today or yesterday
        most_recent = dates[0]
        if most_recent < today - timedelta(days=1):
            return 0  # Streak broken
        
        # Count consecutive days
        streak = 1
        for i in range(1, len(dates)):
            expected_date = dates[i-1] - timedelta(days=1)
            if dates[i] == expected_date:
                streak += 1
            else:
                break
        
        return streak
    
    async def get_activity_timeline(self, user_id: str = "default", days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily activity breakdown for last N days FOR SPECIFIC USER.
        Returns: [
            {date: "2025-11-06", chats: 5, councils: 1, total: 6},
            ...
        ]
        """
        conn = await self._get_db_conn()
        
        try:
            # Query user_activity directly with user filter
            rows = await conn.fetch(f"""
                SELECT 
                    DATE(created_at)::text as date,
                    COUNT(*) FILTER (WHERE activity_type = 'chat_message') as chats,
                    COUNT(*) FILTER (WHERE activity_type IN ('council_message', 'council_created')) as councils,
                    COUNT(*) as total
                FROM user_activity
                WHERE user_id = $1
                AND created_at >= CURRENT_DATE - INTERVAL '{days} days'
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) ASC
            """, user_id)
            
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_top_experts(self, user_id: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get ranking of most consulted experts FOR SPECIFIC USER.
        Returns: [
            {
                expertId: str,
                expertName: str,
                category: str,
                consultations: int,
                lastConsulted: str (ISO),
                avatar: str (URL)
            },
            ...
        ]
        """
        from storage import storage  # Import storage to get expert details
        
        conn = await self._get_db_conn()
        
        try:
            # Get aggregated data from user_activity (no JOIN needed)
            rows = await conn.fetch(f"""
                SELECT 
                    ua.metadata->>'expertId' as "expertId",
                    ua.metadata->>'expertName' as "expertName",
                    COUNT(*) as consultations,
                    MAX(ua.created_at) as "lastConsulted"
                FROM user_activity ua
                WHERE ua.user_id = $1
                AND ua.metadata->>'expertId' IS NOT NULL
                GROUP BY ua.metadata->>'expertId', ua.metadata->>'expertName'
                ORDER BY consultations DESC
                LIMIT {limit}
            """, user_id)
            
            # Get all experts from storage ONCE (build name -> expert mapping)
            all_experts = await storage.get_experts()
            expert_by_name = {expert.name: expert for expert in all_experts}
            
            # Enrich with expert details using NAME match (UUIDs change on reload!)
            result = []
            for row in rows:
                item = dict(row)
                expert_name = item['expertName']
                
                # Match by name since IDs change on Python backend reload
                expert = expert_by_name.get(expert_name)
                if expert:
                    item['category'] = expert.category
                    item['avatar'] = expert.avatar
                else:
                    item['category'] = "Outros"
                    item['avatar'] = "/default-avatar.png"
                
                if item['lastConsulted']:
                    item['lastConsulted'] = item['lastConsulted'].isoformat()
                result.append(item)
            
            return result
        finally:
            await conn.close()
    
    async def get_category_distribution(self, user_id: str = "default") -> Dict[str, int]:
        """
        Get consultation count by category FOR SPECIFIC USER.
        Returns: {
            "Branding": 25,
            "Growth": 18,
            ...
        }
        """
        from storage import storage  # Import storage to get expert categories
        
        conn = await self._get_db_conn()
        
        try:
            # Get expert usage counts from user_activity (include expert names)
            rows = await conn.fetch("""
                SELECT 
                    ua.metadata->>'expertName' as expert_name,
                    COUNT(*) as consultation_count
                FROM user_activity ua
                WHERE ua.user_id = $1
                AND ua.metadata->>'expertName' IS NOT NULL
                GROUP BY ua.metadata->>'expertName'
            """, user_id)
            
            # Get all experts from storage ONCE (build name -> expert mapping)
            all_experts = await storage.get_experts()
            expert_by_name = {expert.name: expert for expert in all_experts}
            
            # Map expert_name -> category using in-memory storage, then aggregate
            category_counts: Dict[str, int] = {}
            for row in rows:
                expert_name = row['expert_name']
                count = row['consultation_count']
                
                # Get expert from storage by NAME (IDs change on reload)
                expert = expert_by_name.get(expert_name)
                if expert:
                    category = expert.category
                    category_counts[category] = category_counts.get(category, 0) + count
            
            return category_counts
        finally:
            await conn.close()
    
    async def get_highlights(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get user's saved favorites and top-rated insights.
        Returns: {
            favoriteMessages: [...],
            topCouncilInsights: [...],
            referencedCampaigns: [...]
        }
        """
        conn = await self._get_db_conn()
        
        try:
            # Get user favorites
            favorites = await conn.fetch("""
                SELECT 
                    item_type as "itemType",
                    item_id as "itemId",
                    notes,
                    metadata,
                    created_at as "createdAt"
                FROM user_favorites
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 10
            """, user_id)
            
            # Get most recent council consensuses FOR THIS USER
            councils = await conn.fetch("""
                SELECT 
                    id,
                    problem,
                    consensus,
                    created_at as "createdAt"
                FROM council_sessions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 5
            """, user_id)
            
            return {
                "favoriteMessages": [dict(f) for f in favorites],
                "topCouncilInsights": [dict(c) for c in councils],
                "referencedCampaigns": []  # TODO: Extract from persona if enriched
            }
        finally:
            await conn.close()
    
    async def generate_recommendations(self, user_id: str = "default") -> List[Dict[str, str]]:
        """
        Use AI to analyze patterns and generate actionable recommendations.
        Returns: [
            {
                type: "expert_suggestion" | "pattern_insight" | "next_step",
                title: str,
                description: str,
                action: str (optional CTA)
            },
            ...
        ]
        """
        from llm_router import LLMRouter, LLMTask
        
        # Gather context about user's activity (PASS USER_ID TO ALL CALLS)
        overview = await self.get_overview_stats(user_id)
        top_experts = await self.get_top_experts(user_id=user_id, limit=5)
        categories = await self.get_category_distribution(user_id=user_id)
        
        # Build prompt for Claude Haiku (cost-optimized)
        context = f"""Analyze this user's O Conselho usage and generate 3-5 actionable recommendations:

ACTIVITY OVERVIEW:
- Total conversations: {overview['totalConversations']}
- Experts consulted: {overview['totalExperts']}
- Council sessions: {overview['totalCouncils']}
- Current streak: {overview['currentStreak']} days

TOP CONSULTED EXPERTS:
{chr(10).join([f"- {e['expertName']} ({e['category']}): {e['consultations']} consultas" for e in top_experts[:3]])}

CATEGORY DISTRIBUTION:
{chr(10).join([f"- {cat}: {count} consultas" for cat, count in list(categories.items())[:5]])}

Generate 3-5 recommendations in Brazilian Portuguese as a JSON array. Each item should have:
- type: "expert_suggestion", "pattern_insight", or "next_step"
- title: Short title (max 60 chars)
- description: Brief explanation (max 150 chars)
- action: Optional CTA text

Focus on: suggesting underutilized experts, identifying patterns, recommending next steps.
"""
        
        router = LLMRouter()
        
        try:
            # Use FAST tier (Claude Haiku) for cost optimization
            response_text = await router.generate_text(
                task=LLMTask.RECOMMEND_EXPERTS,  # FAST tier
                prompt=context,
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse JSON from response
            import json
            import re
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
            
            recommendations = json.loads(json_str)
            
            # Validate structure
            if not isinstance(recommendations, list):
                recommendations = []
            
            return recommendations[:5]  # Max 5 recommendations
            
        except Exception as e:
            print(f"[Analytics] Error generating recommendations: {e}")
            # Return fallback recommendations
            return [
                {
                    "type": "pattern_insight",
                    "title": "Continue sua jornada de aprendizado",
                    "description": f"Você já consultou {overview['totalExperts']} especialistas. Explore novas categorias!",
                    "action": "Ver Categorias"
                }
            ]
