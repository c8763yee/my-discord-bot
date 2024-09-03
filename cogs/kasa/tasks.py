import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension

from .const import PlugID
from .utils import KasaResponseFormatter, KasaUtils

daily_report_time = datetime.time(
    hour=10,
    minute=0,
    second=0,
    tzinfo=datetime.timezone(datetime.timedelta(hours=8)),
)


class KasaTasks(CogsExtension):
    # variables
    def __init__(self, bot, *args, **kwargs):
        super().__init__(bot, *args, **kwargs)
        self.utils = KasaUtils()

    async def cog_load(self):
        self.power_report.start()

    async def cog_unload(self):
        self.power_report.stop()

    @tasks.loop(time=daily_report_time)
    async def power_report(self):
        channel = self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None)))
        for plug_id in PlugID:
            payload = await self.utils.get_daily_power_usage(plug_id)
            embed = await KasaResponseFormatter.format_power_usage(payload)
            await channel.send(f"<@{os.environ['OWNER_ID']}> Daily power usage report", embed=embed)
