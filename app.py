import logging
import logging.handlers
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands


class Bot(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        await ctx.send(error)


bot = Bot(command_prefix='!')


def setup_logger():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(
        '[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == '__main__':
    load_dotenv()
    setup_logger()
    assert os.getenv(
        'DISCORD_TOKEN') is not None, 'DISCORD_TOKEN not found in .env'
    bot.run(os.getenv('DISCORD_TOKEN'))
