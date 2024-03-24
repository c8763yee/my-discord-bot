import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension

from .utils import LeetCodeResponseFormatter, LeetCodeUtils

daily_challenge_time = datetime.time(
    hour=8, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)


class LeetCodeTasks(CogsExtension):
    # variables
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = LeetCodeUtils(bot)
        self.formatter = LeetCodeResponseFormatter(bot)

    async def cog_load(self):
        self.fetch_leetcode_daily_challenge.start()  # pylint: disable=no-member

    async def cog_unload(self):
        self.fetch_leetcode_daily_challenge.stop()  # pylint: disable=no-member

    # methods(tasks)

    @tasks.loop(time=daily_challenge_time)
    async def fetch_leetcode_daily_challenge(self):
        channel = self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None)))
        response = await self.utils.fetch_daily_challenge()
        embed, title = await self.formatter.format_daily_challenge(response)
        owner_id = os.getenv("OWNER_ID", None)
        await channel.send(
            f"<@{owner_id}>\n :tada: **Daily LeetCode Challenge** :tada:  \n{title}",
            embed=embed,
        )
