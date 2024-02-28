from discord.ext import commands

from .cmd import ChatGPTCMD


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatGPTCMD(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("ChatGPTCMD")
