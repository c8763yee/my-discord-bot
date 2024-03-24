from discord.ext import commands

from loggers import setup_package_logger

from .tasks import ChatGPTTasks
from .utils import ChatGPTResopnseFormatter

logger = setup_package_logger(__name__)


class ChatGPTCMD(ChatGPTTasks):

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.formatter = ChatGPTResopnseFormatter()

    @commands.hybrid_group(ephermal=True)
    async def chatgpt(self, ctx: commands.Context):
        """_description_
        dummy function to create a group command

        Args:
            ctx (commands.Context): discord context from the command invoker
        """

    @chatgpt.command("ask")
    async def ask(self, ctx: commands.Context, question: str):
        await ctx.interaction.response.defer()
        answer, usage = await self.utils.get_usage(question)
        usage_embed = await self.formatter.get_usage(usage)
        return await ctx.interaction.followup.send(answer, embed=usage_embed)

    @chatgpt.command("dalle")
    async def dall_e(self, ctx: commands.Context, prompt: str):
        await ctx.interaction.response.defer()
        image_url = await self.utils.generate_image(prompt)
        return await ctx.interaction.followup.send(image_url)
