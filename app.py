import logging
import os
from pathlib import Path
from textwrap import dedent

import discord
from discord.ext import commands
from dotenv import load_dotenv
from sqlmodel import SQLModel

import cogs
from cogs.arcaea.utils import APIUtils
from cogs.mygo.schema import SubtitleItem, engine
from core.func import db_insert_episode, db_insert_subtitle_data, init_models
from loggers import setup_package_logger

if os.path.exists("env/bot.env"):
    load_dotenv(dotenv_path="env/bot.env", verbose=True)

logger = setup_package_logger("main", file_level=logging.INFO)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger: logging.Logger = setup_package_logger("main.bot", file_level=logging.INFO)

    async def on_ready(self):
        channel = self.get_channel(int(os.environ["TEST_CHANNEL_ID"]))

        for modules in cogs.__all__:
            await self.load_extension(f"cogs.{modules}")
            await channel.send(f"`{modules}` loaded", silent=True)

        await self.tree.sync()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # mention owner when ready
        await channel.send(
            f"{self.user} is ready. <@{os.environ['OWNER_ID']}>",
            silent=True,
        )

        with (Path.cwd() / "json_data" / "mygo_detail.json").open("r", encoding="utf-8") as f:
            data = SubtitleItem.model_validate_json(f.read())

        await init_models()

        for episode in ["1-3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
            await db_insert_episode(episode)

        await db_insert_subtitle_data(data)


# ---------------------------- Initialising the bot ---------------------------- #
bot = Bot(
    command_prefix=commands.when_mentioned_or("!", "?", "hey siri, "),
    intents=discord.Intents.all(),
    help_command=commands.DefaultHelpCommand(dm_help=True),
    description="A bot for my Discord server.",
)


@bot.hybrid_command()
@commands.is_owner()
async def load(ctx: commands.Context, extension: str):
    """Load extension.(owner only)."""
    await ctx.interaction.response.defer()
    await bot.load_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(f"`{extension}` loaded", ephemeral=True)


@bot.hybrid_command()
@commands.is_owner()
async def unload(ctx: commands.Context, extension: str):
    """Unload extension.(owner only)."""
    await ctx.interaction.response.defer()
    await bot.unload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(f"`{extension}` unloaded", ephemeral=True)


@bot.hybrid_command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension: str):
    """Reload extension.(owner only)."""
    # if new commands are added into cogs, sync the tree
    await ctx.interaction.response.defer()
    await bot.reload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(f"`{extension}` reloaded", ephemeral=True)


# ---------------------------- Running the bot ---------------------------- #

if __name__ == "__main__":
    assert os.environ.get("DISCORD_BOT_TOKEN", None) is not None, dedent(
        """
    DISCORD_BOT_TOKEN not found in env file, please add it in env/bot.env
    if you are first time using this bot, please rename envExample to env and fill in the token
    """
    )
    try:
        bot.run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None)
    finally:
        APIUtils.close_session()
        logger.info("Session closed")
