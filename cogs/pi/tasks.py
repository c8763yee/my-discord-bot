import os
import datetime
from discord.ext import tasks

from cogs import CogsExtension
from loggers import setup_package_logger

from .utils import RaspberryPiUtils

logger = setup_package_logger(__name__)


per_O_clock = datetime.time(minute=0, second=0)


class RaspberryPiTasks(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = RaspberryPiUtils(bot)
        self.get_temperature.start()

    @tasks.loop(time=per_O_clock)
    async def get_temperature(self):
        channel = self.bot.get_channel(int(os.environ["TEST_CHANNEL_ID"]))
        message = await self.utils.get_temperature()
        await channel.send(message)
