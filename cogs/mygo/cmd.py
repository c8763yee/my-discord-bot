import json
from io import BytesIO
from typing import Literal

from discord import File
from discord.ext import commands

from cogs import CogsExtension

from .const import PAGED_BY
from .types import EpisodeChoices
from .utils import SubtitleUtils


class SubtitleCMD(CogsExtension):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(bot, *args, **kwargs)
        self.utils = SubtitleUtils()

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
        nth_page: int = 1,
    ):
        """Search subtitles by query, then return the result as custom string."""
        results, count = await self.utils.search_title_by_text(query, episode, nth_page=nth_page)

        start = (nth_page - 1) * PAGED_BY + 1  # 1-indexed
        end = start + len(results) - 1
        episode = episode or "ALL"  # convert None to "all"

        await ctx.send(
            f"Search {start} ~ {end} of {count} results for `{query}` in episode `{episode}`:\n\n",
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

    @mygo.command("segment")
    async def search_segment(
        self,
        ctx: commands.Context,
        segment_id: int,
        response_format: Literal["frame", "gif"] = "frame",
    ):
        """Search subtitle by segment_id."""
        await ctx.interaction.response.defer()
        result = await self.utils.get_item_by_segment_id(segment_id)
        file: BytesIO | None = None
        filename: str | None = None

        if result is None:
            raise commands.BadArgument(f"Segment ID {segment_id} not found.")

        if response_format == "gif":
            file = await self.utils.extract_gif(
                result.episode, result.frame_start, result.frame_end
            )
            filename = f"{result.episode}-{result.frame_start}-{result.frame_end}.gif"

        elif response_format == "frame":
            file = await self.utils.extract_frame(result.episode, result.frame_start)
            filename = f"{result.episode}-{result.frame_start}.png"

        return await ctx.interaction.followup.send(
            f"Result for segment_id {segment_id}"
            f"({result.text} at {result.episode}\n({result.frame_start} ~ {result.frame_end}))",
            file=File(file, filename=filename),
        )
