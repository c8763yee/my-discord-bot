from base64 import b64encode as be

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from cogs.mygo.schema import EpisodeItem, SentenceItem, SubtitleItem, engine
from cogs.mygo.utils import SubtitleUtils


def encode_image_to_b64(image_path: str | bytes) -> str:
    if isinstance(image_path, str):
        with open(image_path, "rb") as image_file:
            return be(image_file.read()).decode("utf-8")
    return be(image_path).decode("utf-8")


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def db_insert_subtitle_data(data: SubtitleItem, update: bool = False):
    async with AsyncSession(engine) as session:
        for item in data.result:
            if (
                old_row := await session.get(SentenceItem, item.segment_id)
            ) is not None and update is True:
                old_row.sqlmodel_update(item)
                session.add(old_row)

            elif old_row is None:
                session.add(item)

        await session.commit()


async def db_insert_episode(episode: str, update: bool = False):
    data = await SubtitleUtils.get_total_frame_number(episode)
    async with AsyncSession(engine) as session:
        insert_item = EpisodeItem(
            episode=episode, total_frame=data.total_frame, frame_rate=data.frame_rate
        )
        if (old_row := await session.get(EpisodeItem, episode)) is not None and update is True:
            old_row.sqlmodel_update(insert_item)
            session.add(old_row)

        elif old_row is None:
            session.add(insert_item)
        await session.commit()
