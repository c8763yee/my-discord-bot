import os

from discord.ext import commands

from loggers import setup_package_logger

from .tasks import RaspberryPiTasks
from .utils import RaspberryPiUtils, StatsFormatter

logger = setup_package_logger(__name__)


class RaspberryPiCMD(RaspberryPiTasks):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = RaspberryPiUtils(bot)

    @commands.hybrid_group(ephermal=True)
    async def pi(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @pi.command("reboot")
    async def reboot(self, ctx: commands.Context):
        await ctx.send("Rebooting")
        os.system("sudo reboot")

    @pi.command("temp")
    async def temperature(self, ctx: commands.Context):
        message = await self.utils.get_temperature()
        await ctx.send(message)

    @pi.command("stats")
    async def stats(self, ctx: commands.Context):
        message = await self.utils.get_stats()
        embed = await StatsFormatter.format_stats(message)
        await ctx.send(f'[Raspberry Pi Stats] {message["now"]}', embed=embed)
