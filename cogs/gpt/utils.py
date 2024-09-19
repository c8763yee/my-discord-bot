import inspect
import json
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
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from config import OpenAIConfig
from core.classes import BaseClassMixin, Field
from database import Chat, ChatHistory, engine

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
    if the chat history doesn't need to save, then use DUMMY_str as str.
    """

    system_prompt = dedent(
        """
        You are a helpful assistant to help me with my tasks.
        please answer my questions with my language.
        """
    )
    tools_mapping: dict[str, ChatCompletionToolParam] = {}

    @property
    def tools(self) -> list[ChatCompletionToolParam]:
        return list(self.tools_mapping.values())

    @property
    def history(self) -> list[dict]:
        return self.__history

    @property
    def history_id(self) -> str | None:
        return self.__history_id

    async def retrieve_history(self, init_message: str | None = None, raise_error: bool = False):
        if init_message is None:
            init_message = self.system_prompt

        if self.__use_db is False:
            return await self.append_history(init_message, role="system")

        async with AsyncSession(engine) as session:
            old_item = (
                await session.exec(select(Chat).where(Chat.history_id == self.history_id))
            ).first()

            if old_item is None and raise_error:
                self.logger.warning("The chat history is not found in the database")
                return

            elif old_item is None:
                await self.append_history(init_message, role="system")
                return

            history_message = (
                await session.exec(
                    select(ChatHistory.role, ChatHistory.content).where(
                        ChatHistory.chat_id == self.history_id
                    )
                )
            ).all()

        for role, text_content in history_message:
            try:
                content = json.loads(text_content.strip())
            except json.JSONDecodeError:
                self.logger.debug(
                    "Failed to decode image content from the database, using as string"
                )
                content = text_content

            self.__history.append({"role": role, "content": content})

    async def insert_to_db(self, role: str, content: str | list[dict]):
        if self.__use_db is False:
            return

        async with AsyncSession(engine) as session:
            if isinstance(content, list):
                content = json.dumps(content)

            chat = Chat(history_id=self.history_id)

            if (
                await session.exec(select(Chat).where(Chat.history_id == self.history_id))
            ).first() is None:
                session.add(chat)

            history = ChatHistory(chat_id=self.history_id, role=role, content=content)
            session.add(history)
            await session.commit()

    async def pop_from_db(self) -> ChatHistory:
        if self.__use_db is False:
            raise ValueError("The chat history is not saved in the database")

        async with AsyncSession(engine) as session:
            history_object = await session.exec(
                select(ChatHistory).where(ChatHistory.chat_id == self.history_id).order_by()
            ).first()
            await session.delete(history_object)
            await session.commit()
        return history_object

    async def check_message(self, messages: list[dict]):
        for idx, message in enumerate(messages):
            if message["role"] != "user":  # we only need to check the user messages
                continue
            if isinstance(message["content"], list) is False:
                if await self.detect_malicious_content(message["content"]):
                    self.__history = self.__history[:idx]
                    await self.pop_from_db()
                    raise ValueError(
                        f"Malicious content detected in the message: {message['content']}"
                    )
                continue

            for item in message["content"]:
                if item["type"] == "image_url":
                    continue

                if await self.detect_malicious_content(item["text"]):
                    self.__history = self.__history[:idx]
                    await self.pop_from_db()
                    raise ValueError(f"Malicious content detected in the message: {item['text']}")

    async def clear_history(self):
        self.__history = []
        if self.__use_db is False:
            return

        async with AsyncSession(engine) as session:
            chat_object = (
                await session.exec(
                    select(ChatHistory).where(ChatHistory.chat_id == self.history_id)
                )
            ).all()
            if chat_object is not None:
                await session.exec(
                    delete(ChatHistory).where(ChatHistory.chat_id == self.history_id)
                )
                await session.commit()

    def print_history(self):
        """Print the chat history for debugging purposes"""
        for idx, chat in enumerate(self.history):
            if isinstance(chat["content"], str):
                self.logger.debug("%d: history(%s): %s", idx, chat["role"], chat["content"])

            elif isinstance(chat["content"], list):
                for i, item in enumerate(chat["content"]):
                    text = item.get(item["type"], "")
                    if item["type"] == "image_url":
                        text = "<IMAGE>"

                    self.logger.debug("%d: history(%s)[%s]: %s", idx, chat["role"], i, text)

    async def append_history(
        self, content: str | list[dict], role: Literal["user", "system", "assistant"] = "user"
    ) -> "ChatGPT":
        self.__history.append({"role": role, "content": content})
        await self.insert_to_db(role, content)

    async def append_image(self, image_b64: str, text: str | None = None) -> "ChatGPT":
        vision_prompt = []
        if text is not None:
            vision_prompt.append({"type": "text", "text": text})

        image_url = image_b64
        if image_b64.startswith("http") is False and image_b64.startswith("data:image") is False:
            image_url = f"data:image/jpeg;base64,{image_b64}"

        vision_prompt.append(
            {
                "type": "image_url",
                "image_url": {"url": image_url, "detail": OpenAIConfig.VISION_DETAIL},
            }
        )
        await self.append_history(vision_prompt)

    async def setup_behavior(self, behavior: str | None = None) -> "ChatGPT":
        if behavior is None:
            behavior = self.system_prompt

        if self.__use_db:
            async with AsyncSession(engine) as session:
                chat_object = (
                    await session.exec(select(Chat).where(Chat.history_id == self.history_id))
                ).first()
                if chat_object is None:
                    chat = Chat(history_id=self.history_id)
                    session.add(chat)
                else:
                    await self.clear_history()
                await session.commit()

        await self.append_history(behavior, role="system")

    def __init__(self, *_, history_id: str | None = None, use_db: bool = False, **kwargs):
        super().__init__()
        self.client = openai.AsyncOpenAI(**kwargs)

        if history_id is None and use_db:
            raise ValueError("The history_id must be provided when use_db is True")

        self.__history_id = history_id
        self.__history = []

        self.__use_db = use_db

    async def detect_malicious_content(self, prompt: str) -> bool:
        if isinstance(prompt, str) is False:
            raise ValueError("Prompt must be a string")

        self.logger.info("Checking for malicious content in the prompt: %s", prompt)
        response = await self.client.moderations.create(input=prompt)
        result = response.results[0]

        self.logger.info("Moderation result: %s", result.model_dump())
        return (
            result.flagged
            or any(flag for flag in result.categories.model_dump().values())
            or any(
                score >= OpenAIConfig.MALICIOUS_THRESHOLD
                for score in result.category_scores.model_dump().values()
            )
        )

    async def apply_message(
        self,
        model: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        parse_response: bool = False,
        response_format: dict | BaseModel | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> ChatCompletion | ParsedChatCompletion:
        messages = kwargs.pop("messages", self.__history)
        await self.check_message(messages)

        method = self.client.chat.completions.create
        if parse_response or is_pydantic_model(response_format):
            method = self.client.beta.chat.completions.parse

        result = await method(
            messages=messages, response_format=response_format, model=model, **kwargs
        )
        self.logger.info(
            "Completion Usage(%s): %s", self.history_id, result.usage.model_dump_json(indent=2)
        )
        return result

    async def ask(
        self,
        prompt: str | list[dict],
        model: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        **openai_kwargs,
    ) -> tuple[str, CompletionUsage]:
        self.logger.info("Asking the ChatGPT API with the prompt: %s", prompt)
        await self.append_history(prompt, role="user")
        response = await self.apply_message(model=model, **openai_kwargs)
        message = response.choices[0].message
        await self.append_history(message.content, role=message.role)
        return message.content, response.usage

    async def generate_images(
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
        prompt: str,
        image_url: str,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.VISION_MODEL,
    ) -> tuple[str, CompletionUsage]:
        """Returns the response from the vision model
        Args:
            text: the prompt to the model
            image_text: the base64 encoded image.
        """
        self.logger.info("Asking the vision model with the prompt: %s", prompt)
        self.append_image(image_url, text=prompt)
        response = await self.apply_message(model=model)
        message = response.choices[0].message
        self.append_history(message.content, role=message.role)
        return message.content, response.usage

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

        behavior: dict = kwargs.pop("behavior", self.system_prompt)
        messages = [behavior, *hint_shots, {"role": "user", "content": prompt}]
        response: ChatCompletion | ParsedChatCompletion = await self.apply_message(
            messages=messages, **kwargs, response_format=response_format, model=model, **kwargs
        )

        content: str | BaseModel
        if is_pydantic_model(response_format):
            content = response.choices[0].message.parsed
        else:
            content = response.choices[0].message.content

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
        """Call function that is registered as a tool in the ChatGPT API
        NOTE: This method will not effect the chat history as it will be a separate conversation

        """
        if func.__name__ not in self.tools_mapping:
            raise ValueError(
                f"""
                The function {func.__name__} is not registered as a tool.
                Please use `add_tools` method to register the function arguments as a Pydantic model
                """
            )

        messages = []
        messages.append(self.system_prompt)
        messages.append({"role": "user", "content": prompt})

        tools_response: ParsedChatCompletion = await self.apply_message(
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

        final_response = await self.apply_message(
            messages=messages,
            model=model,
            **kwargs,
        )
        self.logger.debug("Function calling result: %s", final_response.choices[0].message.content)
        return final_response.choices[0].message.content, final_response.usage


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
