import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension

from .utils import RaspberryPiUtils, StatsFormatter, TemperatureTooHighError

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
        self.utils = RaspberryPiUtils()

    async def cog_load(self):
        self.get_stats.start()

    async def cog_unload(self):
        self.get_stats.stop()

    @tasks.loop(time=per_clock)
    async def get_stats(self):
        channel = self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None)))
        try:
            message = await self.utils.get_stats()
        except TemperatureTooHighError:
            await channel.send("Temperature too high, rebooting")
            os.system("sudo reboot")

        embed = await StatsFormatter.format_stats(message)
        await channel.send(f'[Raspberry Pi Stats] {message["now"]}', embed=embed, silent=True)
