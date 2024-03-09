# -*- coding: utf8 -*-
import logging
import os
import sys
import time
import datetime
FORMAT_PATTERN = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(funcName)s - %(message)s"
logging.basicConfig(level=logging.NOTSET, handlers=None)
TZ = datetime.timezone(datetime.timedelta(hours=8))


class ColoredFormatter(logging.Formatter):
    """
    A custom formatter to add colors to the log messages based on the log level.
    Only works for console logs(stdout, stderr) and not for file logs.
    """
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, *,
                 defaults=None):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style,
                         validate=validate, defaults=defaults)
        self.FORMATS = {
            logging.DEBUG: self.blue + fmt + self.reset,
            logging.INFO: self.grey + fmt + self.reset,
            logging.WARNING: self.yellow + fmt + self.reset,
            logging.ERROR: self.red + fmt + self.reset,
            logging.CRITICAL: self.bold_red + fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_package_logger(package_name, file_level=logging.INFO, console_level=logging.DEBUG) -> logging.Logger:
    """_summary_

    Initialize the logger for the specified module.

    Args:
        package_name (str): The name of the package.
        file_level (int): The log level for the file handler.
        console_level (int): The log level for the console handler.
    """

    package_path_elements = package_name.split('.')
    log_directory_path = os.sep.join(package_path_elements[:-1])
    logger_name = package_path_elements[-1]
    os.makedirs(f'logs/{log_directory_path}', exist_ok=True)

    formatter = logging.Formatter(fmt=FORMAT_PATTERN)
    console_formatter = ColoredFormatter(fmt=FORMAT_PATTERN)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(
        filename=f"logs/{log_directory_path}/{logger_name}.log".replace('//', '/'))
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(package_name)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


if __name__ == '__main__':
    logger = setup_package_logger('a.b.c', file_level=logging.DEBUG)
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
    time.sleep(1)
    print('Check the logs folder for the log files.')
    time.sleep(1)
    print('Press any key to exit.')
    input()
    sys.exit()
