import discord
from discord.app_commands.errors import AppCommandError
from discord.ext import commands

from core.models import Field
from loggers import setup_package_logger

__all__ = ("leetcode", "pi", "kasa", "gpt", "arcaea", "mygo")


class CogsExtension(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.logger = setup_package_logger(f"{self.__module__}.{self.__class__.__name__}")
        self.logger.info(f"Loading: {self.__module__}.{self.__class__.__name__}")

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        self.logger.error(f"Error in command `{ctx.command.qualified_name}`:\n{error}")
        self.logger.exception(error)

        await ctx.send(
            f"Error in command `{ctx.command.qualified_name}`:\n```python\n{error!r}\n```"
        )

    async def cog_app_command_error(
        self, interaction: discord.Interaction[discord.Client], error: AppCommandError
    ) -> None:
        self.logger.error(f"Error in command `{interaction.command.qualified_name}`:\n{error}")
        self.logger.exception(error)

        await interaction.response.send_message(
            f"Error in command `{interaction.command.qualified_name}`:\n```python\n{error}\n```"
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
