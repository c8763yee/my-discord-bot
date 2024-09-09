import asyncio
import json
from datetime import datetime
from http import HTTPStatus
from pathlib import Path

import aiohttp
from discord import Color, Embed, File

from core.classes import BaseClassMixin
from core.models import Field
from loggers import setup_package_logger

from .const import (
    BELOW_EX_SCORE_DELTA,
    DIFFICULTY_ABBR,
    DIFFICULTY_COLOR_LIST,
    DIFFICULTY_NAMES,
    EX_RATING_DELTA,
    EX_SCORE_DELTA,
    GRADE_NAMES,
    GRADE_SUFFIX,
    MAX_DIFFICULTY,
    PM_RATING_DELTA,
    GradeEnum,
    GradeScoreEnum,
)
from .schema import Song, SongList

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 "
        "Safari/537.36"
    ),
    "Referer": "https://arcaea.lowiro.com",
    "Set-Cookie": "domain=lowiro.com",
    "Access-Control-Allow-Origin": "https://arcaea.lowiro.com",
}


def is_same_song(song: dict, recent_play: dict) -> bool:
    return song["sid"] == recent_play["song_id"] and song["difficulty"] == recent_play["difficulty"]


class ScoreUtils(BaseClassMixin):
    async def step_to_rating(self, char_step: int, world_step: float) -> float:
        return ((50 / char_step * world_step - 2.5) / 2.45) ** 2

    async def rating_to_step(self, char_step: int, rating: float) -> float:
        r"""# Calculation
        The amount of steps gained after playing a song depends on several factors:.

            - Play Rating
            - Selected Partner's STEP stat
            - Partner skill
            - Mobile only: Boost multipliers (Memory boost, Legacy Play+ Fragment/stamina boosts)

        It can be calculated using:

        {\\displaystyle {\text{Steps Gained}}=
        \\overbrace {\\left(2.45{\\sqrt {\text{Play Rating}}}+2.5\right)} ^{\text{Play Result}}\
        \times {\\dfrac {\text{STEP Stat}}{50}}+{\text{Partner Step Bonuses}}\\,.}
        """
        return char_step / 50 * (2.5 + 2.45 * rating**0.5)

    async def rating_to_score(self, user_rating: float, song_rating: float) -> int:
        diff_rating = user_rating - song_rating

        if diff_rating == PM_RATING_DELTA:
            return GradeScoreEnum.PM

        if diff_rating < EX_RATING_DELTA:
            return max(int(GradeScoreEnum.BELOW_EX + (diff_rating) * BELOW_EX_SCORE_DELTA), 0)

        return int(GradeScoreEnum.EX + (diff_rating - EX_RATING_DELTA) * EX_SCORE_DELTA)

    async def score_to_rating(self, chart_rating: float, score: int) -> float:
        if score >= GradeScoreEnum.PM:
            return chart_rating + PM_RATING_DELTA

        if score < GradeScoreEnum.EX:
            return max(chart_rating + (score - GradeScoreEnum.BELOW_EX) / BELOW_EX_SCORE_DELTA, 0)

        return chart_rating + EX_RATING_DELTA + (score - GradeScoreEnum.EX) / EX_SCORE_DELTA

    @staticmethod
    async def get_grade(score: int) -> int:
        """Get grade from score
        EX+: 9900000
        EX: 9800000
        AA: 9500000
        A: 9200000
        B: 8900000
        C: 8600000.
        """
        grades = [
            (GradeScoreEnum.EX_PLUS, GradeEnum.EX_PLUS),
            (GradeScoreEnum.EX, GradeEnum.EX),
            (GradeScoreEnum.BELOW_EX, GradeEnum.AA),
            (GradeScoreEnum.A, GradeEnum.A),
            (GradeScoreEnum.B, GradeEnum.B),
            (GradeScoreEnum.C, GradeEnum.C),
        ]
        for threshold, grade in grades:
            if score >= threshold:
                return grade

        return 0


