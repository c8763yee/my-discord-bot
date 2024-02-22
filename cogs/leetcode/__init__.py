from discord.ext import commands
from .cmd import LeetCodeCMD
from .tasks import LeetCodeTasks


async def setup(bot: commands.Bot):
    await bot.add_cog(LeetCodeCMD(bot))
    await bot.add_cog(LeetCodeTasks(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog("LeetCodeCMD")
    await bot.remove_cog("LeetCodeTasks")
