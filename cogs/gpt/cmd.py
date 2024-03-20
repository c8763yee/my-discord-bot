from discord.ext import commands

from loggers import setup_package_logger

from .tasks import ChatGPTTasks

logger = setup_package_logger(__name__)


class ChatGPTCMD(ChatGPTTasks):
    @commands.hybrid_group(ephermal=True)
    async def chatgpt(self, ctx: commands.Context):
        pass

    @chatgpt.command("ask")
    async def ask(self, ctx: commands.Context, question: str):
        await ctx.interaction.response.defer()
        answer, embed = await self.utils.ask(question)
        return await ctx.interaction.followup.send(answer, embed=embed)

    @chatgpt.command("dalle")
    async def dall_e(self, ctx: commands.Context, prompt: str):
        await ctx.interaction.response.defer()
        image_url = await self.utils.generate_image(prompt)
        return await ctx.interaction.followup.send(image_url)
