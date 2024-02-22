import os

from discord.ext import commands
import discord
from pydantic import BaseModel
import typing
from typing import Optional
from loggers import setup_package_logger


class Field(BaseModel):
    name: str
    value: typing.Any
    inline: bool = False


__all__ = ('leetcode', )

logger = setup_package_logger(f'{__name__}.__init__')


class Cog_Extension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'{self.__class__.__name__} is ready.')

    async def create_embed(self,  title: str, description: str, thumbnail_url: Optional[str] = None,  color: Optional[int] = 0x000000,  *fields: Field):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        for field in fields:
            embed.add_field(name=field.name, value=field.value,
                            inline=field.inline)

        return embed
