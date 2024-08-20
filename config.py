from typing import Literal


class OpenAIConfig:
    MAX_TOKENS: int = 1024
    VISION_DETAIL: Literal["low", "high", "auto"] = "low"
    IMAGE_RESPONSE_FORMAT: Literal["b64_json", "url"] = "url"
    IMAGE_QUALITY: Literal["standard", "hd"] = "standard"
    IMAGE_SIZE: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "512x512"
    IMAGE_MODEL: Literal["dall-e-2", "dall-e-3"] = "dall-e-2"
    CHAT_MODEL: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = "gpt-4o-mini"
    VISION_MODEL: Literal["gpt-4o", "gpt-4o-mini"] = "gpt-4o-mini"


class Config:
    DEBUG = True
