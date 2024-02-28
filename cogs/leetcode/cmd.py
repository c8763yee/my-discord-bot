from discord.ext import commands

from .tasks import LeetCodeTasks


class LeetCodeCMD(LeetCodeTasks):
    # methods(commands)
    @commands.hybrid_group(ephermal=True)
    async def leetcode(self, ctx: commands.Context):
        pass

    @leetcode.command("user")
    async def user(self, ctx: commands.Context, username: str):
        await ctx.interaction.response.defer()
        embed = await self.utils.fetch_leetcode_user_info(username)
        await ctx.interaction.followup.send(embed=embed)

    @leetcode.command("daily")
    async def daily(self, ctx: commands.Context):
        await ctx.interaction.response.defer()

        embed = await self.utils.fetch_leetcode_daily_challenge()
        await ctx.interaction.followup.send(embed=embed)
