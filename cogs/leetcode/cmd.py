import os

from discord.ext import commands

from .tasks import LeetCodeTasks


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
        embed = await self.formatter.format_user_info(user_info, username)
        await ctx.interaction.followup.send(embed=embed)

    @leetcode.command("daily")
    async def daily(self, ctx: commands.Context):
        await ctx.interaction.response.defer()
        response = await self.utils.fetch_daily_challenge()
        embed, title = await self.formatter.format_daily_challenge(response)
        owner_id = os.getenv("OWNER_ID", None)
        await ctx.interaction.followup.send(
            (f"<@{owner_id}>\n" ":tada: **Daily LeetCode Challenge** :tada:  \n" f"{title}"),
            embed=embed,
        )
