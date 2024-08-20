from enum import IntEnum

PM_RATING_DELTA = 2.0
EX_RATING_DELTA = 1.0

EX_SCORE_DELTA = 200000
BELOW_EX_SCORE_DELTA = 300000

DIFFICULTY_ABBR = ["PST", "PRS", "FTR", "BYD", "ETR"]
DIFFICULTY_NAMES = ["Past", "Present", "Future", "Beyond", "Eternal"]
DIFFICULTY_COLOR_LIST = ["#165365", "#194A08", "#52184D", "#5A0813", "#5D4E76"]

GRADE_NAMES = ["D", "C", "B", "A", "AA", "EX", "EX+"]
GRADE_SUFFIX = ["d", "c", "b", "a", "aa", "ex", "explus"]
MAX_DIFFICULTY = 4  # Past, Present, Future|Eternal, Beyond
MAX_RATING: list = [6, 9, 10, 12, 12]
MIN_INT = -(2**31)
MAX_INT = 2**31 - 1


class DifficultyEnum(IntEnum):
    PAST = 0
    PRESENT = 1
    FUTURE = 2
    BEYOND = 3
    ETERNAL = 4


class GradeEnum(IntEnum):
    EX_PLUS = 6
    EX = 5
    AA = 4
    A = 3
    B = 2
    C = 1
    D = 0


class GradeScoreEnum(IntEnum):
    PM = 10000000
    EX_PLUS = 9900000
    EX = 9800000
    BELOW_EX = 9500000
    AA = 9500000
    A = 9200000
    B = 8900000
    C = 8600000
    D = 8300000
