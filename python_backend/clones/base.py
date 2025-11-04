"""
Base class for all Expert Cognitive Clones.
Framework EXTRACT - 20-point cognitive cloning methodology.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class ExpertCloneBase(ABC):
    """
    Abstract base class for all expert cognitive clones.
    
    Every clone MUST implement:
    - get_system_prompt(): Generate rich system prompt with Framework EXTRACT
    - Identity attributes (name, title, expertise, bio)
    - Story banks (real cases with metrics)
    - Triggers (behavioral activation patterns)
    - Iconic callbacks (signature phrases)
    """

    def __init__(self) -> None:
        # Core Identity
        self.name: str = ""
        self.title: str = ""
        self.expertise: List[str] = []
        self.bio: str = ""
        
        # Temporal Context
        self.active_years: str = ""
        self.historical_context: str = ""
        
        # Story Banks - Real cases with metrics
        self.story_banks: Dict[str, Dict[str, Any]] = {}
        
        # Iconic Callbacks - Signature phrases
        self.iconic_callbacks: List[str] = []
        
        # Triggers - Behavioral patterns
        self.positive_triggers: List[str] = []
        self.negative_triggers: List[str] = []
        self.trigger_reactions: Dict[str, str] = {}
        
        # Metadata
        self.created_at: datetime = datetime.now()
        self.version: str = "1.0"
        
        # Auto-populate story banks from method (if implemented)
        if hasattr(self, 'get_story_banks') and callable(getattr(self, 'get_story_banks')):
            stories = self.get_story_banks()
            self.story_banks = {f"story_{i+1}": story for i, story in enumerate(stories)}
        
        # Auto-populate iconic callbacks from method (if implemented)
        if hasattr(self, 'get_iconic_callbacks') and callable(getattr(self, 'get_iconic_callbacks')):
            self.iconic_callbacks = self.get_iconic_callbacks()
        
        # Auto-populate triggers from method (if implemented)
        if hasattr(self, 'get_trigger_keywords') and callable(getattr(self, 'get_trigger_keywords')):
            triggers = self.get_trigger_keywords()
            self.positive_triggers = triggers.get('positive_triggers', [])
            self.negative_triggers = triggers.get('negative_triggers', [])
        
        # Auto-populate trigger reactions from method (if implemented)
        if hasattr(self, 'get_trigger_reactions') and callable(getattr(self, 'get_trigger_reactions')):
            reactions = self.get_trigger_reactions()
            self.trigger_reactions = {r['trigger']: r['reaction'] for r in reactions}

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Generate complete system prompt using Framework EXTRACT.
        
        MUST include:
        - Identity Core (name, title, bio, expertise)
        - Temporal Context (active years, historical context)
        - Story Banks (real cases with before/after/metrics)
        - Iconic Callbacks (signature phrases)
        - Triggers (behavioral activation)
        
        Returns:
            str: Complete system prompt ready for Claude API
        """
        pass

    def get_story_by_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        Find story bank entry by keyword match.
        
        Args:
            keyword: Search term (e.g., "purple cow", "tribes", "4Ps")
            
        Returns:
            Story dict with company, year, context, before, after, growth, lesson
        """
        keyword_lower = keyword.lower()
        
        for story_id, story_data in self.story_banks.items():
            if "keywords" in story_data:
                keywords = story_data["keywords"].lower()
                if keyword_lower in keywords:
                    return story_data
        
        return None

    def get_trigger_reaction(self, user_input: str) -> Optional[str]:
        """
        Check if user input contains trigger words and return specific reaction.
        
        Args:
            user_input: User's message
            
        Returns:
            Specific reaction string if trigger found, None otherwise
        """
        user_input_lower = user_input.lower()
        
        # Check negative triggers first (stronger reactions)
        for trigger in self.negative_triggers:
            if trigger.lower() in user_input_lower:
                if trigger in self.trigger_reactions:
                    return self.trigger_reactions[trigger]
        
        # Check positive triggers
        for trigger in self.positive_triggers:
            if trigger.lower() in user_input_lower:
                if trigger in self.trigger_reactions:
                    return self.trigger_reactions[trigger]
        
        return None

    def get_random_callback(self) -> str:
        """
        Get random iconic callback phrase.
        
        Returns:
            Random signature phrase from iconic_callbacks
        """
        import random
        if self.iconic_callbacks:
            return random.choice(self.iconic_callbacks)
        return ""

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get clone metadata for inspection/debugging.
        
        Returns:
            Dict with name, expertise, story_count, trigger_count, etc.
        """
        return {
            "name": self.name,
            "title": self.title,
            "expertise": self.expertise,
            "active_years": self.active_years,
            "story_banks_count": len(self.story_banks),
            "iconic_callbacks_count": len(self.iconic_callbacks),
            "positive_triggers_count": len(self.positive_triggers),
            "negative_triggers_count": len(self.negative_triggers),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate that clone has minimum required components.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.name:
            errors.append("Missing required field: name")
        
        if not self.title:
            errors.append("Missing required field: title")
        
        if not self.expertise:
            errors.append("Missing required field: expertise (must have at least 1)")
        
        if len(self.story_banks) < 5:
            errors.append(f"Insufficient story banks: {len(self.story_banks)} (minimum 5 required)")
        
        if len(self.iconic_callbacks) < 7:
            errors.append(f"Insufficient iconic callbacks: {len(self.iconic_callbacks)} (minimum 7 required)")
        
        if len(self.positive_triggers) < 15:
            errors.append(f"Insufficient positive triggers: {len(self.positive_triggers)} (minimum 15 required)")
        
        if len(self.negative_triggers) < 15:
            errors.append(f"Insufficient negative triggers: {len(self.negative_triggers)} (minimum 15 required)")
        
        return (len(errors) == 0, errors)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name} ({len(self.story_banks)} stories)>"
