import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension

from .utils import LeetCodeUtils

daily_challenge_time = datetime.time(
    hour=8, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)


class LeetCodeTasks(CogsExtension):
    # variables
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = LeetCodeUtils(bot)

    def cog_load(self):
        self.fetch_leetcode_daily_challenge.start()

    def cog_unload(self):
        self.fetch_leetcode_daily_challenge.cancel()

    # methods(tasks)

    @tasks.loop(time=daily_challenge_time)
    async def fetch_leetcode_daily_challenge(self):
        channel = self.bot.get_channel(int(os.environ["TEST_CHANNEL_ID"]))
        embed = await self.utils.fetch_leetcode_daily_challenge()
        await channel.send(embed=embed)
