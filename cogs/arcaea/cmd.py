import os
from pathlib import Path

from discord.ext import commands

from cogs import CogsExtension
from core import load_env

from .utils import APIUtils, ArcaeaResponseFormatter

load_env(path=Path.cwd() / "env" / "arcaea.env")


class ArcaeaCMD(CogsExtension):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(bot, *args, **kwargs)
        self.utils = APIUtils(
            email=os.environ["ARCAEA_EMAIL"], password=os.environ["ARCAEA_PASSWORD"]
        )

    async def cog_load(self):
        await self.utils.login()

    async def cog_unload(self):
        await self.utils.unload()

    @commands.hybrid_group(name="arc", ephemeral=True)
    async def arcaea(self, ctx: commands.Context):
        pass

    @arcaea.command("score2step")
    async def score_to_step(
        self, ctx: commands.Context, song_rating: float, char_step: int, score: int
    ):
        rating = await self.utils.score_to_rating(song_rating, score)
        step = await self.utils.rating_to_step(char_step, rating)
        await ctx.send(f"Score: {score} -> Step: {step}")

    @arcaea.command("step2score")
    async def step_to_score(
        self, ctx: commands.Context, song_rating: float, char_step: int, step: int
    ):
        rating = await self.utils.step_to_rating(char_step, step)
        score = await self.utils.rating_to_score(rating, song_rating)
        await ctx.send(f"Step: {step} -> Score: {score}")

    @arcaea.command("recent")
    async def recent_score(self, ctx: commands.Context, user_code: str):
        await ctx.interaction.response.defer()

        result = await self.utils.fetch_recent(user_code)
        embed, username, *files = await ArcaeaResponseFormatter.recent_score(result)

        await ctx.interaction.followup.send(
            f"Recent play info for user **{username}**", embed=embed, files=files
        )
