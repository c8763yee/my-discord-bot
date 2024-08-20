import datetime

import discord
from discord.ext import tasks

from cogs import CogsExtension

from .schema import UpcomingContest
from .utils import LeetCodeUtils, ResponseFormatter

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

contest_remind_time = datetime.time(
    hour=10, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=8))
)


class LeetCodeTasks(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = LeetCodeUtils(bot)

    async def cog_load(self):
        self.fetch_daily_challenge.start()
        self.fetch_contest.start()
        self.biweekly_contest_start_reminder.start()
        self.biweekly_contest_end_reminder.start()
        self.weekly_contest_start_reminder.start()
        self.weekly_contest_end_reminder.start()

    async def cog_unload(self):
        self.fetch_daily_challenge.stop()
        self.fetch_contest.stop()
        self.biweekly_contest_start_reminder.stop()
        self.biweekly_contest_end_reminder.stop()
        self.weekly_contest_start_reminder.stop()
        self.weekly_contest_end_reminder.stop()

    # methods(tasks)

    @tasks.loop(time=daily_challenge_time)
    async def fetch_daily_challenge(self):
        response = await self.utils.fetch_daily_challenge()
        embed, title = await ResponseFormatter.daily_challenge(response)
        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel) is False:
                continue
            try:
                await channel.send(
                    f"@here\n :tada: **Daily LeetCode Challenge** :tada:  \n{title}", embed=embed
                )
            except discord.errors.Forbidden as forbidden:
                self.logger.error(
                    "PiBot has no permission to send message in this channel %s", forbidden
                )

    @tasks.loop(time=contest_remind_time)
    async def fetch_contest(self):
        contests: list[UpcomingContest] = await self.utils.fetch_contest()
        is_success, embeds = await ResponseFormatter.parse_contests(contests, only_today=True)
        if is_success is False or len(embeds) == 0:
            return

        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel) is False:
                continue
            try:
                await channel.send(
                    "@here\n :tada: **Upcoming LeetCode Contest** :tada:  \n", embeds=embeds
                )
            except discord.errors.Forbidden as forbidden:
                self.logger.error(
                    "PiBot has no permission to send message in this channel %s", forbidden
                )

    @tasks.loop(time=biweekly_contest_start_time)
    async def biweekly_contest_start_reminder(self):
        contests: list[UpcomingContest] = await self.utils.fetch_contest()
        target_contest: UpcomingContest | None = None
        for contest in contests:
            if contest.title.startswith("Biweekly Contest"):
                target_contest = contest
                break

        is_success, embed = await ResponseFormatter.parse_contest(target_contest, only_today=True)
        if target_contest is None or is_success is False or embed is None:
            self.logger.info("No biweekly contest today")
            return

        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel) is False:
                continue
            try:
                await channel.send(
                    "@here\n"
                    ":tada:"
                    "**This week of the Biweekly LeetCode Contest is started!**"
                    ":tada:\n",
                    embed=embed,
                )
            except discord.errors.Forbidden as forbidden:
                self.logger.error(
                    "PiBot has no permission to send message in this channel %s", forbidden
                )

    @tasks.loop(time=biweekly_contest_end_time)
    async def biweekly_contest_end_reminder(self):
        contests: list[UpcomingContest] = await self.utils.fetch_contest()
        target_contest: UpcomingContest = None
        for contest in contests:
            if contest.title.startswith("Biweekly Contest"):
                target_contest = contest
                break

        is_success, embed = await ResponseFormatter.parse_contest(target_contest, only_today=True)
        if target_contest is None or is_success is False or embed is None:
            self.logger.info("No biweekly contest today")
            return

        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel) is False:
                continue
            try:
                await channel.send(
                    "@here\n"
                    ":tada:"
                    "**This week of the Biweekly LeetCode Contest will end in 15 minutes!**"
                    ":tada:\n",
                    embed=embed,
                )
            except discord.errors.Forbidden as forbidden:
                self.logger.error(
                    "PiBot has no permission to send message in this channel %s", forbidden
                )

    @tasks.loop(time=weekly_contest_start_time)
    async def weekly_contest_start_reminder(self):
        contests: list[UpcomingContest] = await self.utils.fetch_contest()
        target_contest: UpcomingContest = None
        for contest in contests:
            if contest.title.startswith("Weekly Contest"):
                target_contest = contest
                break

        is_success, embed = await ResponseFormatter.parse_contest(target_contest, only_today=True)
        if target_contest is None or is_success is False or embed is None:
            self.logger.info("No weekly contest today")
            return

    @tasks.loop(time=weekly_contest_end_time)
    async def weekly_contest_end_reminder(self):
        contests: list[UpcomingContest] = await self.utils.fetch_contest()
        target_contest: UpcomingContest = None
        for contest in contests:
            if contest.title.startswith("Weekly Contest"):
                target_contest = contest
                break

        is_success, embed = await ResponseFormatter.parse_contest(target_contest, only_today=True)
        if target_contest is None or is_success is False or embed is None:
            self.logger.info("No weekly contest today")
            return

        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel) is False:
                continue
            try:
                await channel.send(
                    "@here\n"
                    ":tada:"
                    "**This week of the Weekly LeetCode Contest will end in 15 minutes!**"
                    ":tada:\n",
                    embed=embed,
                )
            except discord.errors.Forbidden as forbidden:
                self.logger.error(
                    "PiBot has no permission to send message in this channel %s", forbidden
                )
