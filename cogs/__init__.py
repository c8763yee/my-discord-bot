from typing import Optional

import discord
from discord.ext import commands

from core.models import Field
from loggers import setup_package_logger

__all__ = ('leetcode', 'pi', 'kasa', 'gpt', 'arcaea')


class CogsExtension(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = setup_package_logger(f'{self.__module__}')

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f'{self.__class__.__name__} is ready.')

    async def create_embed(self,  title: str,  description: str,
                           color: Optional[discord.Color] = discord.Color.red(),
                           url: Optional[str] = None,
                           thumbnail_url: Optional[str] = None,
                           *fields: Field):
        """
        Create an embed message with given parameters.
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            url=url
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        for field in fields:
            embed.add_field(name=field.name, value=field.value,
                            inline=field.inline)

        return embed
