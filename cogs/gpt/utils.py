import inspect
import warnings
from collections.abc import Callable, Coroutine, Iterable
from textwrap import dedent
from typing import Any, Literal

import discord
import openai
from openai import pydantic_function_tool
from openai._types import NOT_GIVEN, FileTypes, NotGiven
from openai.types import CompletionUsage, Image
from openai.types.audio.transcription import Transcription
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from pydantic import BaseModel

from config import OpenAIConfig
from core.classes import BaseClassMixin
from core.models import Field

FuncType = Callable[..., Coroutine[Any, Any, Any]] | None


def is_pydantic_model(obj: Any) -> bool:
    result = isinstance(obj, BaseModel)
    if result is False:
        try:
            result = issubclass(obj, BaseModel)

        except TypeError:  # issubclass() arg 1 must be a class
            return False

    return result


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
    tools_mapping: dict[str, ChatCompletionToolParam] = {}

    @property
    def history(self) -> list[dict]:
        return self._history

    @property
    def tools(self) -> list[ChatCompletionToolParam]:
        return list(self.tools_mapping.values())

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._history = [self.behavior]
        self.client = openai.AsyncOpenAI(**kwargs)

    async def setup_behavior(self, behavior: str):
        if isinstance(behavior, str):
            self.behavior = {"role": "system", "content": behavior}
        else:
            self.behavior = behavior

        self._history = [self.behavior]

    async def detect_malicious_content(self, prompt: str) -> bool:
        self.logger.info("Checking for malicious content in the prompt: %s", prompt)
        response = await self.client.moderations.create(input=prompt)
        result = response.results[0]

        self.logger.info("Moderation result: %s", result.model_dump_json(indent=2))
        return result.flagged or any(result.categories.model_dump().values())

    async def _send_message(
        self,
        parse_response: bool = False,
        response_format: dict | BaseModel | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> ChatCompletion | ParsedChatCompletion:
        messages = kwargs.pop("messages", self._history)
        method = self.client.chat.completions.create
        if parse_response or is_pydantic_model(response_format):
            method = self.client.beta.chat.completions.parse

        return await method(
            messages=messages,
            response_format=response_format,
            **kwargs,
        )

    async def ask(
        self,
        prompt: str | list[dict],
        model: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        **openai_kwargs,
    ) -> tuple[str, CompletionUsage]:
        if isinstance(prompt, str) and (await self.detect_malicious_content(prompt)):
            raise ValueError("This Prompt contains malicious content")

        self.logger.info("Asking the ChatGPT API with the prompt: %s", prompt)
        self._history.append({"role": "user", "content": prompt})
        response = await self._send_message(model=model, **openai_kwargs)
        return response.choices[0].message.content, response.usage

    async def create_images(
        self,
        prompt: str,
        model: Literal["dall-e-2", "dall-e-3"] = OpenAIConfig.IMAGE_MODEL,
        quality: Literal["standard", "hd"] = OpenAIConfig.IMAGE_QUALITY,
        size: Literal[
            "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
        ] = OpenAIConfig.IMAGE_SIZE,
    ) -> list[Image]:
        if await self.detect_malicious_content(prompt):
            raise ValueError("This Prompt contains malicious content")

        self.logger.info("Creating images with the prompt: %s", prompt)
        results = await self.client.images.generate(
            prompt=prompt, model=model, quality=quality, size=size
        )
        return results.data

    async def vision(
        self,
        text: str,
        image_content: str,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.VISION_MODEL,
    ) -> tuple[str, CompletionUsage]:
        """Returns the response from the vision model
        Args:
            text: the prompt to the model
            image_text: the base64 encoded image.
        """
        if await self.detect_malicious_content(text):
            raise ValueError("This Prompt contains malicious content")

        self.logger.info("Asking the vision model with the prompt: %s", text)
        if (
            image_content.startswith("http") is False
        ):  # assume that the image is either a base64 encoded string or a file url
            image_content = f"data:image/jpeg;base64,{image_content}"

        vision_prompt = [
            {
                "type": "image_url",
                "image_url": {"url": image_content, "detail": OpenAIConfig.VISION_DETAIL},
            },
            {"type": "text", "text": text},
        ]
        return await self.ask(vision_prompt, model=model)

    async def transcribe(self, audio_file: FileTypes) -> Transcription:
        transcript = await self.client.audio.transcriptions.create(
            file=audio_file, model="whisper-1"
        )
        return transcript

    async def static_ask(
        self,
        prompt: str,
        *hint_shots: dict,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        response_format: type[BaseModel] | BaseModel | dict | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> tuple[str | BaseModel, CompletionUsage]:
        if (
            isinstance(response_format, dict) is False
            and is_pydantic_model(response_format) is False
        ):
            raise ValueError(
                f"response_format must be a Pydantic model or a dict, got {response_format}"
            )

        behavior: dict = kwargs.pop("behavior", self.behavior)
        messages = [behavior, *hint_shots, {"role": "user", "content": prompt}]
        response: ChatCompletion | ParsedChatCompletion = await self._send_message(
            messages=messages, **kwargs, response_format=response_format, model=model, **kwargs
        )
        content: str | BaseModel = response.choices[0].message.content
        if is_pydantic_model(response_format):
            content: BaseModel = response.choices[0].message.parsed

        return content, response.usage

    async def add_tools(self, func_args: type[BaseModel]):
        if not (
            hasattr(func_args, "model_config") or func_args.model_config.get("title") is not None
        ):
            raise ValueError(
                """
                You must specify the title in your pydantic model's `model_config`.
                for example: `model_config = {'title': 'your_function_name'}`
                make sure that the title is unique and is same as the function name you want to call
                """
            )

        func_name = func_args.model_config["title"]
        func_item = pydantic_function_tool(func_args, name=func_name)
        if func_name in self.tools_mapping:
            warnings.warn(
                f"""
                The function {func_name} is already registered as a tool.
                The previous registration will be overwritten.
                """
            )
        self.tools_mapping[func_name] = func_item

    async def function_calling(
        self,
        func: FuncType,
        prompt: str,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        **kwargs,
    ) -> tuple[str, CompletionUsage]:
        """Currently only supports synchronous functions"""
        if func.__name__ not in self.tools_mapping:
            raise ValueError(
                f"""
                The function {func.__name__} is not registered as a tool.
                Please use `add_tools` method to register the function arguments as a Pydantic model
                """
            )

        messages = []
        messages.append(self.behavior)
        messages.append({"role": "user", "content": prompt})

        tools_response: ParsedChatCompletion = await self._send_message(
            messages=messages,
            model=model,
            tools=self.tools,
            tool_choice={"type": "function", "function": {"name": func.__name__}},
            parse_response=True,
            **kwargs,
        )
        if getattr(tools_response.choices[0].message, "refusal", None) is not None:
            raise ValueError(tools_response.choices[0].message.refusal)

        self.logger.debug("Function calling response: %s", tools_response.model_dump_json(indent=2))

        # check if function calling method is not being refused
        response_calls = tools_response.choices[0].message.tool_calls[0]
        response_function = response_calls.function

        function_kwargs = response_function.parsed_arguments.model_dump()

        # check whether the function is async or not
        if inspect.iscoroutinefunction(func):
            calling_result = await func(**function_kwargs)
        else:
            calling_result = func(**function_kwargs)

        function_call_result_message = {
            "role": "tool",
            # convert it to list if the function return iterable, otherwise convert it to string
            "content": str(calling_result)
            if isinstance(calling_result, Iterable) is False
            else list(map(lambda text: {"text": text, "type": "text"}, calling_result)),
            "tool_call_id": response_calls.id,
        }

        messages.append(tools_response.choices[0].message)
        messages.append(function_call_result_message)

        final_response = await self._send_message(
            messages=messages,
            model=model,
            **kwargs,
        )
        self.logger.debug("Function calling result: %s", final_response.choices[0].message.content)
        return final_response.choices[0].message.content, final_response.usage


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
