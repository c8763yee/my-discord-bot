import os
from textwrap import dedent

import discord
import openai
from openai.types import CompletionUsage, Image
from openai.types.chat import ChatCompletion

from cogs import CogsExtension, Field
from loggers import setup_package_logger

from . import const

logger = setup_package_logger(__name__)


class ChatGPT:
    """
    A chatbot based on OpenAI's chat API
    if the chat history doesn't need to save, then use DUMMY_UUID as UUID
    """

    behavior = {
        "role": "system",
        "content": dedent("""
        You are a helpful assistant to help me with my tasks. please answer my questions with my language.
        """)
    }

    client = openai.AsyncOpenAI()

    def __init__(self):
        self._history = [self.behavior]

    @classmethod
    async def detect_malicious_content(cls, prompt: str) -> bool:
        response = await cls.client.moderations.create(input=prompt)
        result = response.results[0]

        logger.info(f"Moderation result: {result}")
        return (result.flagged or
                any(cate is True
                    for cate in result.categories.model_dump().values())
                )

    async def send_message(
            self,
            max_tokens: int = const.MAX_TOKENS,
            model: str = const.CHAT_MODEL,
            **kwargs) -> ChatCompletion:
        response = await self.client.chat.completions.create(messages=self._history,
                                                             max_tokens=max_tokens,
                                                             model=model, **kwargs)
        return response

    async def ask(self, prompt: str, **open_kwargs) -> tuple[str, CompletionUsage]:
        if await self.detect_malicious_content(prompt):
            raise ValueError("This Prompt contains malicious content")

        self._history.append({"role": "user", "content": prompt})
        response = await self.send_message(**open_kwargs)
        return response.choices[0].message.content, response.usage

    @classmethod
    async def create_images(
        cls,
        prompt: str,
        model: str = const.DALL_E_MODEL,
        quality: str = const.IMAGE_QUALITY,
        size: str = const.IMAGE_SIZE,
    ) -> list[Image]:
        if await cls.detect_malicious_content(prompt):
            raise ValueError("This Prompt contains malicious content")

        results = await cls.client.images.generate(prompt=prompt, model=model, quality=quality, size=size)
        return results.data


class ChatGPTUtils(CogsExtension):
    async def ask(self, question: str) -> tuple[str, discord.Embed]:
        chatbot = ChatGPT()
        answer, usage = await chatbot.ask(question)
        usage_embed = await self.create_embed(
            'ChatGPT Usage Information',
            'In this response, the usage information of the ChatGPT API is included.',
            discord.Color.blurple(),
            'https://chat.openai.com/docs/usage',
            'https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg',
            Field(name='completion_tokens', value=usage.completion_tokens),
            Field(name='prompt_tokens', value=usage.prompt_tokens),
            Field(name='total_tokens', value=usage.total_tokens),
        )

        return answer, usage_embed

    async def generate_image(self, prompt: str) -> str:
        chatbot = ChatGPT()
        images = await chatbot.create_images(prompt)
        return images[0].url
