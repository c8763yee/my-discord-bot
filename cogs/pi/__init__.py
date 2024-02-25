from discord.ext import commands
from .cmd import RaspberryPiCMD
from .tasks import RaspberryPiTasks


async def setup(bot: commands.Bot):
    await bot.add_cog(RaspberryPiCMD(bot))
    await bot.add_cog(RaspberryPiTasks(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("RaspberryPiCMD")
    await bot.remove_cog("RaspberryPiTasks")
