from base64 import b64encode as be
from pathlib import Path

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from cogs.mygo.schema import EpisodeItem, SentenceItem, SubtitleItem, engine
from cogs.mygo.utils import SubtitleUtils


def encode_image_to_b64(image_path: str | Path | bytes) -> str:
    if isinstance(image_path, bytes):
        return be(image_path).decode("utf-8")

    if isinstance(image_path, str):
        image_path = Path(image_path)

    with image_path.open("rb") as image:
        return be(image.read()).decode("utf-8")


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def db_insert_subtitle_data(data: SubtitleItem, session: AsyncSession, update: bool = False):
    for item in data.result:
        if (
            old_row := await session.get(SentenceItem, item.segment_id)
        ) is not None and update is True:
            old_row.sqlmodel_update(item)
            session.add(old_row)

        elif old_row is None:
            session.add(item)

    await session.commit()


async def db_insert_episode(episode: str, session: AsyncSession, update: bool = False):
    data = await SubtitleUtils.get_total_frame_number(episode)
    insert_item = EpisodeItem(
        episode=episode, total_frame=data.total_frame, frame_rate=data.frame_rate
    )
    if (old_row := await session.get(EpisodeItem, episode)) is not None and update is True:
        old_row.sqlmodel_update(insert_item)
        session.add(old_row)

    elif old_row is None:
        session.add(insert_item)
    await session.commit()
