import asyncio
import json
from pathlib import Path

import aiohttp
from requests import get
from .const import (BELOW_EX_SCORE, BELOW_EX_SCORE_DELTA, EX_RATING_DELTA,
                    EX_SCORE, EX_SCORE_DELTA, PM_RATING_DELTA, PM_SCORE)

from loggers import setup_package_logger
logger = setup_package_logger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 "
    "Safari/537.36",
    "Referer": "https://arcaea.lowiro.com",
    "Set-Cookie": "domain=lowiro.com",
    "Access-Control-Allow-Origin": "https://arcaea.lowiro.com"
}


def is_same_song(song: dict, recent_play: dict) -> bool:
    return song['sid'] == recent_play['song_id'] and song['difficulty'] == recent_play['difficulty']


class ScoreUtils:
    async def step_to_rating(self, char_step: int, world_step: float) -> float:
        return ((50 / char_step * world_step - 2.5) / 2.45) ** 2

    async def rating_to_step(self, char_step: int, rating: float) -> float:
        return char_step / 50 * (2.5 + 2.45 * rating ** 0.5)

    async def rating_to_score(self, user_rating: float, song_rating: float) -> int:
        diff_rating = user_rating - song_rating

        if diff_rating == PM_RATING_DELTA:
            return PM_SCORE

        elif diff_rating < EX_RATING_DELTA:
            return max(int(BELOW_EX_SCORE + (diff_rating) * BELOW_EX_SCORE_DELTA), 0)

        return int(EX_SCORE + (diff_rating - EX_RATING_DELTA) * EX_SCORE_DELTA)

    async def score_to_rating(self, chart_rating: float, score: int) -> float:
        if score >= PM_SCORE:
            return chart_rating + PM_RATING_DELTA

        if score < EX_SCORE:
            return max(chart_rating + (score - BELOW_EX_SCORE) / BELOW_EX_SCORE_DELTA, 0)

        return chart_rating + EX_RATING_DELTA + (score - EX_SCORE) / EX_SCORE_DELTA

    async def get_grade(self, score: int) -> int:
        """
        Get grade from score
        EX+: 9900000
        EX: 9800000
        AA: 9500000
        A: 9200000
        B: 8900000
        C: 8600000
        """
        if score >= 9900000:
            return 6
        if score >= 9800000:
            return 5
        if score >= 9500000:
            return 4
        if score >= 9200000:
            return 3
        if score >= 8900000:
            return 2
        if score >= 8600000:
            return 1
        return 0


