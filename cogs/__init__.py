import discord
from discord.app_commands.errors import AppCommandError
from discord.ext import commands

from core.classes import BaseClassMixin
from loggers import setup_package_logger

__all__ = ("leetcode", "pi", "kasa", "gpt", "arcaea", "mygo")


class CogsExtension(commands.Cog, BaseClassMixin):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.logger = setup_package_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.logger.info("Loaded class %s.%s", self.__class__.__module__, self.__class__.__name__)

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        self.logger.error("Error in command `%s`:\n%s", ctx.command.qualified_name, error)
        self.logger.exception(error)

        await ctx.send(
            f"Error in command `{ctx.command.qualified_name}`:\n```python\n{error!r}\n```"
        )

    async def cog_app_command_error(
        self, interaction: discord.Interaction[discord.Client], error: AppCommandError
    ) -> None:
        self.logger.error("Error in command `%s`:\n%s", interaction.command.qualified_name, error)
        self.logger.exception(error)

        await interaction.response.send_message(
            f"Error in command `{interaction.command.qualified_name}`:\n```python\n{error}\n```"
        )
