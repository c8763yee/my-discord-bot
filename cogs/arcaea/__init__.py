from discord.ext import commands

from .cmd import ArcaeaCMD


async def setup(bot: commands.Bot):
    await bot.add_cog(ArcaeaCMD(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("ArcaeaCMD")
