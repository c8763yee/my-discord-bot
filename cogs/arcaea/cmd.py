from discord import Color
import json
import os

from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
from cogs import CogsExtension
from core.models import Field
from .utils import APIUtils, AssetFetcher
from .const import DIFFICULTY_ABBR, DIFFICULTY_NAMES, DIFFICULTY_COLOR, GRADE_NAMES, GRADE_URL_SUFFIX
if os.path.exists("env/arcaea.env"):
    load_dotenv("env/arcaea.env", override=True)


class ArcaeaCMD(CogsExtension):

    def __init__(self, bot, *args, **kwargs):
        super().__init__(bot, *args, **kwargs)
        self.utils = APIUtils(
            email=os.environ['ARCAEA_EMAIL'], password=os.environ['ARCAEA_PASSWORD'], *args, **kwargs)

    async def cog_load(self):
        await self.utils.login()

    async def cog_unload(self):
        await self.utils.unload()

    @commands.hybrid_group(name="arc", ephermal=True)
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

    @arcaea.command("recent")
    async def recent_score(self, ctx: commands.Context, user_code: str):
        await ctx.interaction.response.defer()
        result = await self.utils.fetch_recent(user_code)

        song_id = result['song_id']
        difficulty = result['difficulty']

        song_cover = await AssetFetcher.fetch_song_cover(song_id, difficulty)
        grade = await self.utils.get_grade(result['score'])

        username = result['username']
        embed = await self.create_embed(
            f"User: {username}\nRecent Play Info",
            f"{result['title']['ja']} [{DIFFICULTY_ABBR[difficulty]}]「{GRADE_NAMES[grade]}」",
            Color.from_str(DIFFICULTY_COLOR[difficulty]),
            None,
            Field(name="Played at", value=datetime.fromtimestamp(
                result['time_played'] // 1000).strftime('%Y-%m-%d %H:%M:%S'), inline=False),
            Field(name="Rating", value=round(
                result['play_rating'], 2), inline=True),
            Field(name="Score", value=result['score'], inline=False),
            Field(name="Grade", value=GRADE_NAMES[grade], inline=True),
            Field(name="Difficulty",
                  value=DIFFICULTY_NAMES[difficulty], inline=True),
            Field(name="Chart Constant",
                  value=round(result['rating'], 1), inline=True),

            thumbnail_url=f'https://moyoez.github.io/ArcaeaResource-ActionUpdater/arcaea/assets/img/grade/{GRADE_URL_SUFFIX[grade]}.png',
            image_url=song_cover
        )
        await ctx.interaction.followup.send(
            f"Recent play info for user **{username}**",
            embed=embed)
