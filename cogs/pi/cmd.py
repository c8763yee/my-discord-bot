import os

from discord.ext import commands

from .tasks import RaspberryPiTasks
from .utils import RaspberryPiUtils, StatsFormatter, TemperatureTooHighError


class RaspberryPiCMD(RaspberryPiTasks):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = RaspberryPiUtils()

    @commands.hybrid_group(ephemeral=True)
    async def pi(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @pi.command("reboot")
    async def reboot(self, ctx: commands.Context):
        await ctx.send("Rebooting")
        os.system("sudo reboot")

    @pi.command("temp")
    async def temperature(self, ctx: commands.Context):
        try:
            message = await self.utils.get_temperature()
        except TemperatureTooHighError:
            ctx.send("Temperature too high, rebooting")
            os.system("sudo reboot")

        await ctx.send(message)

    @pi.command("stats")
    async def stats(self, ctx: commands.Context):
        try:
            message = await self.utils.get_stats()
        except TemperatureTooHighError:
            ctx.send("Temperature too high, rebooting")
            os.system("sudo reboot")

        embed = await StatsFormatter.format_stats(message)
        await ctx.send(f'[Raspberry Pi Stats] {message["now"]}', embed=embed)
