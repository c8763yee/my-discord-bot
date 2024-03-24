import os
import subprocess
from datetime import datetime

import psutil
from discord import Color, Embed

from cogs import CogsExtension
from core.models import Field
from loggers import TZ, setup_package_logger

from .const import REBOOT_TEMPERATURE, TEMPERATURE_COMMAND, WARNING_TEMPERATURE

logger = setup_package_logger(__name__)


class RaspberryPiUtils(CogsExtension):
    @staticmethod
    def convert_to_gb(value: int) -> float:
        return value / 1024 / 1024 / 1024

    async def get_temperature(self) -> str:
        """
        Get the temperature of the Raspberry Pi using the vcgencmd command
        """
        temperature = float(subprocess.check_output(TEMPERATURE_COMMAND, shell=True).decode())

        message = datetime.now(tz=TZ).strftime("[%Y-%m-%d %H:%M:%S]: ")

        if temperature > REBOOT_TEMPERATURE:
            self.logger.warning("Temperature Too High: %s °C, Rebooting", temperature)
            self.bot.get_channel(int(os.getenv("TEST_CHANNEL_ID", None))).send(
                f"Temperature Too High: {temperature} °C, Rebooting"
            )
            os.system("sudo reboot")
        elif temperature > WARNING_TEMPERATURE:
            message += f"Temperature High: {temperature} °C, Consider Rebooting or Cooling"
            self.logger.warning(message)
        else:
            message += f"Temperature: {temperature} °C"
            self.logger.info(message)

        return message

    async def get_stats(self):
        """
        Get current stats of the Raspberry Pi using psutil and vcgencmd
        """
        memory_used = self.convert_to_gb(psutil.virtual_memory().used)
        memory_total = self.convert_to_gb(psutil.virtual_memory().total)

        memory_text = f"""
        Percentage: {psutil.virtual_memory().percent}%
        Used: ({memory_used:.2f}GB / {memory_total:.2f}GB)
        """

        disk_used = self.convert_to_gb(psutil.disk_usage("/").used)
        disk_total = self.convert_to_gb(psutil.disk_usage("/").total)

        disk_text = f"""
        Percentage: {psutil.disk_usage('/').percent}%
        Used: ({disk_used:.2f}GB / {disk_total:.2f}GB)
        """

        message = {
            "now": datetime.now(tz=TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_usage": f"{psutil.cpu_percent()}%",
            "memory_usage": memory_text,
            "disk_usage": disk_text,
            "temperature": await self.get_temperature(),
        }

        return message


class StatsFormatter(RaspberryPiUtils):
    async def format_stats(self, stats: dict) -> Embed:
        embed = await self.create_embed(
            "Raspberry Pi Statistics",
            f'Current Time: {stats["now"]}',
            Field(name="CPU Usage", value=stats["cpu_usage"], inline=False),
            Field(name="Memory Usage", value=stats["memory_usage"], inline=False),
            Field(name="Disk Usage", value=stats["disk_usage"], inline=False),
            Field(name="Temperature", value=stats["temperature"], inline=False),
            color=Color.blue(),
        )
        return embed
