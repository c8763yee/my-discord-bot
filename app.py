import logging
import os
import sys
import traceback
from datetime import datetime
from textwrap import dedent

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from cogs import CogsExtension
from cogs.arcaea.utils import APIUtils
from core.models import Field
from loggers import setup_package_logger, TZ

if os.path.exists('env/bot.env'):
    load_dotenv(dotenv_path='env/bot.env', verbose=True, override=True)
os.umask(0o000)
logger = setup_package_logger('main', file_level=logging.INFO)


@tasks.loop(minutes=1)
async def update_time():
    now = datetime.now(tz=TZ)
    await bot.change_presence(
        activity=discord.CustomActivity(
            name=f'現在時間： {now.strftime("%Y-%m-%d %H:%M")}',
            emoji=discord.PartialEmoji(name="🕒")
        )
    )


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger: logging.Logger = setup_package_logger(
            __name__, file_level=logging.INFO)

    async def on_ready(self):
        import cogs
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

    async def on_command_error(self, ctx: commands.Context, error):
        """
        response embed with error message
        1. line number and character position
        2. error message
        3. error type
        4. traceback
        """
        exc_info = sys.exc_info()
        if exc_info and exc_info[-1]:
            traceback_info = traceback.extract_tb(exc_info[-1])[-1]
            error_line = traceback_info.lineno
            error_char = traceback_info.col_offset
        else:
            error_line = "N/A"
            error_char = "N/A"

        error_type = error.__class__.__name__
        error_message = str(error)
        self.logger.exception(error)
        await ctx.send(
            embed=await CogsExtension.create_embed(
                "Error occurred",
                f"\n{error_type}",
                discord.Color.red(),
                None,
                Field(
                    name="Error info",
                    value=dedent(f"""
                        Error Type: `{error_type}`
                        """), inline=False)),
            file=discord.File(fp=error_file, filename="error.txt"))


# ---------------------------- Initialising the bot ---------------------------- #
bot = Bot(
    command_prefix=commands.when_mentioned_or("!", "?", "hey siri, "),
    intents=discord.Intents.all(),
    help_command=commands.DefaultHelpCommand(dm_help=True),
    description="A bot for my Discord server.",
)
logging.getLogger("discord.http").setLevel(logging.INFO)


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
    DISCORD_BOT_TOKEN not found in .env, please add it in env/bot.env
    or if you are first time using this bot, please rename envExample to env and fill in the details.
    """
    )
    try:
        bot.run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None)
    finally:
        APIUtils.close_session()
        logger.info("Session closed")
