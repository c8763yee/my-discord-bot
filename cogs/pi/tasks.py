import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension
from loggers import setup_package_logger

from .utils import RaspberryPiUtils, StatsFormatter

logger = setup_package_logger(__name__)

per_clock = [
    datetime.time(
        hour=hour,
        minute=0,
        second=0,
        tzinfo=datetime.timezone(datetime.timedelta(hours=8)),
    )
    for hour in range(6, 24)
]


class RaspberryPiTasks(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = RaspberryPiUtils(bot)
        self.formatter = StatsFormatter(bot)

    async def cog_load(self):
        self.get_stats.start()

    async def cog_unload(self):
        self.get_stats.stop()

    @tasks.loop(time=per_clock)
    async def get_stats(self):
        channel = self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None)))
        message = await self.utils.get_stats()
        embed = await self.formatter.format_stats(message)
        await channel.send(f'[Raspberry Pi Stats] {message["now"]}', embed=embed, silent=True)
