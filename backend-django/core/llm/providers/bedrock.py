from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import boto3
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

from ..types import BaseGenOptions, ChatMessage, LLMClient


class BedrockAdapter(LLMClient):
    provider = "bedrock"

    def __init__(self) -> None:
        # AWS Bedrock uses boto3 client, not API keys
        # Credentials can come from:
        # 1. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars
        # 2. AWS credentials file (~/.aws/credentials)
        # 3. IAM role (when running on EC2/Lambda)
        # 4. Explicit credentials passed via settings
        
        # Check if explicit credentials are provided in settings
        aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID", None) or getattr(settings, "BEDROCK_AWS_ACCESS_KEY_ID", None)
        aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None) or getattr(settings, "BEDROCK_AWS_SECRET_ACCESS_KEY", None)
        aws_region = getattr(settings, "BEDROCK_AWS_REGION", None)
        
        if not aws_region:
            raise ValueError("BEDROCK_AWS_REGION is required")
        
        # Create boto3 client for Bedrock Runtime
        client_kwargs = {
            "service_name": "bedrock-runtime",
            "region_name": aws_region,
        }
        
        # Only add credentials if explicitly provided
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key
        
        self.client = boto3.client(**client_kwargs)
        self.model_id = getattr(settings, "BEDROCK_MODEL_ID", None)
        
        # Validate model ID is set
        if not self.model_id:
            raise ValueError("BEDROCK_MODEL_ID is required")

    def _prepare_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Convert ChatMessage list to Bedrock format."""
        bedrock_messages = []
        for msg in messages:
            # Bedrock uses "user" and "assistant" roles
            role = msg.role if msg.role != "system" else "user"
            bedrock_messages.append({
                "role": role,
                "content": msg.content
            })
        return bedrock_messages

    def _invoke_model(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        """Invoke Bedrock model with messages."""
        # Prepare request body based on model provider
        # Most Bedrock models use Anthropic's message format
        if "anthropic" in self.model_id.lower() or "claude" in self.model_id.lower():
            # Anthropic Claude format
            system_messages = [msg["content"] for msg in messages if msg["role"] == "system"]
            conversation_messages = [msg for msg in messages if msg["role"] != "system"]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": temperature,
                "messages": conversation_messages,
            }
            
            if system_messages:
                body["system"] = "\n".join(system_messages)
            
            if json_mode:
                body["response_format"] = {"type": "json_object"}
        else:
            # Generic format for other models (Meta Llama, etc.)
            body = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4096,
            }
            
            if json_mode:
                body["response_format"] = {"type": "json_object"}
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        return response_body

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_text(
        self, prompt: str, options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        messages = [ChatMessage(role="user", content=prompt)]
        bedrock_messages = self._prepare_messages(messages)
        
        # Use synchronous boto3 client in async context
        # Note: boto3 is synchronous, but we're wrapping it in async
        import asyncio
        try:
            # Python 3.9+ has asyncio.to_thread
            response_body = await asyncio.to_thread(
                self._invoke_model,
                bedrock_messages,
                opts.temperature,
                False
            )
        except AttributeError:
            # Fallback for Python < 3.9
            loop = asyncio.get_event_loop()
            response_body = await loop.run_in_executor(
                None,
                self._invoke_model,
                bedrock_messages,
                opts.temperature,
                False
            )
        
        # Extract text from response based on model type
        if "anthropic" in self.model_id.lower() or "claude" in self.model_id.lower():
            # Anthropic Claude response format
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0].get("text", "")
        else:
            # Generic format
            if "generation" in response_body:
                return response_body["generation"]
            elif "content" in response_body:
                return response_body["content"]
            elif "outputText" in response_body:
                return response_body["outputText"]
        
        return ""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        options: Optional[BaseGenOptions] = None,
    ) -> Dict[str, Any]:
        opts = options or BaseGenOptions(json_mode=True)
        messages = [ChatMessage(role="user", content=f"{prompt}\nReturn ONLY strict JSON that conforms to the provided schema.")]
        bedrock_messages = self._prepare_messages(messages)
        
        import asyncio
        try:
            # Python 3.9+ has asyncio.to_thread
            response_body = await asyncio.to_thread(
                self._invoke_model,
                bedrock_messages,
                opts.temperature,
                True
            )
        except AttributeError:
            # Fallback for Python < 3.9
            loop = asyncio.get_event_loop()
            response_body = await loop.run_in_executor(
                None,
                self._invoke_model,
                bedrock_messages,
                opts.temperature,
                True
            )
        
        # Extract text from response
        if "anthropic" in self.model_id.lower() or "claude" in self.model_id.lower():
            if "content" in response_body and len(response_body["content"]) > 0:
                text = response_body["content"][0].get("text", "")
        else:
            text = response_body.get("generation") or response_body.get("content") or response_body.get("outputText", "")
        
        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text if wrapped
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse JSON from response: {text[:200]}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
    async def chat(
        self, messages: List[ChatMessage], options: Optional[BaseGenOptions] = None
    ) -> str:
        opts = options or BaseGenOptions()
        bedrock_messages = self._prepare_messages(messages)
        
        import asyncio
        try:
            # Python 3.9+ has asyncio.to_thread
            response_body = await asyncio.to_thread(
                self._invoke_model,
                bedrock_messages,
                opts.temperature,
                False
            )
        except AttributeError:
            # Fallback for Python < 3.9
            loop = asyncio.get_event_loop()
            response_body = await loop.run_in_executor(
                None,
                self._invoke_model,
                bedrock_messages,
                opts.temperature,
                False
            )
        
        # Extract text from response
        if "anthropic" in self.model_id.lower() or "claude" in self.model_id.lower():
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0].get("text", "")
        else:
            return response_body.get("generation") or response_body.get("content") or response_body.get("outputText", "")
        
        return ""

