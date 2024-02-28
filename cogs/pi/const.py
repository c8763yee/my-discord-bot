TEMPERATURE_COMMAND: str = '/usr/bin/vcgencmd measure_temp | awk -F"=" \'{print $2}\' | head -c -3'
