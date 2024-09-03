import logging
import os
from pathlib import Path
from textwrap import dedent
from time import perf_counter

import discord
from discord.ext import commands

import cogs
from cogs.arcaea.utils import APIUtils
from core import load_env
from core.func import init
from loggers import setup_package_logger

load_env(path=Path.cwd() / "env" / "bot.env")

logger = setup_package_logger("main", file_level=logging.INFO)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger: logging.Logger = setup_package_logger("main.bot", file_level=logging.INFO)

    async def on_ready(self):
        await init()
        channel = self.get_channel(int(os.environ["TEST_CHANNEL_ID"]))

        for modules in cogs.__all__:
            start_time = perf_counter()
            await self.load_extension(f"cogs.{modules}")
            await channel.send(
                f"`{modules}` loaded in {perf_counter() - start_time:.2f}s",
                silent=True,
            )

        await self.tree.sync()

        # mention owner when ready
        await channel.send(
            f"{self.user} is ready. <@{os.environ['OWNER_ID']}>",
            silent=True,
        )


# ---------------------------- Initializing the bot ---------------------------- #
bot = Bot(
    command_prefix=commands.when_mentioned_or("!", "?", "!!!!!"),
    intents=discord.Intents.all(),
    help_command=commands.DefaultHelpCommand(dm_help=True),
    description="A bot for my Discord server.",
)


@bot.hybrid_command()
@commands.is_owner()
async def load(ctx: commands.Context, extension: str):
    """Load extension.(owner only)."""
    start_time = perf_counter()
    await ctx.interaction.response.defer()
    await bot.load_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(
        f"`{extension}` loaded in {perf_counter() - start_time:.2f}s", ephemeral=True
    )


@bot.hybrid_command()
@commands.is_owner()
async def unload(ctx: commands.Context, extension: str):
    """Unload extension.(owner only)."""
    start_time = perf_counter()
    await ctx.interaction.response.defer()
    await bot.unload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(
        f"`{extension}` unloaded in {perf_counter() - start_time:.2f}s", ephemeral=True
    )


@bot.hybrid_command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension: str):
    """Reload extension.(owner only)."""
    start_time = perf_counter()
    await ctx.interaction.response.defer()
    await bot.reload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(
        f"`{extension}` reloaded in {perf_counter() - start_time:.2f}s", ephemeral=True
    )


# ---------------------------- Running the bot ---------------------------- #

if __name__ == "__main__":
    assert os.environ.get("DISCORD_BOT_TOKEN", None) is not None, dedent(
        """
    DISCORD_BOT_TOKEN not found in env file, please add it in env/bot.env
    if you are first time using this bot, please rename envExample to env and fill in the token
    """
    )
    try:
        bot.run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None, log_level=logging.WARNING)
    finally:
        APIUtils.close_session()
        logger.info("Session closed")
