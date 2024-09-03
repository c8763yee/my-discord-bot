import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cogs.mygo.schema import SubtitleItem
from core.func import db_insert_subtitle_data
from database import BaseSQLModel, SentenceItem


# ------------------------------- fixture -------------------------------
@pytest_asyncio.fixture(scope="session")
async def session_fixture():
    engine = create_async_engine("sqlite+aiosqlite:///test.db", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseSQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()
    # (Path.unlink not working for async session fixture)
    os.remove("test.db")  # noqa: PTH107


@pytest_asyncio.fixture(scope="function")
async def sentence_item() -> SentenceItem:
    return SentenceItem(
        segment_id=1,
        frame_start=5,
        frame_end=10,
        text="Hello",
        episode="test",
    )


@pytest_asyncio.fixture(scope="function")
async def data() -> SubtitleItem:
    return SubtitleItem(
        result=[
            SentenceItem(
                segment_id=1,
                frame_start=5,
                frame_end=10,
                text="Hello",
                episode="test",
            )
        ]
    )


# ------------------------------- test -------------------------------
@pytest.mark.asyncio
async def test_insert_subtitle_data(data: SubtitleItem, session_fixture: AsyncSession):
    await db_insert_subtitle_data(data, session_fixture)

    result = (await session_fixture.exec(select(SentenceItem))).all()
    assert len(result) == 1
    result = result[0]

    for attr in data.result[0].__dict__.keys():
        if attr.startswith("_"):
            continue
        assert getattr(result, attr) == getattr(data.result[0], attr)


@pytest.mark.asyncio
async def test_insert_subtitle_data_update(data: SubtitleItem, session_fixture: AsyncSession):
    data.result[0].text = "Hi"
    await db_insert_subtitle_data(data, session_fixture, update=True)
    after = (await session_fixture.exec(select(SentenceItem))).all()

    assert len(after) == 1
    after = after[0]

    for attr in data.result[0].__dict__.keys():
        if attr.startswith("_"):
            continue
        assert getattr(after, attr) == getattr(data.result[0], attr)
