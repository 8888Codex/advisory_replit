"""
CrewAI Integration for Marketing Legends Cognitive Clones
Uses CloneRegistry for rich cognitive clones with Framework EXTRACT
"""
import os
from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic

# Import clones - works whether imported as module or package
try:
    # Try relative import first (when imported as package)
    from .clones import clone_registry, ExpertCloneBase
    from .tools.perplexity_tool import PerplexityResearchTool
    from .tools.user_memory_tool import UserMemoryTool
    from .tools.story_bank_tool import StoryBankTool
except ImportError:
    # Fall back to absolute import (when imported as module)
    from clones import clone_registry, ExpertCloneBase
    from tools.perplexity_tool import PerplexityResearchTool
    from tools.user_memory_tool import UserMemoryTool
    from tools.story_bank_tool import StoryBankTool

class MarketingLegendAgent:
    """
    Wrapper for CrewAI Agent representing a marketing legend
    Uses Async Anthropic Claude to avoid blocking the event loop
    Now supports rich cognitive clones from CloneRegistry
    """
    
    def __init__(
        self, 
        name: str, 
        system_prompt: str, 
        clone: Optional[ExpertCloneBase] = None,
        tools: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.clone = clone  # Rich clone instance with story banks, triggers, callbacks
        self.tools = tools or {}  # Custom tools (PerplexityTool, UserMemoryTool, StoryBankTool)
        # Use AsyncAnthropic to avoid blocking FastAPI's event loop
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def chat(
        self, 
        conversation_history: List[dict], 
        user_message: str,
        user_id: str = "demo_user"
    ) -> str:
        """
        Process a chat message using the legend's cognitive clone with tool support
        
        Args:
            conversation_history: List of {role: str, content: str} messages
            user_message: New user message to process
            user_id: User identifier for personalization tools
        
        Returns:
            str: Assistant response from the cognitive clone
        """
        # Build enriched system prompt with tool instructions
        enhanced_system = self._build_enhanced_system_prompt(user_id)
        
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
        
        # Call Claude with the legend's enhanced system prompt (async to avoid blocking event loop)
        response = await self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=enhanced_system,
            messages=messages
        )
        
        # Extract text from response - handle different content block types
        for block in response.content:
            if block.type == "text":
                return block.text  # type: ignore
        
        # Fallback to string representation if no text attribute found
        return str(response.content[0]) if response.content else ""
    
    def _build_enhanced_system_prompt(self, user_id: str) -> str:
        """
        Build system prompt enriched with tool instructions
        
        Args:
            user_id: User identifier
        
        Returns:
            Enhanced system prompt with tool capabilities
        """
        enhanced = self.system_prompt
        
        # Add tool instructions if tools are available
        if self.tools:
            enhanced += "\n\n## AVAILABLE TOOLS\n"
            enhanced += "You have access to the following capabilities:\n\n"
            
            for tool_name, tool in self.tools.items():
                if hasattr(tool, 'get_prompt_instruction'):
                    enhanced += f"### {tool_name}\n"
                    enhanced += tool.get_prompt_instruction() + "\n\n"
        
        return enhanced

class LegendAgentFactory:
    """Factory to create agents for different marketing legends"""
    
    @staticmethod
    def create_agent(
        expert_name: str, 
        system_prompt: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None,
        persona_context: Optional[str] = None  # NEW: Persona context to inject
    ) -> MarketingLegendAgent:
        """
        Create a cognitive clone agent for a marketing legend with custom tools.
        
        Priority:
        1. Load clone from CloneRegistry (if exists)
        2. Use clone's rich prompt
        3. ADD persona_context to clone's prompt (if provided)
        4. Fallback to system_prompt if no clone exists
        
        Args:
            expert_name: Name of the marketing legend
            system_prompt: Fallback system prompt if no clone found
            tools: Optional dict of custom tools
            persona_context: Optional persona context to APPEND to any prompt
        """
        # Try to get rich clone from registry
        clone = clone_registry.get_clone(expert_name)
        
        if clone:
            # Use clone's rich prompt (with stories, frameworks, etc.)
            base_prompt = clone.get_system_prompt()
            
            # ADD persona context if provided
            if persona_context:
                final_prompt = base_prompt + persona_context
                print(f"[LegendAgentFactory] Loaded rich clone for {expert_name} + PERSONA CONTEXT ({len(persona_context)} chars)")
            else:
                final_prompt = base_prompt
                print(f"[LegendAgentFactory] Loaded rich clone for {expert_name} ({len(clone.story_banks)} story banks)")
            
            return MarketingLegendAgent(
                name=expert_name,
                system_prompt=final_prompt,  # Clone prompt + persona context!
                clone=clone,
                tools=tools
            )
        else:
            # Fallback to legacy prompt (if provided)
            if not system_prompt:
                raise ValueError(f"No clone found for {expert_name} and no fallback prompt provided")
            
            # ADD persona context to legacy prompt too
            if persona_context:
                final_prompt = system_prompt + persona_context
                print(f"[LegendAgentFactory] Using legacy prompt for {expert_name} + PERSONA CONTEXT")
            else:
                final_prompt = system_prompt
                print(f"[LegendAgentFactory] Using legacy prompt for {expert_name} (no clone in registry)")
            
            return MarketingLegendAgent(
                name=expert_name,
                system_prompt=final_prompt,  # Legacy prompt + persona context!
                clone=None,
                tools=tools
            )
