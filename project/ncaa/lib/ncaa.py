import typing
import json
import pydantic
import urllib.parse
import re
import sys
import ast
import requests
import os
from datetime import datetime
from datetime import timedelta
from .base_client import *
from .ncaamodels import (
    ScheduleResponseModel,
    TeamInfoResponseModel,
    CorrectScoresResponseModelList
)

class NCAAAPI(BaseClient):
    def __init__(self, access_token: typing.Optional[str] = None, logger=None):
        super().__init__(access_token=access_token, logger=logger)
        self.logger.debug("NCAAAPI::__init__()")

    def get_weekly_matchups(
        self,
        year,
        week,
        scheduleSelections = None
    ) -> ScheduleResponseModel:
        matchups = []
        scheduleParsed = []
        route = f"cfb/scores/json/GamesByWeek/{year}/{week}"
        response = self.assert_request(request_type="GET", route=route, host_number=1)
        schedule = pydantic.parse_obj_as(ScheduleResponseModel, response.json())

        if scheduleSelections is not None:
            for game in schedule.__root__:
                if str(game.GameID) in scheduleSelections:
                    scheduleParsed.append(game)
            try:
                scheduleParsed = sorted(scheduleParsed, key=lambda d: d.DateTime)
            except Exception as e:
                scheduleParsed = scheduleParsed
        else:
            scheduleParsed = schedule.__root__

        route = f"cfb/scores/json/Teams"
        response = self.assert_request(request_type="GET", route=route, host_number=1)
        teamdata = pydantic.parse_obj_as(TeamInfoResponseModel, response.json())
        teamMap = {}

        sportsDataAPIKey = os.environ['SPORTS_RADAR_API_KEY']

        correctScoresResponse = requests.get(f"https://api.sportradar.us/ncaafb/trial/v7/en/games/{year}/REG/{week}/schedule.json?api_key={sportsDataAPIKey}")
        correctScores = pydantic.parse_obj_as(CorrectScoresResponseModelList, correctScoresResponse.json())


        for team in teamdata.__root__:
            teamMap[team.TeamID] = team

        for game in scheduleParsed:
            game_id = game.GameID
            status = game.Status
            startTime = game.DateTime
            details = ""
            if game.Status == "Scheduled":
                if (game.DateTime is not None):
                    d = datetime.strptime(game.DateTime, '%Y-%m-%dT%H:%M:%S') - timedelta(hours=3)
                    s = d.strftime('%m/%d/%Y %I:%M %p')
                    status = s
                else:
                    status = "Scheduled - Time TBD"

            for correctScore in correctScores.__root__.week.games:
                try:
                    d1 = datetime.strptime(correctScore.scheduled, '%Y-%m-%dT%H:%M:%S+00:00') - timedelta(hours=5)
                    d2 = datetime.strptime(game.DateTime, '%Y-%m-%dT%H:%M:%S')
                except:
                    d1 = None
                    d2 = None

                if ((correctScore.home.name in game.HomeTeamName or game.HomeTeamName in correctScore.home.name) and (correctScore.away.name in game.AwayTeamName or game.AwayTeamName in correctScore.away.name)) or (correctScore.venue.name is not None and (correctScore.venue.name in game.Stadium.Name or game.Stadium.Name in correctScore.venue.name) and correctScore.venue.city == game.Stadium.City and d1 == d2):
                    if correctScore.scoring is not None and correctScore.scoring.home_points is not None:
                        # sometimes the two APIs flip flop which teams are Home and Away (seems only neutral venues)
                        if(game.HomeTeamName == correctScore.away.name):
                            home_team = game.HomeTeam + ": " + str(correctScore.scoring.away_points)
                        else:
                            home_team = game.HomeTeam + ": " + str(correctScore.scoring.home_points)
                    else:
                        home_team = game.HomeTeam + ": 0"
                    if correctScore.scoring is not None and correctScore.scoring.away_points is not None:
                        if(game.AwayTeamName == correctScore.home.name):
                            away_team = game.AwayTeam + ": " + str(correctScore.scoring.home_points)
                        else:
                            away_team = game.AwayTeam + ": " + str(correctScore.scoring.away_points)
                    else:
                        away_team = game.AwayTeam + ": 0"
                    break

            # OLD API with intentionally incorrect scores
            #if game.HomeTeamScore is not None:
            #    home_team = game.HomeTeam + ": " + str(game.HomeTeamScore)
            #else:
            #    home_team = game.HomeTeam + ": 0"
            #if game.AwayTeamScore is not None:
            #    away_team = game.AwayTeam + ": " + str(game.AwayTeamScore)
            #else:
            #    away_team = game.AwayTeam + ": 0"

            homeTeamRank = ""
            awayTeamRank = ""
            if teamMap[game.HomeTeamID].ApRank is not None:
                homeTeamRank = " (#" + str(teamMap[game.HomeTeamID].ApRank) + ")"
            if teamMap[game.AwayTeamID].ApRank is not None:
                awayTeamRank = " (#" + str(teamMap[game.AwayTeamID].ApRank) + ")"
            if game.PointSpread is not None:
                home_details = "HOME: " + game.HomeTeamName + homeTeamRank +  " (" + str(teamMap[game.HomeTeamID].Wins) + "-" + str(teamMap[game.HomeTeamID].Losses) + ")" + " | " + str(game.PointSpread)
                away_details = "AWAY: " + game.AwayTeamName + awayTeamRank + " (" + str(teamMap[game.AwayTeamID].Wins) + "-" + str(teamMap[game.AwayTeamID].Losses) + ")" + " | " + str(-1 * game.PointSpread)
            else:
                home_details = "HOME: " + game.HomeTeamName + homeTeamRank +  " (" + str(teamMap[game.HomeTeamID].Wins) + "-" + str(teamMap[game.HomeTeamID].Losses) + ")"
                away_details = "AWAY: " + game.AwayTeamName + awayTeamRank + " (" + str(teamMap[game.AwayTeamID].Wins) + "-" + str(teamMap[game.AwayTeamID].Losses) + ")"

            if(game.Period is not None and game.Period != "F" and game.TimeRemainingMinutes is not None and game.TimeRemainingSeconds is not None):
                if game.TimeRemainingSeconds < 10:
                    remainingSeconds = "0" + str(game.TimeRemainingSeconds)
                else:
                    remainingSeconds = str(game.TimeRemainingSeconds)
                details = "Q" + str(game.Period) + " " + str(game.TimeRemainingMinutes) + ":" + remainingSeconds
            if(game.Down is not None and game.Distance is not None):
                if str(game.Down) == "1":
                    down = "1st"
                elif str(game.Down) == "2":
                    down = "2nd"
                elif str(game.Down) == "3":
                    down = "3rd"
                else:
                    down = "4th"
                details = details + " " + down + " & " + str(game.Distance)
            # Uncomment after valid API Key to unscramble
            #if(game.Possession is not None and game.YardLineTerritory):
            #    details = details + " - POSSESSION: " + game.Possession + " - TERRITORY: " + game.YardLineTerritory
            if(status != "InProgress"):
                details = details + status
            else:
                if(game.Period == "Half"):
                    details = details + game.Period
            if(game.Stadium.Name is not None and game.Stadium.City is not None and game.Stadium.State is not None):
                details = details + " - " + str(game.Stadium.Name) + " - " + str(game.Stadium.City) + ", " + str(game.Stadium.State)

            matchups.append({\
            "game_id": game_id, \
            "home_team_details": home_team, \
            "away_team_details": away_team, \
            "game_details": details, \
            "home": home_details,\
            "away":  away_details,\
            "kickoff": startTime, \
            "isClosed": game.IsClosed})

        return matchups

    # Fetch the current season week to set default week settings on page
    def get_current_week(self):
        route = f'cfb/scores/json/CurrentSeasonDetails'
        response = self.assert_request(request_type="GET", route=route, host_number=1)
        apiWeek = str(json.loads(response.text)['ApiWeek'])
        return apiWeek