class APIUtils(ScoreUtils):

    base_url = 'https://webapi.lowiro.com'
    _session = None
    _loop = asyncio.get_event_loop()
    _songlist: list = []

    def __init__(self, email: str, password: str, *args, **kwargs):
        self.email = email
        self.password = password
        self.is_logged_in = False
        self.friend_ids = set()

    async def unload(self) -> None:
        await self.__class__._session.close()
        self.is_logged_in = False
        self.__class__._songlist = []
        self.__class__._session = None

    async def login(self) -> None:
        if getattr(self, 'is_logged_in', False) is True:
            return

        if self._session is None or self._session.closed:
            await self.open_session()

        async with self._session.post(f'{self.base_url}/auth/login',
                                      data={'email': self.email,
                                            'password': self.password},
                                      headers=headers) as request:

            response = await request.json()
            self.is_logged_in = response.get('isLoggedIn')
            if self.__class__._songlist == []:
                self.__class__._songlist = await self.get_slst()

    async def fetch_play_info(self, song: dict, user_id: int) -> dict:
        songs_url = f'{self.base_url}/webapi/score/song/friend?song_id={song["sid"]}&difficulty={song["difficulty"]}&start=0&limit=30'
        async with self._session.get(songs_url, headers=headers) as r:
            result = await r.json()
            if result['success'] is False:
                raise Exception(
                    f'Error fetching play info for {song["sid"]} {song["difficulty"]}')

            for value in result['value']:
                if value['user_id'] == user_id:
                    value.update(song)
                    return value
        return {}

    async def fetch_recent_play_info(self, user_id: int) -> dict:
        async with self._session.get(self.base_url+'/webapi/user/me', headers=headers) as r:
            result = await r.json()

            if result['success']:
                for friend in result['value']['friends']:
                    if friend['user_id'] == user_id:
                        return friend['recent_score'][0]
        return {}

    async def add_friend(self, user_code: str) -> dict:
        async with self._session.post(
                self.base_url+'/webapi/friend/me/add',
                headers={
                    'Content-Type': 'multipart/form-data; boundary=boundary', **headers},
                data=f'--boundary\r\nContent-Disposition: form-data; name=\"friend_code\"\r\n\r\n{user_code}\r\n--boundary--\r\n') as r:

            friend_data = await r.json()

        return friend_data

    async def del_friend(self, user_id: int) -> dict:
        async with self._session.post(
                self.base_url+'/webapi/friend/me/delete',
                headers={
                    'Content-Type': 'multipart/form-data; boundary=boundary', **headers},
                data=f'--boundary\r\nContent-Disposition: form-data; name=\"friend_id\"\r\n\r\n{user_id}\r\n--boundary--\r\n') as r:
            friend_data = await r.json()
        return friend_data

    async def update_friend_list(self) -> None:
        async with self._session.get(self.base_url+'/webapi/user/me', headers=headers) as r:
            resp = await r.json()
            self.friend_ids = set([f['user_id']
                                  for f in resp['value']['friends']])

    async def get_slst(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.chinosk6.cn/arcscore/get_slst') as r:
                songlist_response = await r.json()
        return songlist_response

    async def open_session(self) -> None:
        self.__class__._session = aiohttp.ClientSession()

    @classmethod
    def close_session(cls) -> None:
        if cls._session and not cls._session.closed:
            cls._loop.run_until_complete(
                cls._loop.create_task(cls._session.close()))

    async def get_user_id(self, user_code: str) -> tuple[int, str]:
        if self._session is None or self._session.closed:
            await self.open_session()

        if not self.is_logged_in:
            await self.login()

            if not self.is_logged_in:
                raise ValueError('Login failed!')

        await self.update_friend_list()

        # delete all friends before querying user
        for user_id in self.friend_ids:
            await self.del_friend(user_id)

        resp = await self.add_friend(user_code)
        if resp.get('success'):
            user_id = resp['value']['friends'][0]['user_id']
            username = resp['value']['friends'][0]['name']
            return user_id, username
        elif resp.get('error_code') == 401:
            raise Exception('User not found!')
        else:
            raise Exception(
                f'Unknown error!,{resp}')

    async def fetch_all(self, user_code: str) -> tuple[dict, str]:
        user_id, user_name = await self.get_user_id(user_code)

        tasks = [await self.fetch_play_info(song, user_id) for song in self._songlist]
        result = {}
        for play_data in tasks:
            if not play_data:
                continue
            if play_data['sid'] not in result:
                result[play_data['sid']] = {}

            result[play_data['sid']][play_data['difficulty']] = {
                'score': play_data.get('score', 'N/A'),
                'play_rating': await self.score_to_rating(play_data.get('rating', 'N/A')/10, play_data.get('score', 'N/A')),
                'best_clear_type': play_data.get('best_clear_type', 'N/A'),
                'shiny_perfect_count': play_data.get('shiny_perfect_count', 'N/A'),
                'perfect_count': play_data.get('perfect_count', 'N/A'),
                'near_count': play_data.get('near_count', 'N/A'),
                'miss_count': play_data.get('miss_count', 'N/A'),
                'rating': play_data.get('rating', 'N/A'),
                'time_played': play_data.get('time_played', 'N/A')
            }

        return result, user_name

    async def fetch_recent(self, target_user_code: str) -> dict:
        target_user_id, username = await self.get_user_id(target_user_code)
        recent_play = await self.fetch_recent_play_info(target_user_id)
        this_song = next(
            filter(lambda song: is_same_song(song, recent_play), self._songlist), None)

        if this_song:
            recent_play['rating'] = this_song['rating'] / \
                10 if this_song['rating'] != -1 else 0

        recent_play['play_rating'] = await self.score_to_rating(recent_play.get('rating', 0), recent_play.get('score', 0))
        recent_play['username'] = username
        return recent_play


class AssetFetcher:
    base_url = 'https://moyoez.github.io/ArcaeaResource-ActionUpdater/arcaea/assets'
    songlist = get(f'{base_url}/songs/songlist')
    songlist_map = {song['id']: song for song in songlist.json()['songs']}

    @classmethod
    async def fetch_song_cover(cls, song_id: int, difficulty: int) -> str:
        song_data = cls.songlist_map[song_id]
        song_name = f'dl_{song_id}' if song_data.get(
            'remote_dl', False) else song_id

        difficulty_name = str(difficulty) if song_data['difficulties'][difficulty].get(
            'jacketOverride', False) else 'base'

        for prefix in ['1080_', '']:
            filename = f'{prefix}{difficulty_name}.jpg'
            song_cover_url = f'{cls.base_url}/songs/{song_name}/{filename}'
            async with aiohttp.ClientSession() as session:
                async with session.get(song_cover_url) as r:
                    if r.status == 200:
                        return song_cover_url

        return f'{cls.base_url}/songs/{song_name}/base.jpg'
