from pydantic import BaseModel, Field


class Data(BaseModel): ...


class UpcomingContest(BaseModel):
    title: str
    titleSlug: str
    startTime: int
    duration: int
    typename: str = Field(alias="__typename")


class UpcomingContestsResponse(Data):
    class Data(BaseModel):
        upcomingContests: list[UpcomingContest]

    data: Data
