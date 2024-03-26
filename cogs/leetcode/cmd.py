from discord.ext import commands

from loggers import setup_package_logger

from .tasks import LeetCodeTasks
from .utils import ResponseFormatter

logger = setup_package_logger(__name__)


class LeetCodeCMD(LeetCodeTasks):
    # methods(commands)
    @commands.hybrid_group(ephermal=True)
    async def leetcode(self, ctx: commands.Context):
        """
        dummy function to create a group command
        """

    @leetcode.command("user")
    async def user(self, ctx: commands.Context, username: str):
        await ctx.interaction.response.defer()
        user_info = await self.utils.fetch_user_info(username)

        embed = await ResponseFormatter.user_info(user_info, username)
        await ctx.interaction.followup.send(embed=embed)

    @leetcode.command("daily_challenge")
    async def daily(self, ctx: commands.Context):
        await ctx.interaction.response.defer()

        response = await self.utils.fetch_daily_challenge()
        embed, title = await ResponseFormatter.daily_challenge(response)
        await ctx.interaction.followup.send(f"Daily LeetCode Challenge: {title}", embed=embed)

    @leetcode.command("contest")
    async def contest(self, ctx: commands.Context, only_today: bool = False):
        await ctx.interaction.response.defer()

        response = await self.utils.fetch_contest()
        is_success, embeds = await ResponseFormatter.contests(response, only_today)

        if is_success is False:
            await ctx.interaction.followup.send("No upcoming contest")
            return

        await ctx.interaction.followup.send("Upcoming LeetCode Contest", embeds=embeds)
