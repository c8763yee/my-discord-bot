import datetime

from discord.ext import tasks

from cogs import CogsExtension

from .utils import LeetCodeResponseFormatter, LeetCodeUtils

# variables
daily_challenge_time = datetime.time(
    hour=8, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)
biweekly_contest_start_time = datetime.time(
    hour=22, minute=30, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)
biweekly_contest_end_time = datetime.time(
    hour=23, minute=45, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)
weekly_contest_start_time = datetime.time(
    hour=10, minute=30, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)
weekly_contest_end_time = datetime.time(
    hour=11, minute=45, second=14, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)


class LeetCodeTasks(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = LeetCodeUtils(bot)
        self.formatter = LeetCodeResponseFormatter(bot)

    async def cog_load(self):
        self.fetch_leetcode_daily_challenge.start()
        self.fetch_leetcode_contest.start()
        self.biweekly_contest_start_reminder.start()
        self.biweekly_contest_end_reminder.start()
        self.weekly_contest_start_reminder.start()
        self.weekly_contest_end_reminder.start()

    async def cog_unload(self):
        self.fetch_leetcode_daily_challenge.stop()
        self.fetch_leetcode_contest.stop()
        self.biweekly_contest_start_reminder.stop()
        self.biweekly_contest_end_reminder.stop()
        self.weekly_contest_start_reminder.stop()
        self.weekly_contest_end_reminder.stop()

    # methods(tasks)

    @tasks.loop(time=daily_challenge_time)
    async def fetch_leetcode_daily_challenge(self):
        response = await self.utils.fetch_leetcode_daily_challenge()
        embed, title = await self.formatter.daily_challenge(response)
        for channel in self.bot.get_all_channels():
            await channel.send(
                f"@here\n :tada: **Daily LeetCode Challenge** :tada:  \n{title}", embed=embed
            )

    @tasks.loop(time=daily_challenge_time)
    async def fetch_leetcode_contest(self):
        response = await self.utils.fetch_leetcode_contest()
        is_success, embeds = await self.formatter.contests(response, only_today=True)
        if is_success is False:
            return

        for channel in self.bot.get_all_channels():
            await channel.send(
                "@here\n :tada: **Upcoming LeetCode Contest** :tada:  \n", embeds=embeds
            )

    @tasks.loop(time=biweekly_contest_start_time)
    async def biweekly_contest_start_reminder(self):
        response = await self.utils.fetch_leetcode_contest()
        target_contest = None
        for contest in response:
            if contest["title"].startswith("Biweekly Contest"):
                target_contest = contest
                break
        if target_contest is None or self.formatter.today_is_contest(target_contest) is False:
            return

        for channel in self.bot.get_all_channels():
            await channel.send(
                "@here\n"
                ":tada:"
                "**This week of the Biweekly LeetCode Contest is started!**"
                ":tada:\n"
            )

    @tasks.loop(time=biweekly_contest_end_time)
    async def biweekly_contest_end_reminder(self):
        response = await self.utils.fetch_leetcode_contest()
        target_contest = None
        for contest in response:
            if contest["title"].startswith("Biweekly Contest"):
                target_contest = contest
                break
        if target_contest is None or self.formatter.today_is_contest(target_contest) is False:
            return

        for channel in self.bot.get_all_channels():
            await channel.send(
                "@here\n"
                ":tada:"
                "**This week of the Biweekly LeetCode Contest will end in 15 minutes!**"
                ":tada:\n"
            )

    @tasks.loop(time=weekly_contest_start_time)
    async def weekly_contest_start_reminder(self):
        response = await self.utils.fetch_leetcode_contest()
        target_contest = None
        for contest in response:
            if contest["title"].startswith("Weekly Contest"):
                target_contest = contest
                break
        if target_contest is None or await self.formatter.today_is_contest(target_contest) is False:
            return

        for channel in self.bot.get_all_channels():
            await channel.send(
                "@here\n :tada: **This week of the weekly LeetCode Contest is started!** :tada:  \n"
            )

    @tasks.loop(time=weekly_contest_end_time)
    async def weekly_contest_end_reminder(self):
        response = await self.utils.fetch_leetcode_contest()
        target_contest = None
        for contest in response:
            if contest["title"].startswith("Weekly Contest"):
                target_contest = contest
                break
        if target_contest is None or await self.formatter.today_is_contest(target_contest) is False:
            return

        for channel in self.bot.get_all_channels():
            await channel.send(
                "@here\n"
                ":tada:"
                "**This week of the weekly LeetCode Contest will end in 15 minutes!**"
                ":tada:  \n"
            )
