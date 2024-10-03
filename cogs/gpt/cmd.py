from typing import Literal

import discord
from discord.ext import commands

from cogs import CogsExtension
from config import OpenAIConfig

from .utils import ChatGPT, ChatGPTResponseFormatter


class ChatGPTCMD(CogsExtension):
    @commands.hybrid_group(ephemeral=True)
    async def chatgpt(self, _: commands.Context):
        """Command that can let you interact with OpenAI's ChatGPT and DALL-E models."""

    @chatgpt.command("ask")
    async def ask(
        self,
        ctx: commands.Context,
        question: str,
        model: Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"] = OpenAIConfig.CHAT_MODEL,
        save_history: bool = False,
    ):
        await ctx.interaction.response.defer()
        gpt = ChatGPT(history_id=str(ctx.author.id), use_db=save_history)
        await gpt.retrieve_history()
        answer, usage = await gpt.ask(question, model=model)
        usage_embed = await ChatGPTResponseFormatter.usage(usage)
        return await ctx.interaction.followup.send(answer, embed=usage_embed)

    @chatgpt.command("dalle")
    async def dall_e(
        self,
        ctx: commands.Context,
        prompt: str,
        model: Literal["dall-e-2", "dall-e-3"] = OpenAIConfig.IMAGE_MODEL,
    ):
        await ctx.interaction.response.defer()
        image_urls = await ChatGPT(history_id=str(ctx.author.id)).generate_images(prompt, model)
        return await ctx.interaction.followup.send(image_urls[0])

    @chatgpt.command("vision")
    async def vision(
        self,
        ctx: commands.Context,
        text: str,
        image: discord.Attachment,
        save_history: bool = False,
        model: Literal["gpt-4o", "gpt-4o-mini"] = OpenAIConfig.VISION_MODEL,
    ):
        await ctx.interaction.response.defer()
        gpt = ChatGPT(history_id=str(ctx.author.id), use_db=save_history)
        await gpt.retrieve_history()
        vision_response, usage = await gpt.vision(text, image.url, model=model)
        usage_embed = await ChatGPTResponseFormatter.usage(usage)
        return await ctx.interaction.followup.send(vision_response, embed=usage_embed)

    @chatgpt.command("clear")
    async def clear_history(self, ctx: commands.Context):
        await ctx.interaction.response.defer()
        await ChatGPT(history_id=str(ctx.author.id), use_db=True).clear_history()
        return await ctx.interaction.followup.send("Chat history cleared.")
