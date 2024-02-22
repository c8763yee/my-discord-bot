import json
import os
import re
from datetime import datetime
from io import BytesIO

import discord
from aiohttp import ClientSession
from discord.ext import commands

from . import Cog_Extension, Field

# https://github.com/akarsh1995/leetcode-graphql-queries for more queries
QUERY = ''
with open('queries/profile_page.graphql', 'r') as f:
    QUERY = f.read()


class LeetCode(Cog_Extension):
    difficulty_color = {
        'Easy': 0x00ff00,
        'Medium': 0xffff00,
        'Hard': 0xff0000
    }

    @commands.hybrid_group()
    async def leetcode(self, ctx: commands.Context):
        await ctx.response.defer()

    @leetcode.command('daily')
    async def fetch_leetcode_daily_challenge(self, ctx: commands.Context):
        """send embed message with leetcode daily challenge data
        including title, difficulty, tags, link, etc.
        """

        THUMBNAIL_URL = 'https://leetcode.com/static/images/LeetCode_Sharing.png'
        async with ClientSession() as session:
            async with session.post('https://leetcode.com/graphql', json={'query': QUERY, 'operationName': 'questionOfToday', 'variables': {}}) as resp:
                data = await resp.json()

        question = data['data']['activeDailyCodingChallengeQuestion']['question']
        ID = question['frontendQuestionId']
        title = f'{ID}. {question["title"]}'
        difficulty = question['difficulty']
        color = self.difficulty_color[difficulty]

        link = Field(
            name='Link', value=f"https://leetcode.com{data['data']['activeDailyCodingChallengeQuestion']['link']}", inline=False)
        difficulty = Field(name='Difficulty', value=difficulty, inline=True)
        topic = Field(name='Topic', value=', '.join(
            map(lambda tag: tag['name'], question['topicTags'])), inline=True)
        ac_rate = Field(name='Acceptance Rate',
                        value=f'{question["acRate"]:.2f}%', inline=True)

        embed = await self.create_embed(
            title, 'Today\'s Leetcode Daily Challenge', THUMBNAIL_URL, color, link, difficulty, topic, ac_rate)
        await ctx.send(embed=embed)

    @leetcode.command('user', ephemeral=True)
    async def fetch_user(self, ctx: commands.Context, username: str):
        global QUERY
        operation_name = []
        await ctx.interaction.response.defer()
        for line in QUERY.split('\n'):
            # query <topic>($username: String!), get the topic query using group
            if re.match(r'^\s*query\s+([a-zA-Z]+)\s*\((.*)\)\s*{', line) is None:
                continue
            operation_name.append(
                re.match(r'^\s*query\s+([a-zA-Z]+)\s*\((.*)\)\s*{', line).group(1))

        response = {}
        async with ClientSession() as session:
            for operation in operation_name:
                now = datetime.now()
                body = {'query': QUERY, 'operationName': operation, 'variables': {
                    'username': username, 'year': now.year, 'month': now.month, 'limit': 5}}

                async with session.post('https://leetcode.com/graphql', json=body) as resp:
                    response[operation] = await resp.json()

        # ...
        with open('response.json', 'w') as f:
            json.dump(response, f, indent=2,
                      ensure_ascii=False, sort_keys=True)
        buffer = BytesIO()
        buffer.write(json.dumps(response, indent=2).encode())
        buffer.seek(0)
        await ctx.interaction.followup.send(file=discord.File(buffer, filename='response.json'))


async def setup(bot: commands.Bot):
    await bot.add_cog(LeetCode(bot))


async def teardown(bot: commands.Bot):
    await bot.remove_cog('LeetCode')
