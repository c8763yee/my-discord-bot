from cogs import CogsExtension

from .const import (BELOW_EX_SCORE, BELOW_EX_SCORE_DELTA, EX_RATING_DELTA,
                    EX_SCORE, EX_SCORE_DELTA, PM_RATING_DELTA, PM_SCORE)


class ArcaeaUtils(CogsExtension):
    async def step_to_rating(self, char_step: int, world_step: float) -> float:
        return ((50 / char_step * world_step - 2.5) / 2.45) ** 2

    async def rating_to_step(self, char_step: int, rating: float) -> float:
        return char_step / 50 * (2.5 + 2.45 * rating ** 0.5)

    async def rating_to_score(self, user_rating: float, song_rating: float) -> int:
        diff_rating = user_rating - song_rating

        if diff_rating == PM_RATING_DELTA:
            return PM_SCORE

        elif diff_rating < EX_RATING_DELTA:
            return max(int(BELOW_EX_SCORE + (diff_rating) * BELOW_EX_SCORE_DELTA), 0)

        return int(EX_SCORE + (diff_rating - EX_RATING_DELTA) * EX_SCORE_DELTA)

    async def score_to_rating(self, song_rating: float, score: int) -> float:
        if score >= PM_SCORE:
            return song_rating + PM_RATING_DELTA

        if score < EX_SCORE:
            return max(song_rating + (score - BELOW_EX_SCORE) / BELOW_EX_SCORE_DELTA, 0)

        return song_rating + EX_RATING_DELTA + (score - EX_SCORE) / EX_SCORE_DELTA
