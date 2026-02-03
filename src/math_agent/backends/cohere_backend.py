import os
import cohere
import logging
from typing import List, Optional
from .base import LLMBackend

logger = logging.getLogger(__name__)

class CohereBackend(LLMBackend):
    def __init__(self, api_key: Optional[str] = None, model: str = "command-r-08-2024"):
        self.api_key = api_key or os.getenv("CO_API_KEY")
        if not self.api_key:
            raise ValueError("CO_API_KEY environment variable not set.")
        
        # Determine if we should use V2.
        # command-a-reasoning models require V2.
        # We'll use ClientV2 for all interactions to be future-proof and support reasoning.
        try:
            self.client = cohere.ClientV2(self.api_key)
            self.use_v2 = True
        except AttributeError:
            # Fallback for older SDKs if ClientV2 is missing (unlikely given our setup)
            self.client = cohere.Client(self.api_key)
            self.use_v2 = False
            
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, other_prompts: Optional[List[str]] = None, temperature: float = 0.7) -> str:
        
        # Construct the message(s)
        if self.use_v2:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": user_prompt})
            
            if other_prompts:
                for prompt in other_prompts:
                    messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            
            if response.message and response.message.content:
                content_blocks = response.message.content
                thinking_text = ""
                final_text = ""
                
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if block.type == "thinking":
                            thinking_text += block.thinking
                        elif block.type == "text":
                            final_text += block.text
                else:
                    # Fallback if structure is simple text
                    final_text = str(content_blocks)

                if thinking_text:
                    # Log the thinking trace for debugging/audit, but do not return it to the user.
                    logger.info(f"Thinking Trace for request:\n{thinking_text}")
                
                return final_text
            return ""

        else:
            # V1 Fallback
            message = user_prompt
            if other_prompts:
                message += "\n\n" + "\n\n".join(other_prompts)

            response = self.client.chat(
                model=self.model,
                message=message,
                preamble=system_prompt,
                temperature=temperature,
            )
            return response.text
