import datetime
import os
from pathlib import Path
from textwrap import dedent

from pydantic import ConfigDict, computed_field
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel

from core import load_env
from loggers import setup_package_logger

db_logger = setup_package_logger("database")
load_env(Path.cwd() / "env" / "db.env")
DATABASE_URL: str = (
    "mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DATABASE}"
).format(
    MYSQL_USER=os.getenv("MYSQL_USER", "root"),
    MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD", "root"),
    MYSQL_HOST=os.getenv("MYSQL_HOST", "localhost"),
    MYSQL_DATABASE=os.getenv("MYSQL_DATABASE", "default"),
)
engine = create_async_engine(DATABASE_URL, echo=False)
db_logger.debug(f"DATABASE_URL: {DATABASE_URL}")


# --------------- SQL Model --------------- #
class BaseSQLModel(SQLModel):
    __abstract__ = True
    __table_args__ = {"extend_existing": True}


# --------------- mygo --------------- #
class EpisodeItem(BaseSQLModel, table=True):
    __tablename__ = "episode"
    model_config = ConfigDict(title=__tablename__)

    episode: str = Field(primary_key=True)
    total_frame: int
    frame_rate: float


class SentenceItem(BaseSQLModel, table=True):
    def __str__(self):
        return dedent(
            f"""
            Episode: {self.episode}
            Frame Start: {self.frame_start}
            Frame End: {self.frame_end}
            Text: {self.text}

            -----------------
            command:
                <prefix>mygo gif {self.episode} {self.frame_start} {self.frame_end}
                <prefix>mygo frame {self.episode} <number in {self.frame_start} ~ {self.frame_end}>

            """
        )

    __tablename__ = "sentence"
    model_config = ConfigDict(title=__tablename__)

    text: str
    episode: str
    frame_start: int
    frame_end: int
    segment_id: int = Field(default=None, primary_key=True)

    @computed_field
    @property
    def gif_command(self) -> str:
        return f"mygo gif {self.episode} {self.frame_start} {self.frame_end}"

    @computed_field
    @property
    def frame_command(self) -> str:
        return f"mygo frame {self.episode} <number in {self.frame_start} ~ {self.frame_end}>"


# --------------- Kasa --------------- #
class Emeter(BaseSQLModel):
    __abstract__ = True
    ID: int = Field(primary_key=True)
    create_time: datetime.datetime = Field(default=datetime.datetime.now())
    name: str = Field(nullable=False)
    status: bool = Field(nullable=False)
    voltage: float = Field(nullable=False, alias="V")
    current: float = Field(nullable=False, alias="A")
    power: float = Field(nullable=False, alias="W")
    total_wh: float = Field(nullable=False)


class HS300(Emeter, table=True):
    __tablename__ = "hs300"


class PC(Emeter, table=True):
    __tablename__ = "pc"


class ScreenFHD(Emeter, table=True):
    __tablename__ = "screen_fhd"


class Screen2K(Emeter, table=True):
    __tablename__ = "screen_2k"


class NintendoSwitch(Emeter, table=True):
    __tablename__ = "switch"


class PhoneCharge(Emeter, table=True):
    __tablename__ = "phone"


class RaspberryPi(Emeter, table=True):
    __tablename__ = "pi"
