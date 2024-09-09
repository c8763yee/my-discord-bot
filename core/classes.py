from discord import Embed
from discord.ui import View

from loggers import setup_package_logger

from .models import Field


class BaseClassMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = setup_package_logger(f"{self.__module__}.{self.__class__.__name__}")
        self.logger.info("Loading: %s.%s", self.__module__, self.__class__.__name__)

    @classmethod
    async def create_embed(cls, title: str, description: str, *fields: Field, **kwargs) -> Embed:
        """Create an embed message with given parameters."""
        embed = Embed(
            title=title,
            description=description,
            color=kwargs.get("color"),
            url=kwargs.get("url"),
        )

        embed.set_thumbnail(url=kwargs.get("thumbnail_url"))
        embed.set_image(url=kwargs.get("image_url"))
        for field in fields:
            embed.add_field(name=field.name, value=field.value, inline=field.inline)

        return embed


class CogsView(BaseClassMixin, View): ...
