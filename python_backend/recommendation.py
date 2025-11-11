"""
Expert Recommendation System
Matches user business profile with marketing experts based on expertise, goals, and challenges
"""

from typing import List, Dict, Optional
from models import Expert, BusinessProfile

class ExpertRecommendationEngine:
    """
    Recommendation engine that scores experts based on business profile match
    Uses keyword matching, goal alignment, and industry expertise
    """
    
    # Expert expertise mappings (keywords that indicate relevance - PT-BR)
    EXPERT_EXPERTISE_MAP = {
        "Philip Kotler": {
            "keywords": ["estratégia", "segmentação", "posicionamento", "4ps", "marketing corporativo", 
                        "mercado", "análise", "planejamento", "branding", "internacional"],
            "goals": ["crescimento", "growth", "posicionamento", "positioning", "lançamento", "launch"],
            "industries": ["b2b", "corporativo", "tecnologia", "serviços", "services", "tech"],
            "challenges": ["estratégia", "mercado", "competição", "posicionamento", "segmentação"]
        },
        "David Ogilvy": {
            "keywords": ["publicidade", "propaganda", "copywriting", "luxo", "luxury", "branding", "campanha",
                        "criatividade", "mensagem", "direct response"],
            "goals": ["posicionamento", "positioning", "crescimento", "growth", "lançamento", "launch"],
            "industries": ["varejo", "retail", "luxo", "luxury", "consumo", "produto"],
            "challenges": ["awareness", "diferenciação", "mensagem", "criatividade", "campanha"]
        },
        "Claude Hopkins": {
            "keywords": ["científico", "teste", "roi", "métricas", "metrics", "performance", "conversão",
                        "teste a/b", "dados", "data", "mensuração", "resultado"],
            "goals": ["crescimento", "growth", "retenção", "retention"],
            "industries": ["ecommerce", "digital", "performance", "online"],
            "challenges": ["conversão", "roi", "performance", "métricas", "resultado", "custo"]
        },
        "John Wanamaker": {
            "keywords": ["varejo", "retail", "atendimento", "experiência", "customer service",
                        "loja", "confiança", "cliente"],
            "goals": ["retenção", "retention", "crescimento", "growth"],
            "industries": ["varejo", "retail", "ecommerce", "marketplace"],
            "challenges": ["atendimento", "experiência", "fidelização", "fidelidade", "confiança", "retail"]
        },
        "Mary Wells Lawrence": {
            "keywords": ["emocional", "lifestyle", "branding emocional", "storytelling", "inovação",
                        "criatividade", "cultura", "viral"],
            "goals": ["posicionamento", "positioning", "lançamento", "launch"],
            "industries": ["consumo", "moda", "fashion", "lifestyle", "cultura"],
            "challenges": ["diferenciação", "branding", "emocional", "conexão", "cultura"]
        },
        "Seth Godin": {
            "keywords": ["permission marketing", "purple cow", "vaca roxa", "tribes", "tribos", "remarkável", "digital",
                        "storytelling", "nicho", "comunidade", "inovação"],
            "goals": ["posicionamento", "positioning", "crescimento", "growth", "lançamento", "launch"],
            "industries": ["digital", "startup", "tecnologia", "tech", "inovação"],
            "challenges": ["diferenciação", "digital", "comunidade", "engajamento", "inovação"]
        },
        "Gary Vaynerchuk": {
            "keywords": ["social media", "mídias sociais", "digital marketing", "conteúdo", "content", "hustle", "personal branding",
                        "redes sociais", "vídeo", "autenticidade", "execução"],
            "goals": ["crescimento", "growth", "lançamento", "launch"],
            "industries": ["digital", "ecommerce", "startup", "b2c"],
            "challenges": ["digital", "social media", "mídias sociais", "conteúdo", "engajamento", "crescimento rápido"]
        },
        "Leo Burnett": {
            "keywords": ["storytelling", "personagem", "arquétipo", "narrativa", "emocional",
                        "brand character", "publicidade", "campanha"],
            "goals": ["posicionamento", "positioning", "retenção", "retention"],
            "industries": ["consumo", "varejo", "retail", "produto", "branding"],
            "challenges": ["storytelling", "branding", "conexão emocional", "memorabilidade"]
        }
    }
    
    def calculate_expert_score(
        self, 
        expert: Expert, 
        profile: Optional[BusinessProfile] = None
    ) -> Dict:
        """
        Calculate relevance score (0-100) for an expert based on business profile
        
        Returns:
            Dict with score, justification, and breakdown
        """
        if not profile:
            return {
                "score": 50,
                "justification": "Sem perfil de negócio disponível. Todos os especialistas podem ser relevantes.",
                "breakdown": {}
            }
        
        expert_data = self.EXPERT_EXPERTISE_MAP.get(expert.name, {})
        if not expert_data:
            return {
                "score": 50,
                "justification": f"{expert.name} pode oferecer perspectivas valiosas para seu negócio.",
                "breakdown": {}
            }
        
        score = 0
        breakdown = {}
        justifications = []
        
        # 1. Goal alignment (30 points max)
        goal_score = 0
        if profile.primaryGoal.lower() in expert_data.get("goals", []):
            goal_score = 30
            justifications.append(f"Especialista alinhado com seu objetivo de {profile.primaryGoal}")
        elif any(goal in profile.primaryGoal.lower() for goal in expert_data.get("goals", [])):
            goal_score = 20
            justifications.append(f"Parcialmente alinhado com seu objetivo de {profile.primaryGoal}")
        else:
            goal_score = 5
        score += goal_score
        breakdown["goal_alignment"] = goal_score
        
        # 2. Industry match (25 points max)
        industry_score = 0
        profile_industry_lower = profile.industry.lower()
        for industry_keyword in expert_data.get("industries", []):
            if industry_keyword in profile_industry_lower:
                industry_score = 25
                justifications.append(f"Experiência comprovada em {profile.industry}")
                break
        if industry_score == 0:
            industry_score = 5
        score += industry_score
        breakdown["industry_match"] = industry_score
        
        # 3. Challenge match (25 points max)
        challenge_score = 0
        profile_challenge_lower = profile.mainChallenge.lower()
        for challenge_keyword in expert_data.get("challenges", []):
            if challenge_keyword in profile_challenge_lower:
                challenge_score = 25
                justifications.append(f"Especialista em resolver: {profile.mainChallenge}")
                break
        if challenge_score == 0:
            # Check partial match
            for challenge_keyword in expert_data.get("challenges", []):
                if any(word in profile_challenge_lower for word in challenge_keyword.split()):
                    challenge_score = 15
                    justifications.append(f"Pode ajudar com: {profile.mainChallenge}")
                    break
        if challenge_score == 0:
            challenge_score = 5
        score += challenge_score
        breakdown["challenge_match"] = challenge_score
        
        # 4. Keyword match in products/audience (20 points max)
        keyword_score = 0
        # Safe handling of potentially empty fields
        main_products = getattr(profile, 'mainProducts', '') or ''
        target_audience = getattr(profile, 'targetAudience', '') or ''
        context = f"{main_products} {target_audience}".lower()
        
        matched_keywords = [kw for kw in expert_data.get("keywords", []) if kw in context]
        if matched_keywords:
            keyword_score = min(20, len(matched_keywords) * 5)
            if keyword_score >= 15:
                justifications.append(f"Alta relevância para seu mercado e produtos")
        score += keyword_score
        breakdown["keyword_match"] = keyword_score
        
        # Normalize to 0-100 scale
        score = min(100, score)
        
        # Generate justification
        if not justifications:
            justification = f"{expert.name} oferece perspectivas valiosas de {expert.title}."
        else:
            justification = " • ".join(justifications)
        
        return {
            "score": score,
            "justification": justification,
            "breakdown": breakdown
        }
    
    def get_star_rating(self, score: int) -> int:
        """Convert score (0-100) to star rating (1-5)"""
        if score >= 85:
            return 5
        elif score >= 70:
            return 4
        elif score >= 50:
            return 3
        elif score >= 30:
            return 2
        else:
            return 1
    
    def get_recommendations(
        self,
        experts: List[Expert],
        profile: Optional[BusinessProfile] = None,
        top_n: Optional[int] = None
    ) -> List[Dict]:
        """
        Get ranked expert recommendations
        
        Returns:
            List of dicts with expert info, score, stars, and justification
        """
        recommendations = []
        
        for expert in experts:
            result = self.calculate_expert_score(expert, profile)
            recommendations.append({
                "expertId": expert.id,
                "expertName": expert.name,
                "score": result["score"],
                "stars": self.get_star_rating(result["score"]),
                "justification": result["justification"],
                "breakdown": result["breakdown"]
            })
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top N if specified
        if top_n:
            return recommendations[:top_n]
        
        return recommendations


# Singleton instance
recommendation_engine = ExpertRecommendationEngine()
