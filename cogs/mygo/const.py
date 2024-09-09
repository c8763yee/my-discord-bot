from enum import IntEnum

PAGED_BY: int = 25
HEIGHT: int = 480

MICROSECOND: int = 1000
SECOND: int = 1
MINUTE: int = 60
HOUR: int = 3600


class IndexEnum(IntEnum):
    RESPONSE = 0
    SUBTITLE = 1
    PREV = 2
    SUBMIT = 3
    NEXT = 4
