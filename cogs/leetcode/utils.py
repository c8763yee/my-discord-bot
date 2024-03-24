import datetime
import json
import os
import re
from textwrap import dedent
from typing import Optional

import discord
from aiohttp import ClientSession, ContentTypeError
from dotenv import load_dotenv

from cogs import CogsExtension
from core.models import Field
from loggers import TZ, setup_package_logger

from .const import API_URL, THUMBNAIL_URL

logger = setup_package_logger(__name__)

if os.path.exists("env/bot.env"):
    load_dotenv(dotenv_path="env/bot.env", verbose=True, override=True)
with open("secret.json", "r", encoding="utf-8") as f:
    script = json.load(f)
    headers = script["headers"]
    cookies = script["cookies"]
    cookies["csrftoken"] = os.getenv("LEETCODE_CSRFTOKEN", None)

difficulty_color = {
    "Easy": discord.Color.green(),
    "Medium": discord.Color.gold(),
    "Hard": discord.Color.red(),
}


class LeetCodeUtils(CogsExtension):

    async def _send_request_to_api(self, operation: str, query: str, **variables) -> dict:
        request_body = {
            "operationName": operation,
            "variables": variables,
            "query": query,
        }
        async with ClientSession() as session:
            async with session.post(
                API_URL, json=request_body, headers=headers, cookies=cookies
            ) as resp:
                try:
                    response = await resp.json()
                except ContentTypeError as exception:
                    logger.error("Error occurred: %s", exception)
                    raise ValueError(
                        "Error occurred while fetching data from LeetCode API,"
                        f"{(await resp.text())}"
                    ) from exception
        return response

    async def fetch_user_info(self, username: str) -> dict:
        with open("queries/profile_page.graphql", "r", encoding="utf-8") as file:
            user_query: str = file.read()

        operation_name = [
            re.match(r"^\s*query\s+([a-zA-Z]+)\s*\((.*)\)\s*{", line).group(1)
            for line in user_query.split("\n")
            if re.match(r"^\s*query\s+([a-zA-Z]+)\s*\((.*)\)\s*{", line) is not None
        ]

        now = datetime.datetime.now(tz=TZ)
        response = {}
        for operation in operation_name:
            operation_response = await self._send_request_to_api(
                operation,
                user_query,
                username=username,
                year=now.year,
                month=now.month,
                limit=1,
            )

            response[operation] = operation_response["data"]

        return response

    async def fetch_daily_challenge(self) -> dict:
        """send embed message with leetcode daily challenge data
        including title, difficulty, tags, link, etc.
        """
        with open("queries/profile_page.graphql", "r", encoding="utf-8") as file:
            daily_query: str = file.read()

        result = await self._send_request_to_api("questionOfToday", daily_query)
        return result["data"]

    async def fetch_contest(self) -> list[dict]:
        with open("queries/feed.graphql", "r", encoding="utf-8") as file:
            contest_query: str = file.read()

        result = await self._send_request_to_api("upcomingContests", contest_query)
        return result["data"]["upcomingContests"]


class LeetCodeResponseFormatter(CogsExtension):
    async def format_user_info(self, response: dict, username: str) -> discord.Embed:
        matched_user = response["userPublicProfile"]["matchedUser"]
        matched_userprofile = matched_user["profile"]

        thumbnail = matched_userprofile["userAvatar"]
        description = matched_userprofile["aboutMe"]
        # items
        rating_info = response.get("userContestRankingInfo", {}).get("userContestRanking", {}) or {}
        solved_problems = response["userProblemsSolved"]["matchedUser"]["submitStatsGlobal"][
            "acSubmissionNum"
        ]
        language_count = response["languageStats"]["matchedUser"]["languageProblemCount"]

        # data processing
        language_count.sort(key=lambda x: x["problemsSolved"], reverse=True)

        # Fields
        # ------------------------------------------------
        recent_ac_list = response["recentAcSubmissions"]["recentAcSubmissionList"]
        recent_ac = (
            f'[{recent_ac_list[0]["title"]}]'
            f'(https://leetcode.com/problems/{recent_ac_list[0]["titleSlug"]})'
        )
        # ------------------------------------------------
        rating = dedent(
            f"""
            attempts: {rating_info.get('attendedContestsCount', 'N/A')}
            Rank: {rating_info.get('globalRanking', 'N/A')}/ \
                                   {rating_info.get('totalParticipants', 'N/A')}
            Rating: {rating_info.get('rating', 'N/A')}
            Top %: {rating_info.get('topPercentage', 0):.2f}%
            """
        )

        solved_count = "\n".join(
            [f"{item['difficulty']}: {item['count']}" for item in solved_problems]
        )
        languages = "\n".join(
            [f"{item['languageName']}: {item['problemsSolved']}" for item in language_count]
        )
        return await self.create_embed(
            matched_userprofile["realName"],
            description,
            Field(name="Recent AC", value=recent_ac, inline=False),
            Field(name="Rating", value=rating, inline=True),
            Field(name="Solved Count", value=solved_count, inline=True),
            Field(name="Languages", value=languages, inline=False),
            color=discord.Color.blurple(),
            thumbnail_url=thumbnail,
            url=f"https://leetcode.com/{username}",
        )

    async def format_daily_challenge(self, response: dict) -> tuple[discord.Embed, str]:
        question = response["activeDailyCodingChallengeQuestion"]["question"]
        question_id = question["frontendQuestionId"]
        title = f'{question_id}. {question["title"]}'
        difficulty = question["difficulty"]
        color = difficulty_color[difficulty]

        link = f"https://leetcode.com{response['activeDailyCodingChallengeQuestion']['link']}"

        topic = ", ".join(map(lambda tag: tag["name"], question["topicTags"]))
        ac_rate = f'{question["acRate"]:.2f}%'

        embed = await self.create_embed(
            title,
            "Today's Leetcode Daily Challenge",
            Field(name="Question Link", value=f"[link]({link})", inline=False),
            Field(name="Difficulty", value=difficulty, inline=True),
            Field(name="Topic", value=topic, inline=True),
            Field(name="Acceptance Rate", value=ac_rate, inline=True),
            color=color,
            url=link,
            thumbnail_url=THUMBNAIL_URL,
        )
        return embed, title

    async def contest(
        self, response: dict, only_today: bool = False
    ) -> tuple[bool, Optional[discord.Embed]]:

        if only_today and await self.today_is_contest(response) is False:
            return False, None

        start_time = datetime.datetime.fromtimestamp(response["startTime"], tz=TZ)
        title = description = response["title"]
        link = f'https://leetcode.com/contest/{response["titleSlug"]}/'

        embed = await self.create_embed(
            title,
            description,
            Field(
                name="Start Time",
                value=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                inline=False,
            ),
            color=discord.Color.blurple(),
            url=link,
            thumbnail_url=THUMBNAIL_URL,
        )
        return True, embed

    async def contests(
        self, response: list[dict], only_today: bool = False
    ) -> tuple[bool, list[discord.Embed]]:
        embeds = []
        for contest in response:
            is_success, embed = await self.contest(contest, only_today)
            if is_success:
                embeds.append(embed)
        return bool(embeds), embeds

    async def today_is_contest(self, contest: dict) -> bool:
        start_time = datetime.datetime.fromtimestamp(contest["startTime"], tz=TZ)
        return start_time.date() == datetime.datetime.now(tz=TZ).date()
