from pydantic import BaseModel, Field


class UpcomingContest(BaseModel):
    title: str
    titleSlug: str
    startTime: int
    duration: int
    typename: str = Field(alias="__typename")


class UpcomingContestsResponse(BaseModel):
    class Data(BaseModel):
        upcomingContests: list[UpcomingContest]

    data: Data
