import os
import subprocess

from cogs import CogsExtension
from .const import TEMPERATURE_COMMAND
from loggers import setup_package_logger
from datetime import datetime
logger = setup_package_logger(__name__)


class RaspberryPiUtils(CogsExtension):
    async def get_temperature(self) -> str:
        temperature = float(subprocess.check_output(
            TEMPERATURE_COMMAND, shell=True).decode())

        message = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]: ")

        if temperature > 80:
            logger.warning(
                f"Temperature Too High: {temperature} °C, Rebooting")
            self.bot.get_channel(int(os.environ['TEST_CHANNEL_ID'])).send(
                f"Temperature Too High: {temperature} °C, Rebooting")
            os.system("sudo reboot")
        elif temperature > 60:
            message += f"Temperature High: {temperature} °C, Consider Rebooting or Cooling"
            logger.warning(message)
        else:
            message += f"Temperature: {temperature} °C"
            logger.info(message)

        return message