class APIUtils(ScoreUtils):
    base_url = "https://webapi.lowiro.com"
    _session: aiohttp.ClientSession = None
    _loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    _songlist: list = []

    def __init__(self, email: str, password: str):
        self.email: str = email
        self.password: str = password
        self.is_logged_in: bool = False
        self.friend_ids: set = set()

    async def _unload(self):
        await self.__class__._session.close()
        self.is_logged_in = False
        self.__class__._songlist = []
        self.__class__._session = None

    async def unload(self) -> None:
        await self._unload()

    async def login(self) -> None:
        if self.is_logged_in is True:
            return

        if self._session is None or self._session.closed:
            await self.open_session()

        async with self._session.post(
            f"{self.base_url}/auth/login",
            data={"email": self.email, "password": self.password},
            headers=headers,
        ) as request:
            response = await request.json()
            self.is_logged_in = response.get("isLoggedIn")
            if not self.__class__._songlist:
                self.__class__._songlist = await self.get_slst()

    async def fetch_play_info(self, song: dict, user_id: int) -> dict:
        sid = song["sid"]
        difficulty = song["difficulty"]

        songs_url = (
            f"{self.base_url}"
            "/webapi/score/song/friend"
            f"?song_id={sid}&difficulty={difficulty}&start=0&limit=30"
        )
        async with self._session.get(songs_url, headers=headers) as response:
            result = await response.json()
            if result["success"] is False:
                return result

        for value in result["value"]:
            if value["user_id"] == user_id:
                value.update(song)
                return value

        return result

    async def fetch_recent_play_info(self, user_id: int) -> dict:
        async with self._session.get(
            self.base_url + "/webapi/user/me", headers=headers
        ) as response:
            result = await response.json()

            if result["success"] is False:
                return result

        for friend in result["value"]["friends"]:
            if friend["user_id"] == user_id:
                return friend["recent_score"][0]

        return result

    async def add_friend(self, user_code: str) -> dict:
        async with self._session.post(
            self.base_url + "/webapi/friend/me/add",
            headers={
                "Content-Type": "multipart/form-data; boundary=boundary",
                **headers,
            },
            data=(
                "--boundary\r\n"
                f'Content-Disposition: form-data;name="friend_code"\r\n\r\n{user_code}\r\n'
                "--boundary--\r\n"
            ),
        ) as response:
            friend_data = await response.json()

        return friend_data

    async def del_friend(self, user_id: int) -> dict:
        async with self._session.post(
            self.base_url + "/webapi/friend/me/delete",
            headers={
                "Content-Type": "multipart/form-data; boundary=boundary",
                **headers,
            },
            data=(
                "--boundary\r\n"
                f'Content-Disposition: form-data; name="friend_id"\r\n\r\n{user_id}\r\n'
                "--boundary--\r\n"
            ),
        ) as response:
            friend_data = await response.json()
        return friend_data

    async def update_friend_list(self) -> None:
        async with self._session.get(
            self.base_url + "/webapi/user/me", headers=headers
        ) as response:
            resp = await response.json()
            self.friend_ids = {friends["user_id"] for friends in resp["value"]["friends"]}

    async def get_slst(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.chinosk6.cn/arcscore/get_slst") as response:
                songlist_response = await response.json()
        return songlist_response

    async def open_session(self) -> None:
        self.__class__._session = aiohttp.ClientSession()

    @classmethod
    def close_session(cls) -> None:
        if cls._session and not cls._session.closed:
            cls._loop.run_until_complete(cls._loop.create_task(cls._session.close()))

    async def get_user_id(self, user_code: str) -> tuple[int, str]:
        if self._session is None or self._session.closed:
            await self.open_session()

        if not self.is_logged_in:
            await self.login()

            if self.is_logged_in is False:
                raise ValueError("Login failed!")

        await self.update_friend_list()

        # delete all friends before querying user
        for user_id in self.friend_ids:
            await self.del_friend(user_id)

        resp = await self.add_friend(user_code)
        if resp.get("success"):
            user_id = resp["value"]["friends"][0]["user_id"]
            username = resp["value"]["friends"][0]["name"]
            return user_id, username

        if resp.get("error_code", HTTPStatus.UNAUTHORIZED) == HTTPStatus.UNAUTHORIZED:
            raise ValueError("User not found!")

        raise ValueError(f"Unknown error!,{resp}")

    async def fetch_all(self, user_code: str) -> tuple[dict, str]:
        user_id, user_name = await self.get_user_id(user_code)

        tasks = [await self.fetch_play_info(song, user_id) for song in self._songlist]
        result = {}
        for play_data in tasks:
            if not play_data or play_data.get("success", False) is False:
                continue
            if play_data["sid"] not in result:
                result[play_data["sid"]] = {}

            play_rating = await self.score_to_rating(
                play_data.get("rating", 0) / 10, play_data.get("score", 0)
            )

            result[play_data["sid"]][play_data["difficulty"]] = {
                "score": play_data.get("score", "N/A"),
                "play_rating": play_rating,
                "best_clear_type": play_data.get("best_clear_type", "N/A"),
                "shiny_perfect_count": play_data.get("shiny_perfect_count", "N/A"),
                "perfect_count": play_data.get("perfect_count", "N/A"),
                "near_count": play_data.get("near_count", "N/A"),
                "miss_count": play_data.get("miss_count", "N/A"),
                "rating": play_data.get("rating", "N/A"),
                "time_played": play_data.get("time_played", "N/A"),
            }

        return result, user_name

    async def fetch_recent(self, target_user_code: str) -> dict:
        target_user_id, username = await self.get_user_id(target_user_code)
        recent_play = await self.fetch_recent_play_info(target_user_id)
        this_song = next(filter(lambda song: is_same_song(song, recent_play), self._songlist), None)

        if this_song:
            recent_play["rating"] = this_song["rating"] / 10 if this_song["rating"] != -1 else 0

        recent_play["play_rating"] = await self.score_to_rating(
            recent_play.get("rating", 0), recent_play.get("score", 0)
        )

        recent_play["username"] = username
        return recent_play


class AssetFetcher:
    ROOT_PATH = Path("/opt/arcaea/assets")
    with (ROOT_PATH / "songs" / "songlist").open(encoding="utf-8") as file:
        songlist = SongList.model_validate(json.load(file))

    songlist_map = {song.id: song for song in songlist.songs}

    @classmethod
    async def get_thumbnail(cls, grade: int) -> File:
        thumbnail_path = cls.ROOT_PATH / "img" / "grade" / f"{GRADE_SUFFIX[grade]}.png"
        if thumbnail_path.exists() is False:
            cls.logger.error("Thumbnail not found: %s", thumbnail_path)
            raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")
        return File(thumbnail_path)

    @classmethod
    async def get_song_cover(cls, song_id: int, difficulty: int) -> File:
        song_data: Song = cls.songlist_map[song_id]
        song_name = f"dl_{song_id}" if song_data.remote_dl is True else song_id

        difficulty_name = (
            str(difficulty)
            if song_data.difficulties[min(difficulty, MAX_DIFFICULTY - 1)].jacketOverride is True
            # minus 1 because BEYOND and ETERNAL can not be at the same time
            else "base"
        )

        for prefix in ["1080_", ""]:
            song_cover_path = cls.ROOT_PATH / "songs" / song_name / f"{prefix}{difficulty_name}.jpg"
            cls.logger.debug("Trying to fetch: %s", song_cover_path)

            if song_cover_path.exists():
                return File(song_cover_path)

        # return base cover if no cover found
        song_cover_path = cls.ROOT_PATH / "songs" / song_name / "base.jpg"
        if song_cover_path.exists() is False:
            raise FileNotFoundError(f"Thumbnail not found: {song_cover_path}")

        return File(song_cover_path)


class ArcaeaResponseFormatter:
    @staticmethod
    async def recent_score(result: dict) -> tuple[Embed, str, File, File]:
        song_id = result["song_id"]
        difficulty = result["difficulty"]

        song_cover = await AssetFetcher.get_song_cover(song_id, difficulty)
        grade = await ScoreUtils.get_grade(result["score"])
        thumbnail: File = await AssetFetcher.get_thumbnail(grade)

        rating_val = round(result["play_rating"], 2)
        rating = str(rating_val) if rating_val > 0 else "Too low to calculate"

        username = result["username"]
        embed = await BaseClassMixin.create_embed(
            f"User: {username}\nRecent Play Info",
            f"{result['title']['ja']} [{DIFFICULTY_ABBR[difficulty]}]「{GRADE_NAMES[grade]}」",
            Field(
                name="Played at",
                value=datetime.fromtimestamp(result["time_played"] // 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                inline=False,
            ),
            Field(name="Rating", value=rating, inline=True),
            Field(name="Score", value=result["score"], inline=False),
            Field(name="Grade", value=GRADE_NAMES[grade], inline=True),
            Field(name="Difficulty", value=DIFFICULTY_NAMES[difficulty], inline=True),
            Field(name="Chart Constant", value=round(result.get("rating", 0), 1), inline=True),
            color=Color.from_str(DIFFICULTY_COLOR_LIST[difficulty]),
            image_url=f"attachment://{song_cover.filename}",
            thumbnail_url=f"attachment://{thumbnail.filename}",
        )
        return embed, username, thumbnail, song_cover


AssetFetcher.logger = setup_package_logger(f"{AssetFetcher.__module__}.AssetFetcher")
