TEMPERATURE_COMMAND: str = "/usr/bin/vcgencmd measure_temp | awk -F\"=\" '{print $2}' | head -c -3"
REBOOT_TEMPERATURE: float = 80.0
WARNING_TEMPERATURE: float = 60.0
