import datetime
import os

from discord.ext import tasks, commands

from cogs import CogsExtension
from .utils import KasaUtils

per_clock = [datetime.time(hour=h, minute=0, second=0) for h in range(6, 24)]


class KasaTasks(CogsExtension):
    # variables
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = KasaUtils(bot)

    def cog_load(self):
        self.power_report.start()

    def cog_unload(self):
        self.power_report.stop()

    # methods(tasks)

    @tasks.loop(time=per_clock)
    async def power_report(self):
        channel = self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None)))
        # mention bot owner
        await channel.send(f"<@{os.environ['OWNER_ID']}> Power usage report")
        embeds = [await self.utils.get_power_usage(x) for x in range(6+1)]

        await channel.send(embeds=embeds)
