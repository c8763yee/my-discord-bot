from textwrap import dedent

import discord
import openai
from openai.types import CompletionUsage, Image
from openai.types.chat import ChatCompletion

from cogs import CogsExtension
from config import OpenAIConfig
from core.models import Field
from loggers import setup_package_logger

from . import const


class ChatGPT:
    """
    A chatbot based on OpenAI's chat API
    if the chat history doesn't need to save, then use DUMMY_UUID as UUID
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

    client = openai.AsyncOpenAI()
    logger = setup_package_logger(__name__)

    def __init__(self):
        self._history = [self.behavior]

    @classmethod
    async def detect_malicious_content(cls, prompt: str) -> bool:
        response = await cls.client.moderations.create(input=prompt)
        result = response.results[0]

        cls.logger.info("Moderation result: %s", result)
        return result.flagged or any(
            cate is True for cate in result.categories.model_dump().values()
        )

    async def send_message(
        self,
        max_tokens: int = const.MAX_TOKENS,
        model: str = const.CHAT_MODEL,
        **kwargs,
    ) -> ChatCompletion:
        response = await self.client.chat.completions.create(
            messages=self._history, max_tokens=max_tokens, model=model, **kwargs
        )
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

        results = await cls.client.images.generate(
            prompt=prompt, model=model, quality=quality, size=size
        )
        return results.data

    async def vision(self, text: str, images_b64: str):
        """
        returns the response from the vision model
        Args:
            text: the prompt to the model
            image_text: the base64 encoded image
        """
        if self.detect_malicious_content(text):
            raise ValueError("This Prompt contains malicious content")

        vision_prompt = [{"type": "text", "text": text}]
        for image_b64 in images_b64:
            image_url = f"data:image/png;base64,{image_b64}"
            vision_prompt.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (image_url),
                        "detail": OpenAIConfig.VISION_DETAIL,
                    },
                }
            )
        vision_response, usage = await self.ask(vision_prompt, model="gpt-4-vision-preview")
        # filter out the markdown syntax from the response
        return vision_response, usage


class ChatGPTUtils(CogsExtension):
    async def get_usage(self, question: str) -> str:
        chatbot = ChatGPT()
        answer, token_usage = await chatbot.ask(question)
        return answer, token_usage

    async def generate_image(self, prompt: str) -> str:
        chatbot = ChatGPT()
        images = await chatbot.create_images(prompt)
        return images[0].url


class ChatGPTResopnseFormatter(ChatGPTUtils):
    async def usage(self, usage: CompletionUsage) -> tuple[str, discord.Embed]:
        usage_embed = await self.create_embed(
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
