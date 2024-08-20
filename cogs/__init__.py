import discord
from discord.ext import commands

from core.models import Field
from loggers import setup_package_logger

__all__ = ("leetcode", "pi", "kasa", "gpt", "arcaea")


class CogsExtension(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.logger = setup_package_logger(
            getattr(self.__class__, "__qualname__", self.__class__.__name__)
        )

    @classmethod
    async def create_embed(cls, title: str, description: str, *fields: Field, **kwargs):
        """Create an embed message with given parameters."""
        embed = discord.Embed(
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
