import datetime
import os

from discord.ext import tasks

from cogs import CogsExtension
from loggers import setup_package_logger

from .utils import ChatGPTUtils

logger = setup_package_logger(__name__)


class ChatGPTTasks(CogsExtension):
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = ChatGPTUtils(bot)
