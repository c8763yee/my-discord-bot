from discord.ext import commands

from .cmd import RaspberryPiCMD


async def setup(bot: commands.Bot):
    await bot.add_cog(RaspberryPiCMD(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("RaspberryPiCMD")
