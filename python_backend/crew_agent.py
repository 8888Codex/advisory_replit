"""
CrewAI Integration for Marketing Legends Cognitive Clones
Uses CloneRegistry for rich cognitive clones with Framework EXTRACT
"""
import os
from typing import List, Optional
from anthropic import AsyncAnthropic

# Import clones - works whether imported as module or package
try:
    # Try relative import first (when imported as package)
    from .clones import clone_registry, ExpertCloneBase
except ImportError:
    # Fall back to absolute import (when imported as module)
    from clones import clone_registry, ExpertCloneBase

class MarketingLegendAgent:
    """
    Wrapper for CrewAI Agent representing a marketing legend
    Uses Async Anthropic Claude to avoid blocking the event loop
    Now supports rich cognitive clones from CloneRegistry
    """
    
    def __init__(self, name: str, system_prompt: str, clone: Optional[ExpertCloneBase] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.clone = clone  # Rich clone instance with story banks, triggers, callbacks
        # Use AsyncAnthropic to avoid blocking FastAPI's event loop
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def chat(self, conversation_history: List[dict], user_message: str) -> str:
        """
        Process a chat message using the legend's cognitive clone
        
        Args:
            conversation_history: List of {role: str, content: str} messages
            user_message: New user message to process
        
        Returns:
            str: Assistant response from the cognitive clone
        """
        # Build full message history for Claude
        messages = []
        
        # Add conversation history (excluding the current user message)
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add new user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude with the legend's system prompt (async to avoid blocking event loop)
        response = await self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_prompt,
            messages=messages
        )
        
        # Extract text from response - handle different content block types
        for block in response.content:
            if block.type == "text":
                return block.text  # type: ignore
        
        # Fallback to string representation if no text attribute found
        return str(response.content[0]) if response.content else ""

class LegendAgentFactory:
    """Factory to create agents for different marketing legends"""
    
    @staticmethod
    def create_agent(expert_name: str, system_prompt: Optional[str] = None) -> MarketingLegendAgent:
        """
        Create a cognitive clone agent for a marketing legend.
        
        Priority:
        1. Try to load from CloneRegistry (rich clone with Framework EXTRACT)
        2. Fallback to provided system_prompt (legacy support)
        """
        # Try to get rich clone from registry
        clone = clone_registry.get_clone(expert_name)
        
        if clone:
            # Use rich clone's dynamic system prompt
            system_prompt = clone.get_system_prompt()
            print(f"[LegendAgentFactory] Loaded rich clone for {expert_name} ({len(clone.story_banks)} story banks)")
            return MarketingLegendAgent(
                name=expert_name,
                system_prompt=system_prompt,
                clone=clone
            )
        else:
            # Fallback to legacy prompt (if provided)
            if not system_prompt:
                raise ValueError(f"No clone found for {expert_name} and no fallback prompt provided")
            
            print(f"[LegendAgentFactory] Using legacy prompt for {expert_name} (no clone in registry)")
            return MarketingLegendAgent(
                name=expert_name,
                system_prompt=system_prompt,
                clone=None
            )
