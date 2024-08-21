from io import BytesIO
from pathlib import Path

import ffmpeg
from sqlmodel import column, select
from sqlmodel.ext.asyncio.session import AsyncSession

from cogs import CogsExtension

from .const import PAGED_BY
from .schema import EpisodeItem, FFProbeResponse, FFProbeStream, SentenceItem, engine
from .types import EpisodeChoices


class SubtitleUtils(CogsExtension):
    @staticmethod
    def _frame_to_time(frame: int, frame_rate: float) -> str:
        seconds, ms = divmod(frame / frame_rate, 1)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{int(ms * 1000):03d}"

    @staticmethod
    async def _check_frame_exist(episode: EpisodeChoices, *frames: int) -> list[bool]:
        async with AsyncSession(engine) as session:
            episode_data = await session.get(EpisodeItem, episode)

        return list(map(lambda frame: 0 <= frame <= episode_data.total_frame, frames))

    @staticmethod
    async def get_total_frame_number(
        episode: EpisodeChoices,
    ) -> FFProbeStream:
        r"""Get total frame number of video file.

        Equivalent to:
            ffprobe -select_streams v:0 -show_streams -print_format json ${episode}.mp4
        """
        video_path = Path.home() / "mygo-anime" / f"{episode}.mp4"

        media = ffmpeg.probe(
            video_path, select_streams="v:0", show_streams=None, print_format="json"
        )

        # get the first video stream
        return FFProbeResponse.model_validate(media).streams[0]

    async def extract_frame(
        self,
        episode: EpisodeChoices,
        frame_number: int,
    ) -> BytesIO:
        r"""Extract frame from video file as BytesIO.

        Equivalent to:
            ffmpeg -i ${episode}.mp4 -ss ${frame_time} -vframes 1 -f image2 -vcodec png -y ${output}
        """
        if all(await self._check_frame_exist(episode, frame_number)) is False:
            raise ValueError(f"Frame {frame_number} does not exist in episode {episode}")

        if frame_number < 0:
            raise ValueError("Frame number must be positive")

        async with AsyncSession(engine) as session:
            episode_data = await session.get(EpisodeItem, episode)

        video_path = Path.home() / "mygo-anime" / f"{episode}.mp4"
        self.logger.info("Extracting frame %d from %s", frame_number, video_path)

        process = ffmpeg.input(
            video_path,
            ss=self._frame_to_time(frame_number, episode_data.frame_rate),
        ).output("pipe:", vframes=1, format="image2", vcodec="mjpeg")
        result, _ = process.run(capture_stdout=True)

        self.logger.debug(
            "Extracted frame %d from %s: result=%s",
            frame_number,
            video_path,
            result[:100],
        )
        return BytesIO(result)

    async def extract_gif(
        self,
        episode: EpisodeChoices,
        start_frame: int,
        end_frame: int,
    ) -> BytesIO:
        r"""Extract frame range from video file as GIF.

        If start frame is greater than end frame, result GIF will be reversed.

        video_path = Path.home() / "mygo-anime" / f"{EPISODE}.mp4"
        # implement below two process

        ffmpeg -ss $start_time -to $end_time -i $video_path -vf "palettegen" -y $palette
        ffmpeg -ss $start_time -to $end_time -i $video_path -i $palette \
            -lavfi "$filters [x]; [x][1:v] paletteuse" -y $output
        """
        video_path = Path.home() / "mygo-anime" / f"{episode}.mp4"
        reverse = False
        async with AsyncSession(engine) as session:
            episode_data = await session.get(EpisodeItem, episode)

        if start_frame > end_frame:
            start_frame, end_frame = end_frame, start_frame
            reverse = True

        elif start_frame == end_frame:
            return await self.extract_frame(
                episode, start_frame
            )  # fallback to extract single frame

        # process palettegen and paletteuse
        input_stream = ffmpeg.input(
            video_path,
            ss=self._frame_to_time(start_frame, episode_data.frame_rate),
            to=self._frame_to_time(end_frame, episode_data.frame_rate),
        )
        if reverse:
            input_stream = input_stream.filter("reverse")

        split = input_stream.split()
        palette = split[0].filter("palettegen")
        process_palette = ffmpeg.filter([split[1], palette], "paletteuse")

        result, _ = process_palette.output(
            "pipe:", vcodec="gif", format="gif", loglevel="quiet"
        ).run(capture_stdout=True)

        return BytesIO(result)

    @staticmethod
    async def search_title_by_text(
        text: str, episode: EpisodeChoices, paged_by: int = PAGED_BY, nth_page: int = 1
    ) -> list[SentenceItem]:
        """(1-indexed).

        Search subtitle by text and episode. and return paged result.

        Assume that paged_by is always greater than 0 and nth_page is always greater than 0

        Equivalent to:
            SELECT * FROM sentence
            WHERE episode = ${episode} AND text LIKE '%${text}%'
            LIMIT ${paged_by} OFFSET ${paged_by * (nth_page - 1)}
        """
        assert paged_by > 0 and nth_page > 0, "Invalid Input"

        async with AsyncSession(engine) as session:
            episode_data = await session.get(EpisodeItem, episode)
            sql_query = (
                select(SentenceItem)
                .where(
                    SentenceItem.episode == episode_data.episode,
                    column("text").contains(text),
                )
                .limit(paged_by)
                .offset(paged_by * (nth_page - 1))
            )

            results: list[SentenceItem] = (await session.exec(sql_query)).all()

        return results
