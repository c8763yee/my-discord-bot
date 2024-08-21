import logging
import os
from pathlib import Path
from textwrap import dedent
from time import perf_counter

import discord
from discord.ext import commands
from dotenv import load_dotenv
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import cogs
from cogs.arcaea.utils import APIUtils
from cogs.mygo.schema import SubtitleItem, engine
from core.func import db_insert_episode, db_insert_subtitle_data, init_models
from loggers import setup_package_logger

env_path = Path.cwd() / "env" / "bot.env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, verbose=True)

logger = setup_package_logger("main", file_level=logging.INFO)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger: logging.Logger = setup_package_logger("main.bot", file_level=logging.INFO)

    async def on_ready(self):
        channel = self.get_channel(int(os.environ["TEST_CHANNEL_ID"]))

        for modules in cogs.__all__:
            start_time = perf_counter()
            await self.load_extension(f"cogs.{modules}")
            await channel.send(
                f"`{modules}` loaded in {perf_counter() - start_time:.2f}s",
                silent=True,
            )

        await self.tree.sync()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # mention owner when ready
        await channel.send(
            f"{self.user} is ready. <@{os.environ['OWNER_ID']}>",
            silent=True,
        )

        with (Path.cwd() / "json_data" / "mygo_detail.json").open("r", encoding="utf-8") as file:
            data = SubtitleItem.model_validate_json(file.read())

        await init_models()

        async with AsyncSession(engine) as session:
            for episode in ["1-3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                await db_insert_episode(episode, session)

            await db_insert_subtitle_data(data, session)


# ---------------------------- Initializing the bot ---------------------------- #
bot = Bot(
    command_prefix=commands.when_mentioned_or("!", "?", "hey SiRi, ", "!!!!!"),
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
