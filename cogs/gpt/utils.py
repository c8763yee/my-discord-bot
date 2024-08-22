from textwrap import dedent
from typing import Literal

import discord
import openai
from openai.types import CompletionUsage, Image
from openai.types.chat import ChatCompletion

from config import OpenAIConfig
from core.classes import BaseClassMixin
from core.models import Field


class ChatGPT(BaseClassMixin):
    """A chatbot based on OpenAI's chat API
    if the chat history doesn't need to save, then use DUMMY_UUID as UUID.
    """

    behavior = {
        "role": "system",
        "content": dedent(
            """
        You are a helpful assistant to help me with my tasks.
        please answer my questions with my language.
        """
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._history = [self.behavior]
        self.client = openai.AsyncOpenAI(**kwargs)

    async def detect_malicious_content(self, prompt: str) -> bool:
        response = await self.client.moderations.create(input=prompt)
        result = response.results[0]

        self.logger.info("Moderation result: %s", result.model_dump_json(indent=2))
        return result.flagged or any(
            cate is True for cate in result.categories.model_dump().values()
        )

    async def _send_message(
        self,
        max_tokens: int = OpenAIConfig.MAX_TOKENS,
        model: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        **kwargs,
    ) -> ChatCompletion:
        response = await self.client.chat.completions.create(
            messages=self._history, max_tokens=max_tokens, model=model, **kwargs
        )
        self.logger.info("ChatGPT Response: %s", response.model_dump_json(indent=2))
        return response

    async def ask(self, prompt: str, **open_kwargs) -> tuple[str, CompletionUsage]:
        if await self.detect_malicious_content(prompt):
            raise ValueError("This Prompt contains malicious content")

        self._history.append({"role": "user", "content": prompt})
        response = await self._send_message(**open_kwargs)
        return response.choices[0].message.content, response.usage

    async def create_images(
        self,
        prompt: str,
        model: str,
        quality: str = OpenAIConfig.IMAGE_QUALITY,
        size: str = OpenAIConfig.IMAGE_SIZE,
    ) -> list[Image]:
        if await self.detect_malicious_content(prompt):
            raise ValueError("This Prompt contains malicious content")

        results = await self.client.images.generate(
            prompt=prompt, model=model, quality=quality, size=size
        )
        return results.data

    async def vision(
        self,
        text: str,
        image_url: str,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.VISION_MODEL,
    ):
        """Returns the response from the vision model
        Args:
            text: the prompt to the model
            image_text: the base64 encoded image.
        """
        if await self.detect_malicious_content(text):
            raise ValueError("This Prompt contains malicious content")

        vision_prompt = [
            {
                "type": "image_url",
                "image_url": {"url": image_url, "detail": OpenAIConfig.VISION_DETAIL},
            },
            {"type": "text", "text": text},
        ]
        return await self.ask(vision_prompt, model=model)


class ChatGPTUtils:
    def __init__(self):
        self.chatbot = ChatGPT()

    async def ask(self, question: str, model: str) -> str:
        answer, token_usage = await self.chatbot.ask(question, model=model)
        return answer, token_usage

    async def generate_image(self, prompt: str, model: str) -> str:
        images = await self.chatbot.create_images(prompt=prompt, model=model)
        return images[0].url

    async def vision(
        self,
        text: str,
        image_url: str,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.VISION_MODEL,
    ) -> str:
        return await self.chatbot.vision(text, image_url, model=model)


class ChatGPTResponseFormatter:
    @classmethod
    async def usage(cls, usage: CompletionUsage) -> tuple[str, discord.Embed]:
        usage_embed = await BaseClassMixin.create_embed(
            "ChatGPT Usage Information",
            "In this response, the usage information of the ChatGPT API is included.",
            Field(name="completion_tokens", value=usage.completion_tokens),
            Field(name="prompt_tokens", value=usage.prompt_tokens),
            Field(name="total_tokens", value=usage.total_tokens),
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg",
            color=discord.Color.blurple(),
            url="https://chat.openai.com/docs/usage",
        )

        return usage_embed
