import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from textwrap import dedent

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from loggers import setup_package_logger

if os.path.exists('env/bot.env'):
    load_dotenv(dotenv_path='env/bot.env', verbose=True, override=True)


@tasks.loop(minutes=1)
async def update_time():
    now = datetime.now() + timedelta(hours=8)
    await bot.change_presence(activity=discord.CustomActivity(name=f'現在時間： {now.strftime("%Y-%m-%d %H:%M")}', emoji=discord.PartialEmoji(name="🕒"))
                              )


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = setup_package_logger(__name__, file_level=logging.INFO)

    async def on_ready(self):
        import cogs

        for modules in cogs.__all__:
            await self.load_extension(f"cogs.{modules}")

        await update_time.start()
        await self.tree.sync()

        self.logger.info(f"{self.user} is ready.")
        await self.get_channel(int(os.environ["TEST_CHANNEL_ID"])).send(
            f"{self.user} is ready."
        )

    async def on_command_error(self, ctx: commands.Context, error):
        match error:
            case commands.CommandNotFound():
                self.logger.error(
                    f"Command {ctx.message.content} not found.")
                await ctx.send(f"Command {ctx.message.content} not found.")
            case commands.MissingRequiredArgument():
                self.logger.error(f"Missing required argument: {error.param}")
                await ctx.send(f"Missing required argument: {error.param}")
            case _:
                self.logger.exception(
                    f"Ignoring exception in command {ctx.command}:")
                traceback.print_exception(
                    type(error), error, error.__traceback__, file=sys.stderr
                )


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

    await bot.load_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.send(f"`{extension}` loaded")


@bot.hybrid_command()
@commands.is_owner()
async def unload(ctx: commands.Context, extension: str):
    """Unload extension.(owner only)"""
    await bot.unload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.send(f"`{extension}` unloaded")


@bot.hybrid_command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension: str):
    """Reload extension.(owner only)"""
    # if new commands are added into cogs, sync the tree
    await bot.reload_extension(f"cogs.{extension}")
    await bot.tree.sync()
    await ctx.send(f"`{extension}` reloaded")


# ---------------------------- Running the bot ---------------------------- #

if __name__ == "__main__":
    assert os.environ.get("DISCORD_BOT_TOKEN", None) is not None, dedent(
        """
    DISCORD_BOT_TOKEN not found in .env, please add it in env/bot.env
    or if you are first time using this bot, please rename envExample to env and fill in the details.
    """
    )
    bot.run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None)
