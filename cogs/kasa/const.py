from enum import IntEnum


class PlugID(IntEnum):
    POWER_STRIP = 0
    PC = 1
    SCREEN_BENQ = 2
    SCREEN_ASUS = 3
    NINTENDO_SWITCH = 4
    PHONE_CHARGE = 5
    RASPBERRY_PI = 6


class MQTTQoS(IntEnum):
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2
