from enum import IntEnum

PM_RATING_DELTA = 2.0
EX_RATING_DELTA = 1.0

EX_SCORE_DELTA = 200000
BELOW_EX_SCORE_DELTA = 300000

DIFFICULTY_ABBR = ["PST", "PRS", "FTR", "BYD", "ETR"]
DIFFICULTY_NAMES = ["Past", "Present", "Future", "Beyond", "Eternal"]
DIFFICULTY_COLOR_LIST = ["#165365", "#194A08", "#52184D", "#5A0813", "#5D4E76"]

GRADE_NAMES = ["D", "C", "B", "A", "AA", "EX", "EX+"]
GRADE_URL_SUFFIX = ["d", "c", "b", "a", "aa", "ex", "explus"]
DIFFICULTY_LEN = 4  # Past, Present, Future|Eternal, Beyond


class Grade(IntEnum):
    EX_PLUS = 6
    EX = 5
    AA = 4
    A = 3
    B = 2
    C = 1
    D = 0


class GradeScore(IntEnum):
    PM = 10000000
    EX_PLUS = 9900000
    EX = 9800000
    BELOW_EX = 9500000
    AA = 9500000
    A = 9200000
    B = 8900000
    C = 8600000
    D = 8300000
