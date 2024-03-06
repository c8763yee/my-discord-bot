import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension
from .utils import KasaUtils

daily_report_time = datetime.time(
    hour=10,
    minute=0,
    second=0,
    tzinfo=datetime.timezone(datetime.timedelta(hours=8)),
)


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

    @tasks.loop(time=daily_report_time)
    async def power_report(self):
        channel = self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None)))
        embeds = [await self.utils.get_power_usage(x) for x in range(6 + 1)]

        await channel.send(f"<@{os.environ['OWNER_ID']}> Daily power usage report", embeds=embeds)
