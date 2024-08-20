from typing import Literal

import discord
from discord.ext import commands

from config import OpenAIConfig
from loggers import setup_package_logger

from .tasks import ChatGPTTasks
from .utils import ChatGPTResopnseFormatter

logger = setup_package_logger(__name__)


class ChatGPTCMD(ChatGPTTasks):
    @commands.hybrid_group(ephermal=True)
    async def chatgpt(self, _: commands.Context):
        """_description_
        dummy function to create a group command.

        Args:
        ----
            ctx (commands.Context): discord context from the command invoker

        """

    @chatgpt.command("ask")
    async def ask(
        self,
        ctx: commands.Context,
        question: str,
        model: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
    ):
        await ctx.interaction.response.defer()
        answer, usage = await self.utils.ask(question, model=model)
        usage_embed = await ChatGPTResopnseFormatter.usage(usage)
        return await ctx.interaction.followup.send(answer, embed=usage_embed)

    @chatgpt.command("dalle")
    async def dall_e(
        self,
        ctx: commands.Context,
        prompt: str,
        model: Literal["dall-e-2", "dall-e-3"] = OpenAIConfig.IMAGE_MODEL,
    ):
        await ctx.interaction.response.defer()
        image_url = await self.utils.generate_image(prompt, model)
        return await ctx.interaction.followup.send(image_url)

    @chatgpt.command("vision")
    async def vision(
        self,
        ctx: commands.Context,
        text: str,
        image: discord.Attachment,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.VISION_MODEL,
    ):
        await ctx.interaction.response.defer()
        vision_response, usage = await self.utils.vision(text, image.url, model=model)
        usage_embed = await ChatGPTResopnseFormatter.usage(usage)
        return await ctx.interaction.followup.send(vision_response, embed=usage_embed)
