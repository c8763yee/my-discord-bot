import os

from discord.ext import tasks

from cogs import CogsExtension
from loggers import setup_package_logger

from .utils import RaspberryPiUtils

logger = setup_package_logger(__name__)


class RaspberryPiTasks(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = RaspberryPiUtils(bot)
        self.get_temperature.start()

    @tasks.loop(minutes=5)
    async def get_temperature(self):
        channel = self.bot.get_channel(int(os.environ['TEST_CHANNEL_ID']))
        message = await self.utils.get_temperature()
        await channel.send(message)
