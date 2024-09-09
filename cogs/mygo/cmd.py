from collections.abc import Callable
from io import BytesIO
from typing import Literal

from discord import File, Interaction
from discord.enums import ButtonStyle
from discord.ext import commands
from discord.ui import Button, Select

from cogs import CogsExtension
from core.classes import CogsView

from .const import PAGED_BY, IndexEnum
from .schema import SentenceItem
from .types import EpisodeChoices
from .utils import SubtitleUtils


class SubtitleView(CogsView):
    def __init__(
        self,
        *,
        text: str,
        utils: SubtitleUtils,
        timeout: float | None = 60.0,
        page: int = 1,
        episode: EpisodeChoices | None = None,
    ):
        """- self.children
        0: PrevButton
        1: NextButton
        2: SubmitButton
        3: ResponseSelect
        4: SubtitleSelect

        """
        super().__init__(timeout=timeout)
        self.page = page
        self.text = text
        self.utils = utils
        self.episode = episode

        prev_button = Button(label="Previous", custom_id="previous", emoji="⬅️", disabled=True)
        next_button = Button(label="Next", custom_id="next", emoji="➡️")
        submit_button = Button(
            label="Submit", custom_id="submit", emoji="✅", style=ButtonStyle.success
        )
        response_select = Select(placeholder="Select response")
        response_select.add_option(label="Frame", value="frame")
        response_select.add_option(label="Gif", value="gif")
        subtitle_select = Select(placeholder="Select subtitle")

        self.add(response_select, callback=self.update_response_value).add(
            subtitle_select, callback=self.update_subtitle
        ).add(prev_button, callback=self.prev_page).add(submit_button, callback=self.submit).add(
            next_button, callback=self.next_page
        )

    async def prev_page(self, interaction: Interaction):
        await interaction.response.defer()
        prev_button: Button = self.children[IndexEnum.PREV]
        next_button: Button = self.children[IndexEnum.NEXT]
        self.page = max(self.page - 1, 1)

        results, count = await self.utils.search_title_by_text(
            self.text, self.episode, nth_page=self.page
        )

        start = (self.page - 1) * PAGED_BY + 1
        end = self.page * PAGED_BY

        prev_button.disabled = self.page == 1
        next_button.disabled = count < end

        self.update_subtitle_select(results)
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=(
                f"Paged {self.page}:\n"
                f"Search {start} ~ {min(end, count)} of {count} results "
                f"for `{self.text}` in episode `{self.episode or 'ALL'}`:\n\n"
            ),
            view=self,
        )

    async def next_page(self, interaction: Interaction):
        await interaction.response.defer()
        prev_button: Button = self.children[IndexEnum.PREV]
        next_button: Button = self.children[IndexEnum.NEXT]

        self.page += 1
        results, count = await self.utils.search_title_by_text(
            self.text, self.episode, nth_page=self.page
        )

        start = (self.page - 1) * PAGED_BY + 1
        end = self.page * PAGED_BY

        prev_button.disabled = self.page == 1
        next_button.disabled = count <= end

        self.update_subtitle_select(results)
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=(
                f"Paged {self.page}:\n"
                f"Search {start} ~ {min(end, count)} of {count} results "
                f"for `{self.text}` in episode `{self.episode or 'ALL'}`:\n\n"
            ),
            view=self,
        )

    async def submit(self, interaction: Interaction):
        await interaction.response.defer()
        subtitle_select: Select = self.children[IndexEnum.SUBTITLE]
        response_select: Select = self.children[IndexEnum.RESPONSE]

        segment_id = subtitle_select.values[0].split(", ")[1]
        response_type = response_select.values[0]

        if response_type not in ("frame", "gif"):
            raise commands.BadArgument("Invalid response type.")

        subtitle_item = await self.utils.get_item_by_segment_id(segment_id)

        if response_type == "frame":
            result = await self.utils.extract_frame(
                subtitle_item.episode, subtitle_item.frame_start
            )
            extension = "png"
        else:
            result: BytesIO = await self.utils.extract_gif(
                subtitle_item.episode, subtitle_item.frame_start, subtitle_item.frame_end
            )
            extension = "gif"

        await interaction.followup.send(
            file=File(result, filename=f"{segment_id}-{response_type}.{extension}"),
        )

    async def update_response_value(self, interaction: Interaction):
        await interaction.response.defer()
        response_select: Select = self.children[IndexEnum.RESPONSE]
        response_select.placeholder = f"Selected: {response_select.values[0]}"
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self)

    async def update_subtitle(self, interaction: Interaction):
        await interaction.response.defer()
        subtitle_select: Select = self.children[IndexEnum.SUBTITLE]
        text = subtitle_select.values[0].split(", ")[0]
        subtitle_select.placeholder = f"Selected: {text}"
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self)

    def add(self, item: Select | Button, callback: Callable | None = None) -> "SubtitleView":
        self.add_item(item)
        if callback:
            item.callback = callback

        return self

    def update_subtitle_select(self, items: list[SentenceItem]) -> "SubtitleView":
        subtitle_select: Select = self.children[IndexEnum.SUBTITLE]
        subtitle_select.options = []  # clear all options
        for item in items:
            subtitle_select.add_option(
                label=f"{item.text}",
                description=(
                    f"Episode {item.episode} - {item.frame_start} ~ {item.frame_end} "
                    f"(segment {item.segment_id})"
                ),
                value=f"{item.text}, {item.segment_id}",
            )

        return self


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
        if count == 0:
            return await ctx.send(f"No result found for `{query}` in episode `{episode or 'ALL'}`")
        start = max(1, (nth_page - 1) * PAGED_BY + 1)  # 1-indexed
        end = min(count, start + len(results) - 1)

        subtitle_view = SubtitleView(text=query, episode=episode, page=nth_page, utils=self.utils)
        subtitle_view.children[IndexEnum.PREV].disabled = nth_page == 1
        subtitle_view.children[IndexEnum.NEXT].disabled = count <= end

        subtitle_view.update_subtitle_select(results)
        await ctx.send(
            f"Search {start} ~ {end} of {count} results"
            f"for `{query}` in episode `{episode or 'ALL'}`",
            view=subtitle_view,
            delete_after=subtitle_view.timeout,
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
        result.episode = result.episode or "ALL"
        if result is None:
            raise commands.BadArgument(f"Segment ID {segment_id} not found.")

        if response_format not in ("frame", "gif"):
            raise commands.BadArgument("Invalid response format.")

        if response_format == "gif":
            file = await self.utils.extract_gif(
                result.episode, result.frame_start, result.frame_end
            )
            filename = f"{result.episode}-{result.frame_start}-{result.frame_end}.gif"

        else:
            file = await self.utils.extract_frame(result.episode, result.frame_start)
            filename = f"{result.episode}-{result.frame_start}.png"

        return await ctx.interaction.followup.send(
            f"Result for segment_id {segment_id}"
            f"({result.text} at {result.episode}\n({result.frame_start} ~ {result.frame_end}))",
            file=File(file, filename=filename),
        )
