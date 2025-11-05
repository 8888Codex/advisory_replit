"""
StoryBankTool - Access expert's story banks filtered by user context
Enables experts to share relevant case studies and examples
"""
from typing import Optional, Dict, Any, List
from clones.base import ExpertCloneBase


class StoryBankTool:
    """
    Tool that allows marketing legend agents to access their story banks
    (real cases with metrics) filtered by user's industry, niche, or challenge.
    
    Benefits for "Disney Experience":
    - Makes recommendations concrete with real examples
    - Shares relevant case studies automatically
    - Validates advice with proven track record
    - Engages user with storytelling
    """
    
    def __init__(self):
        self.name = "story_bank"
        self.description = (
            "Accesses expert's story banks - real cases with metrics and outcomes. "
            "Filters stories by user's industry, niche, or challenge for maximum relevance. "
            "Use to make recommendations concrete with proven examples."
        )
    
    def get_relevant_stories(
        self,
        clone: ExpertCloneBase,
        context: Dict[str, Any],
        max_stories: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get relevant story banks from expert's clone based on user context
        
        Args:
            clone: ExpertCloneBase instance with story_banks
            context: Dict with user's industry, niche, challenge keywords
            max_stories: Maximum number of stories to return
        
        Returns:
            List of relevant story bank entries sorted by relevance
        """
        if not clone or not clone.story_banks:
            return []
        
        # Get all stories
        all_stories = list(clone.story_banks.values())
        
        # Extract context keywords for filtering
        keywords = []
        if "industry" in context and context["industry"]:
            keywords.append(context["industry"].lower())
        if "niche" in context and context["niche"]:
            keywords.extend(context["niche"].lower().split())
        if "challenge" in context and context["challenge"]:
            keywords.extend(context["challenge"].lower().split())
        if "goal" in context and context["goal"]:
            keywords.append(context["goal"].lower())
        
        # Score stories by keyword relevance
        scored_stories = []
        for story in all_stories:
            score = 0
            story_text = " ".join([
                story.get("title", ""),
                story.get("challenge", ""),
                story.get("solution", ""),
                story.get("results", "")
            ]).lower()
            
            # Count keyword matches
            for keyword in keywords:
                if keyword in story_text:
                    score += 1
            
            scored_stories.append((score, story))
        
        # Sort by relevance score (descending) and take top N
        scored_stories.sort(key=lambda x: x[0], reverse=True)
        relevant_stories = [story for score, story in scored_stories[:max_stories]]
        
        return [
            {
                "title": story.get("title", "Case Study"),
                "challenge": story.get("challenge", ""),
                "solution": story.get("solution", ""),
                "results": story.get("results", ""),
                "takeaway": story.get("takeaway", "")
            }
            for story in relevant_stories
        ]
    
    def get_prompt_instruction(self) -> str:
        """
        Returns instruction text for including in agent system prompts
        """
        return (
            "\n\n## 📚 FERRAMENTA: Story Bank\n"
            "Você tem acesso às suas story banks - casos reais com métricas e resultados. "
            "Quando suas recomendações se beneficiariam de exemplos concretos, "
            "compartilhe histórias relevantes do seu acervo. Seja específico com métricas: "
            "'Em um caso com empresa similar, implementamos X e obtivemos Y% de aumento em Z.'\n\n"
            "Suas story banks são automaticamente filtradas por contexto do usuário "
            "para maximizar relevância."
        )


# Global instance for easy import
story_bank_tool = StoryBankTool()
