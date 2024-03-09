import datetime
import json
import os
import re
from textwrap import dedent

import discord
from aiohttp import ClientSession, ContentTypeError

from cogs import CogsExtension
from core.models import Field
from loggers import setup_package_logger, TZ

from .const import API_URL, LEETCODE_USER_QUERY, THUMBNAIL_URL

logger = setup_package_logger(__name__)


with open("secret.json", "r") as f:
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

    async def send_request_to_leetcode_API(
        self, operation: str, query: str = LEETCODE_USER_QUERY, **variables
    ) -> dict:
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
                except ContentTypeError as e:
                    logger.error(f"Error occurred: {e}")
                    raise ValueError(f"Error occurred while fetching data from LeetCode API, {(await resp.text())[:50]}")
        return response

    async def fetch_leetcode_user_info(self, username: str) -> dict:
        operation_name = [
            re.match(r"^\s*query\s+([a-zA-Z]+)\s*\((.*)\)\s*{", line).group(1)
            for line in LEETCODE_USER_QUERY.split("\n")
            if re.match(r"^\s*query\s+([a-zA-Z]+)\s*\((.*)\)\s*{", line) is not None
        ]

        now = datetime.datetime.now(tz=TZ)
        response = {}
        for operation in operation_name:
            operation_response = await self.send_request_to_leetcode_API(
                operation, username=username, year=now.year, month=now.month, limit=1
            )

            response[operation] = operation_response["data"]

        return response

    async def fetch_leetcode_daily_challenge(self) -> dict:
        """send embed message with leetcode daily challenge data
        including title, difficulty, tags, link, etc.
        """
        return (await self.send_request_to_leetcode_API("questionOfToday"))["data"]


class LeetCodeResponseFormatter(CogsExtension):
    async def format_user_info(self, response: dict, username: str) -> discord.Embed:
        matched_user = response["userPublicProfile"]["matchedUser"]
        matched_userprofile = matched_user["profile"]

        thumbnail = matched_userprofile["userAvatar"]
        description = matched_userprofile["aboutMe"]
        # items
        rating_info = (
            response.get("userContestRankingInfo", dict()).get(
                "userContestRanking", dict()
            )
            or dict()
        )
        solved_problems = response["userProblemsSolved"]["matchedUser"][
            "submitStatsGlobal"
        ]["acSubmissionNum"]
        language_count = response["languageStats"]["matchedUser"][
            "languageProblemCount"
        ]

        # data processing
        language_count.sort(key=lambda x: x["problemsSolved"], reverse=True)

        # Fields
        # ------------------------------------------------
        recent_AC_list = response["recentAcSubmissions"]["recentAcSubmissionList"]
        recent_AC = f'[{recent_AC_list[0]["title"]}](https://leetcode.com/{recent_AC_list[0]["titleSlug"]})'
        # ------------------------------------------------
        rating = dedent(
            f"""
            attempts: {rating_info.get('attendedContestsCount', 'N/A')}
            Rank: {rating_info.get('globalRanking', 'N/A')}/{rating_info.get('totalParticipants', 'N/A')}
            Rating: {rating_info.get('rating', 'N/A')}
            Top %: {rating_info.get('topPercentage', 0):.2f}%
            """
        )

        solved_count = "\n".join(
            [f"{item['difficulty']}: {item['count']}" for item in solved_problems]
        )
        languages = "\n".join(
            [
                f"{item['languageName']}: {item['problemsSolved']}"
                for item in language_count
            ]
        )
        return await self.create_embed(
            matched_userprofile["realName"],
            description,
            discord.Color.blurple(),
            f"https://leetcode.com/{username}",
            Field(name="Recent AC", value=recent_AC, inline=False),
            Field(name="Rating", value=rating, inline=True),
            Field(name="Solved Count", value=solved_count, inline=True),
            Field(name="Languages", value=languages, inline=False),
            thumbnail_url=thumbnail,
        )

    async def format_daily_challenge(self, response: dict) -> tuple[discord.Embed, str]:
        question = response["activeDailyCodingChallengeQuestion"]["question"]
        ID = question["frontendQuestionId"]
        title = f'{ID}. {question["title"]}'
        difficulty = question["difficulty"]
        color = difficulty_color[difficulty]

        link = (
            f"https://leetcode.com{response['activeDailyCodingChallengeQuestion']['link']}"
        )

        topic = ", ".join(map(lambda tag: tag["name"], question["topicTags"]))
        ac_rate = f'{question["acRate"]:.2f}%'

        embed = await self.create_embed(
            title,
            "Today's Leetcode Daily Challenge",
            color,
            link,
            Field(name="Question Link", value=f"[link]({link})", inline=False),
            Field(name="Difficulty", value=difficulty, inline=True),
            Field(name="Topic", value=topic, inline=True),
            Field(name="Acceptance Rate", value=ac_rate, inline=True),
            thumbnail_url=THUMBNAIL_URL,
        )
        return embed, title
