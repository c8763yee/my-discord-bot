import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension

from .const import PlugID
from .utils import KasaUtils

daily_report_time = datetime.time(
    hour=12,
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
        watts = {}
        for plug_id in PlugID:
            daily_kwh = await self.utils.get_daily_power_usage(plug_id)
            watts[plug_id] = daily_kwh
        await channel.send(
            "Daily power usage report for all plugs\n```\n"
            + "\n".join([f"Plug {plug_id}: {kwh} kWh" for plug_id, kwh in watts.items()])
            + "\n```"
        )
