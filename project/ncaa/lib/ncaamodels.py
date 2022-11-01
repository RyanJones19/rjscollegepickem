"""
NCAA API request and response models
"""
import typing
import pydantic

class StadiumResponseModel(pydantic.BaseModel):
    StadiumID: int
    Name: str
    City: typing.Optional[str]
    State: typing.Optional[str]

class GameResponseModel(pydantic.BaseModel):
    GameID: int
    Season: int
    SeasonType: int
    Week: int
    Status: str
    HomeTeam: str
    AwayTeam: str
    HomeTeamName: str
    AwayTeamName: str
    HomeTeamScore: typing.Optional[int]
    AwayTeamScore: typing.Optional[int]
    HomeTeamID: int
    AwayTeamID: int
    Possession: typing.Optional[str]
    TimeRemainingMinutes: typing.Optional[typing.Any]
    TimeRemainingSeconds: typing.Optional[typing.Any]
    Period: typing.Optional[str]
    PointSpread: typing.Optional[int]
    IsClosed: bool
    YardLine: typing.Optional[typing.Any]
    YardLineTerritory: typing.Optional[typing.Any]
    Down: typing.Optional[typing.Any]
    Distance: typing.Optional[typing.Any]
    Stadium: StadiumResponseModel
    DateTime: typing.Optional[str]

class ScheduleResponseModel(pydantic.BaseModel):
    __root__: typing.List[GameResponseModel]

class TeamResponseModel(pydantic.BaseModel):
    TeamID: int
    Key: str
    School: str
    Name: str
    ApRank: typing.Optional[int]
    Wins: typing.Optional[int]
    Losses: typing.Optional[int]

class TeamInfoResponseModel(pydantic.BaseModel):
    __root__: typing.List[TeamResponseModel]

class CorrectTeamResponseModel(pydantic.BaseModel):
    name: typing.Optional[str]
    alias: typing.Optional[str]

class CorrectScoringResponseModel(pydantic.BaseModel):
    home_points: typing.Optional[int]
    away_points: typing.Optional[int]

class CorrectVenueResponseModel(pydantic.BaseModel):
    name: typing.Optional[str]
    city: typing.Optional[str]

class CorrectGamesResponseModel(pydantic.BaseModel):
    home: CorrectTeamResponseModel
    away: CorrectTeamResponseModel
    scheduled: str
    venue: typing.Optional[CorrectVenueResponseModel]
    scoring: typing.Optional[CorrectScoringResponseModel]

class CorrectWeekResponseModel(pydantic.BaseModel):
    games: typing.List[CorrectGamesResponseModel]

class CorrectScoresResponseModel(pydantic.BaseModel):
    week: CorrectWeekResponseModel

class CorrectScoresResponseModelList(pydantic.BaseModel):
    __root__: CorrectScoresResponseModel

