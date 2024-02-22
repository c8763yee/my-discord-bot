from discord.ext import commands

from cogs import CogsExtension

from .utils import LeetCodeUtils


class LeetCodeCMD(CogsExtension):
    # variables
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = LeetCodeUtils(bot)

    # methods(commands)
    @commands.hybrid_group(ephermal=True)
    async def leetcode(self, ctx: commands.Context):
        pass

    @leetcode.command("user")
    async def user(self, ctx: commands.Context, username: str):
        await ctx.interaction.response.defer()

        # response of leetcode API (ref: queries/profile_page.graphql)
        embed = await self.utils.fetch_leetcode_user_info(username)
        await ctx.interaction.followup.send(embed=embed)
        # self.create_embed(response, thumbnail)

    @leetcode.command("daily")
    async def daily(self, ctx: commands.Context):
        await ctx.interaction.response.defer()

        embed = await self.utils.fetch_leetcode_daily_challenge()
        await ctx.interaction.followup.send(embed=embed)
