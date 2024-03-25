from typing import Literal


class OpenAIConfig:
    MAX_TOKENS: int = 1024
    CHAT_MODEL: str = "gpt-3.5-turbo-0125"
    VISION_DETAIL: Literal["low", "high", "auto"] = "low"


class Config:
    DEBUG = True
