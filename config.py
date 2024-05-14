from typing import Literal


class OpenAIConfig:
    MAX_TOKENS: int = 1024
    VISION_DETAIL: Literal["low", "high", "auto"] = "low"
    IMAGE_RESPONSE_FORMAT: Literal["b64_json", "url"] = "url"
    IMAGE_QUALITY: Literal["standard", "hd"] = "standard"
    IMAGE_SIZE: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "512x512"


class Config:
    DEBUG = True
