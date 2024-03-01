from discord.ext import commands

from loggers import setup_package_logger

from .utils import ArcaeaUtils
from cogs import CogsExtension


class ArcaeaCMD(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = ArcaeaUtils(bot)

    @commands.hybrid_group(ephermal=True)
    async def arcaea(self, ctx: commands.Context):
        pass

    @arcaea.command("score2step")
    async def score_to_step(self, ctx: commands.Context, song_rating: float, char_step: int, score: int):
        rating = await self.utils.score_to_rating(song_rating, score)
        step = await self.utils.rating_to_step(char_step, rating)
        await ctx.send(f"Score: {score} -> Step: {step}")

    @arcaea.command("step2score")
    async def step_to_score(self, ctx: commands.Context, song_rating: float, char_step: int, step: int):
        rating = await self.utils.step_to_rating(char_step, step)
        score = await self.utils.rating_to_score(rating, song_rating)
        await ctx.send(f"Step: {step} -> Score: {score}")
