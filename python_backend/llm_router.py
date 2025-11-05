"""
LLM Router - Selects optimal LLM for each task to minimize costs
Routes simple tasks to Claude Haiku (~12x cheaper) and complex tasks to Claude Sonnet
"""
import os
import json
from enum import Enum
from typing import Optional, Dict, Any
from anthropic import AsyncAnthropic


class LLMTask(Enum):
    """Types of LLM tasks with different complexity requirements"""
    RECOMMEND_EXPERTS = "recommend_experts"  # Simple: analyze expertise vs problem
    SUGGEST_QUESTIONS = "suggest_questions"  # Simple: generate contextual questions
    CHAT_EXPERT = "chat_expert"              # Complex: 1:1 conversation with Framework EXTRACT
    COUNCIL_DIALOGUE = "council_dialogue"    # Complex: multi-expert roundtable discussion
    AUTO_CLONE = "auto_clone"                # Complex: create cognitive clone with research
    SYNTHESIS = "synthesis"                  # Medium: synthesize multiple expert contributions


class LLMTier(Enum):
    """Available LLM tiers ordered by cost (cheapest to most expensive)"""
    FAST = "claude-3-5-haiku-20241022"     # Claude Haiku 3.5 - ~$0.25 per 1M input tokens
    STANDARD = "claude-sonnet-4-20250514"  # Claude Sonnet 4 - ~$3 per 1M input tokens
    # PREMIUM = "claude-opus-4-20250514"   # Claude Opus 4 - ~$15 per 1M tokens (future use)


# Task to LLM tier mapping
TASK_ROUTING: Dict[LLMTask, LLMTier] = {
    LLMTask.RECOMMEND_EXPERTS: LLMTier.FAST,      # Simple matching task
    LLMTask.SUGGEST_QUESTIONS: LLMTier.FAST,      # Simple question generation
    LLMTask.CHAT_EXPERT: LLMTier.STANDARD,        # Needs Framework EXTRACT fidelity
    LLMTask.COUNCIL_DIALOGUE: LLMTier.STANDARD,   # Complex multi-expert dialogue
    LLMTask.AUTO_CLONE: LLMTier.STANDARD,         # Complex cognitive cloning
    LLMTask.SYNTHESIS: LLMTier.STANDARD,          # Important consensus synthesis
}


class LLMRouter:
    """Routes LLM requests to the optimal model based on task complexity"""
    
    def __init__(self):
        # Initialize Claude client (used for both Haiku and Sonnet)
        self.claude_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def get_tier_for_task(self, task: LLMTask) -> LLMTier:
        """Get the optimal LLM tier for a given task"""
        return TASK_ROUTING.get(task, LLMTier.STANDARD)
    
    async def generate_text(
        self,
        task: LLMTask,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> str:
        """
        Generate text using the optimal LLM for the task
        
        Args:
            task: Type of LLM task (determines which model to use)
            prompt: Text prompt for the model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text response
        """
        tier = self.get_tier_for_task(task)
        model_name = tier.value
        
        # Log which model is being used
        model_label = "Claude Haiku" if tier == LLMTier.FAST else "Claude Sonnet"
        cost_label = "(cost-optimized ~92% cheaper)" if tier == LLMTier.FAST else "(high-quality)"
        print(f"[LLM Router] Using {model_label} for {task.value} {cost_label}")
        
        try:
            response = await self.claude_client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract text from response
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text
            
            return response_text
            
        except Exception as e:
            error_msg = str(e)
            print(f"[LLM Router] Error with {model_name}: {error_msg}")
            raise e
    
    def get_cost_estimate(self, task: LLMTask, tokens: int = 1000) -> float:
        """
        Estimate cost for a task (in USD per 1M tokens for comparison)
        
        Args:
            task: Type of LLM task
            tokens: Estimated number of tokens
            
        Returns:
            Estimated cost multiplier (relative to Claude Sonnet baseline)
        """
        tier = self.get_tier_for_task(task)
        
        # Cost multipliers relative to Claude Sonnet (1.0x baseline)
        # Haiku: $0.25 input / $1.25 output per 1M tokens
        # Sonnet: $3 input / $15 output per 1M tokens
        cost_multipliers = {
            LLMTier.FAST: 0.083,       # Haiku is ~12x cheaper than Sonnet
            LLMTier.STANDARD: 1.0,     # Sonnet baseline
        }
        
        return cost_multipliers.get(tier, 1.0)


# Singleton instance
llm_router = LLMRouter()
