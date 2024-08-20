from discord.ext import commands

from .cmd import SubtitleCMD


async def setup(bot: commands.Bot):
    await bot.add_cog(SubtitleCMD(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("SubtitleCMD")
