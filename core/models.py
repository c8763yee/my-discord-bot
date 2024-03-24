from typing import Any

from pydantic import BaseModel


class Field(BaseModel):
    name: str
    value: Any
    inline: bool = False
