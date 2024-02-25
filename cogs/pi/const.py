TEMPERATURE_COMMAND = '/usr/bin/vcgencmd measure_temp | awk -F"=" \'{print $2}\' | head -c -3'
