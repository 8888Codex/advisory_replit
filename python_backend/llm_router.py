"""
LLM Router - Selects optimal LLM for each task to minimize costs
Routes simple tasks to Gemini Flash (~20x cheaper) and complex tasks to Claude Sonnet
"""
import os
import json
from enum import Enum
from typing import Optional, Dict, Any
import httpx
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
    FAST = "gemini-2.5-flash"       # Google Gemini Flash - ~$0.075 per 1M tokens
    STANDARD = "claude-sonnet-4-20250514"  # Claude Sonnet-4 - ~$3 per 1M tokens
    # PREMIUM = "claude-opus-4-20250514"   # Claude Opus-4 - ~$15 per 1M tokens (future use)


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
        # Gemini via Replit AI Integrations (HTTP client)
        self.gemini_base_url = os.getenv("AI_INTEGRATIONS_GEMINI_BASE_URL")
        self.gemini_api_key = os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY")
        
        # Initialize Claude client
        self.claude_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def get_tier_for_task(self, task: LLMTask) -> LLMTier:
        """Get the optimal LLM tier for a given task"""
        return TASK_ROUTING.get(task, LLMTier.STANDARD)
    
    async def _call_gemini_api(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> str:
        """Call Gemini API via Replit AI Integrations"""
        async with httpx.AsyncClient() as client:
            # Gemini API request format (Replit AI Integrations compatible)
            request_body = {
                "model": "gemini-2.5-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            headers = {
                "Authorization": f"Bearer {self.gemini_api_key}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{self.gemini_base_url}/v1/chat/completions",
                json=request_body,
                headers=headers,
                timeout=60.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract text from response
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            
            raise ValueError("No content in Gemini response")
    
    async def generate_text(
        self,
        task: LLMTask,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.3,
        fallback_to_claude: bool = True
    ) -> str:
        """
        Generate text using the optimal LLM for the task
        
        Args:
            task: Type of LLM task (determines which model to use)
            prompt: Text prompt for the model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            fallback_to_claude: If True, falls back to Claude if Gemini fails
            
        Returns:
            Generated text response
        """
        tier = self.get_tier_for_task(task)
        
        try:
            if tier == LLMTier.FAST:
                # Use Gemini Flash for simple tasks
                print(f"[LLM Router] Using Gemini Flash for {task.value} (cost-optimized)")
                return await self._call_gemini_api(prompt, max_tokens, temperature)
                
            else:
                # Use Claude Sonnet for complex tasks
                print(f"[LLM Router] Using Claude Sonnet for {task.value} (high-quality)")
                
                response = await self.claude_client.messages.create(
                    model=tier.value,
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
            print(f"[LLM Router] Error with {tier.value}: {error_msg}")
            
            # Fallback to Claude if Gemini fails and fallback is enabled
            if tier == LLMTier.FAST and fallback_to_claude:
                print(f"[LLM Router] Falling back to Claude Sonnet for {task.value}")
                
                try:
                    response = await self.claude_client.messages.create(
                        model=LLMTier.STANDARD.value,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    
                    response_text = ""
                    for block in response.content:
                        if block.type == "text":
                            response_text += block.text
                    
                    return response_text
                    
                except Exception as fallback_error:
                    print(f"[LLM Router] Fallback to Claude also failed: {fallback_error}")
                    raise fallback_error
            
            # Re-raise original error if no fallback or fallback disabled
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
        cost_multipliers = {
            LLMTier.FAST: 0.025,      # ~40x cheaper than Sonnet
            LLMTier.STANDARD: 1.0,     # Baseline
        }
        
        return cost_multipliers.get(tier, 1.0)


# Singleton instance
llm_router = LLMRouter()
