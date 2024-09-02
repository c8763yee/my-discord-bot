from pathlib import Path

from dotenv import load_dotenv

from config import Config as config


def load_env(path: Path):
    if config.DEBUG is False:
        path = Path.cwd() / ".env"

    load_dotenv(path, override=True)
