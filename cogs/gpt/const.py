from typing import Literal

MAX_TOKENS: int = 512
CHAT_MODEL: str = "gpt-3.5-turbo-0125"

IMAGE_QUALITY: Literal["standard", "hd"] = "standard"
IMAGE_SIZE: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "512x512"

DALL_E_MODEL: Literal["dall-e-2", "dall-e-3"] = "dall-e-2"
IMAGE_RESPONSE_FORMAT: Literal["b64_json", "url"] = "url"
