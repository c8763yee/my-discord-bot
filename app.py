import logging
import os
from datetime import datetime
from textwrap import dedent

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

import cogs
from cogs.arcaea.utils import APIUtils
from loggers import TZ, setup_package_logger

if os.path.exists("env/bot.env"):
    load_dotenv(dotenv_path="env/bot.env", verbose=True, override=True)

logger = setup_package_logger("main", file_level=logging.INFO)
setup_package_logger("discord", file_level=logging.INFO, console_level=logging.DEBUG)
logging.getLogger("discord.http").setLevel(logging.INFO)


@tasks.loop(minutes=1)
async def update_time():
    now = datetime.now(tz=TZ)
    await bot.change_presence(
        activity=discord.CustomActivity(
            name=f'現在時間： {now.strftime("%Y-%m-%d %H:%M")}',
            emoji=discord.PartialEmoji(name="🕒"),
        )
    )


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger: logging.Logger = setup_package_logger(__name__, file_level=logging.INFO)

    async def on_ready(self):
        channel = self.get_channel(int(os.environ["TEST_CHANNEL_ID"]))

        for modules in cogs.__all__:
            await self.load_extension(f"cogs.{modules}")
            await channel.send(f"`{modules}` loaded", silent=True)

        update_time.start()
        await self.tree.sync()
        # mention owner when ready
        await channel.send(
            f"{self.user} is ready. <@{os.environ['OWNER_ID']}>",
            silent=True,
        )


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
    """Load extension.(owner only)"""

    await ctx.interaction.response.defer()
    await bot.load_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(f"`{extension}` loaded", ephemeral=True)


@bot.hybrid_command()
@commands.is_owner()
async def unload(ctx: commands.Context, extension: str):
    """Unload extension.(owner only)"""
    await ctx.interaction.response.defer()
    await bot.unload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.interaction.followup.send(f"`{extension}` unloaded", ephemeral=True)


@bot.hybrid_command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension: str):
    """Reload extension.(owner only)"""
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
