import json
from io import BytesIO

from discord import File
from discord.ext import commands

from cogs import CogsExtension

from .schema import SentenceItem
from .types import EpisodeChoices
from .utils import SubtitleUtils


class SubtitleCMD(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = SubtitleUtils(bot)

    # use custom prefix `!!!!!`
    @commands.hybrid_group(ephemeral=True)
    async def mygo(self, ctx: commands.Context):
        """Function to get frame of videos."""

    @mygo.command(name="frame")
    async def extract_frame(
        self,
        ctx: commands.Context,
        episode: EpisodeChoices,
        frame: int,
    ):
        """Get image at specific frame from video."""
        frame_io: BytesIO = await self.utils.extract_frame(episode, frame)
        await ctx.send(file=File(frame_io, filename=f"{episode}-{frame}.png"))

    @mygo.command(name="gif")
    async def extract_gif(
        self,
        ctx: commands.Context,
        episode: EpisodeChoices,
        start: int,
        end: int,
    ):
        """Get gif from start to end frame from video."""
        await ctx.interaction.response.defer()
        gif_io: BytesIO = await self.utils.extract_gif(episode, start, end)
        await ctx.interaction.followup.send(
            file=File(gif_io, filename=f"{episode}-{start}-{end}.gif")
        )

    @mygo.command(name="search")
    async def search_subtitles(
        self,
        ctx: commands.Context,
        query: str,
        episode: EpisodeChoices | None = None,
        nth_page: int | None = 1,

    ):
        """Search subtitles by query, then return the result as custom string."""
        results: list[SentenceItem] = await self.utils.search_title_by_text(
            query, episode, nth_page=nth_page
        )

        await ctx.send(
            f'Search result for "{query}" in episode {episode} (page {nth_page}):\n\n',
            file=File(
                BytesIO(
                    json.dumps(
                        [result.model_dump() for result in results],
                        indent=2,
                        ensure_ascii=False,
                    ).encode()
                ),
                filename=f"{episode}-{query}.json",
            ),
        )
