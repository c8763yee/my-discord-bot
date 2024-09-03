from enum import IntEnum

from database import (
    HS300,
    PC,
    NintendoSwitch,
    PhoneCharge,
    RaspberryPi,
    Screen2K,
    ScreenFHD,
)


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


plug_mapping = {
    PlugID.POWER_STRIP: HS300,
    PlugID.PC: PC,
    PlugID.SCREEN_BENQ: ScreenFHD,
    PlugID.SCREEN_ASUS: Screen2K,
    PlugID.NINTENDO_SWITCH: NintendoSwitch,
    PlugID.PHONE_CHARGE: PhoneCharge,
    PlugID.RASPBERRY_PI: RaspberryPi,
}
