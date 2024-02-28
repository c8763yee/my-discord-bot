from discord.ext import commands

from .cmd import KasaCMD


async def setup(bot: commands.Bot):
    await bot.add_cog(KasaCMD(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("KasaCMD")
