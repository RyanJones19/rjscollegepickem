from flask import Blueprint, render_template, Flask, request, redirect, url_for, render_template_string
from flask_login import login_required, current_user
from .ncaa.lib.ncaa import NCAAAPI
from .models import User, Scores, Adminselections
from datetime import datetime
from . import db
import json

main = Blueprint('main', __name__)

ncaa_api_client = NCAAAPI()


week="1"
totalWeeks=12

@main.route('/')
def index():
    games=[]
    return render_template('index.html', games=games, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[],totalScore=0, week=week, yearlyScoresDict={})

@main.route('/admin/<week>')
@login_required
def admin(week=1):
    games=ncaa_api_client.get_weekly_matchups(2022, week)
    if current_user.admin == 0:
        return render_template('failedadmin.html', name=current_user.name, games=games, userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})
    else:
        return render_template('admin.html', name=current_user.name, games=games, userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, weekText="Game Options for week " + week, yearlyScoresDict={})

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name, games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})


@main.route('/myscores/<week>')
@login_required
def myscores(week=1):
    try:
        data =  getattr(Adminselections.query.filter_by(year=1).first(), "week" + week).split(',')
    except:
        return render_template('profile.html', name=str(current_user.name) + ", you have not made any picks yet for week " + week + " please go make your selections", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})
    if data is not None:
        games=ncaa_api_client.get_weekly_matchups(2022, week, data)
    else:
        return render_template('profile.html', name=str(current_user.name) + ", you have not made any picks yet for week " + week + " please go make your selections", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})
    picks=getattr(Scores.query.filter_by(id=current_user.id).first(), "week" + week + "picks")

    if picks is not None:
        picks = picks.split(',')
        correctSelections=[]
        incorrectSelections=[]
        selectionDisplay={}
        totalScore = 0
        for i in range(len(games)):
            team = ""
            points = picks[i][1:]
            if picks[i][0] == "1":
                team = games[i]['home_team_details'].split(":")[0]
            else:
                team = games[i]['away_team_details'].split(":")[0]
            selectionDisplay[team] = points
            if int(games[i]['home_team_details'].split(":")[1]) > int(games[i]['away_team_details'].split(":")[1]) and games[i]['isClosed']:
                correctSelections.append(games[i]['home_team_details'].split(":")[0])
                incorrectSelections.append(games[i]['away_team_details'].split(":")[0])
            elif games[i]['isClosed']:
                correctSelections.append(games[i]['away_team_details'].split(":")[0])
                incorrectSelections.append(games[i]['home_team_details'].split(":")[0])
            else:
                print("Game has not yet concluded")
        for winner in correctSelections:
            if winner in selectionDisplay:
                totalScore = totalScore + int(selectionDisplay[winner])
        scores = Scores.query.filter_by(id=current_user.id).first()
        setattr(scores, "week" + week + "score", str(totalScore))
        db.session.commit()
        return render_template('myscores.html', name=current_user.name, games=[], userid=current_user.id, selections=[], selectionDisplay=json.dumps(selectionDisplay), correctSelections=correctSelections, incorrectSelections=incorrectSelections, totalScore=totalScore, week=week, yearlyScoresDict={})
    else:
        return render_template('profile.html', name=current_user.name + ", you have not made any picks yet for week " + week + " please go make your selections", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})

@main.route('/schedule/<week>')
@login_required
def schedule(week=1):
    try:
        data =  getattr(Adminselections.query.filter_by(year=1).first(), "week" + week).split(',')
        games=ncaa_api_client.get_weekly_matchups(2022, week, data)
        userSelectedScores=getattr(Scores.query.filter_by(id=current_user.id).first(), "week" + week + "picks")
        return render_template('schedule.html', games=games, userid=current_user.id, selections=userSelectedScores, selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})
    except:
        return render_template('profile.html', name=" game choices for week " + week + " have not been chosen by an admin yet, please check back later.", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})

@main.route('/submitpicks/<week>', methods=['GET'])
@login_required
def submit_picks(week):
    scores = Scores.query.filter_by(id=current_user.id).first()
    args = request.args
    setattr(scores, "week" + week + "picks", str(args.get("picks")))
    db.session.commit()
    return redirect(url_for('main.profile'))

@main.route('/selectweeklygames/<week>', methods=['GET'])
@login_required
def select_games(week):
    args = request.args
    adminSelections = Adminselections.query.filter_by(year=1).first()
    setattr(adminSelections, "week" + week, str(args.get("selections")))
    db.session.commit()
    return redirect(url_for('main.profile'))

@main.route('/weeklyleaguestats/<week>')
@login_required
def weeklyleaguestats(week):
    try:
        data =  getattr(Adminselections.query.filter_by(year=1).first(), "week" + week).split(',')
    except:
        return render_template('profile.html', name=str(current_user.name) + ", an error occurred loading all other teams picks, please reachout to an admin", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})
    if data is not None:
        games=ncaa_api_client.get_weekly_matchups(2022, week, data)
    else:
        return render_template('profile.html', name=str(current_user.name) + ", an error occurred loading all other teams picks, please reachout to an admin", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})

    for game in range(len(games)):
        if datetime.strptime(games[0]['kickoff'], '%Y-%m-%dT%H:%M:%S') > datetime.now():
            return render_template('profile.html', name=str(current_user.name) + ", games for week " + week + " have not unlocked yet, please check back after the first game kicks off", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})

    allPicks=db.session.query(User,Scores).filter(User.id==Scores.id).all()
    groupSelectionDisplay={}

    if allPicks is not None:
        for picks in allPicks:
            username = picks.User.name
            picks = getattr(picks.Scores, "week" + week + "picks")
            if picks is None:
                groupSelectionDisplay[username] = {
                    'selections': {},
                    'score': 0
                }
                continue
            else:
                picks = picks.split(',')
            correctSelections=[]
            incorrectSelections=[]
            userSelectionDisplay={}
            totalScore = 0
            for i in range(len(games)):
                team = ""
                points = picks[i][1:]
                if picks[i][0] == "1":
                    team = games[i]['home_team_details'].split(":")[0]
                else:
                    team = games[i]['away_team_details'].split(":")[0]
                userSelectionDisplay[team] = points
                if int(games[i]['home_team_details'].split(":")[1]) > int(games[i]['away_team_details'].split(":")[1]) and games[i]['isClosed']:
                    correctSelections.append(games[i]['home_team_details'].split(":")[0])
                    incorrectSelections.append(games[i]['away_team_details'].split(":")[0])
                elif games[i]['isClosed']:
                    correctSelections.append(games[i]['away_team_details'].split(":")[0])
                    incorrectSelections.append(games[i]['home_team_details'].split(":")[0])
                else:
                    print("Game has not yet concluded")
            for winner in correctSelections:
                if winner in userSelectionDisplay:
                    totalScore = totalScore + int(userSelectionDisplay[winner])
            groupSelectionDisplay[username] = {
                'selections': userSelectionDisplay,
                'score': totalScore
            }
            #print(groupSelectionDisplay.items())
        groupSelectionDisplay = sorted(groupSelectionDisplay.items(), key=lambda x: x[1]['score'], reverse=True)
        return render_template('weeklyleaguestats.html', name=current_user.name, games=[], userid=current_user.id, selections=[], selectionDisplay=json.dumps(groupSelectionDisplay), correctSelections=correctSelections, incorrectSelections=incorrectSelections, totalScore=totalScore, week=week, yearlyScoresDict={})
    else:
        return render_template('profile.html', name=current_user.name + ", you have not made any picks yet for week " + week + " please go make your selections", games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict={})

@main.route('/yearlyleaguestats')
@login_required
def yearlyleaguestats():
    userScores = db.session.query(User,Scores).filter(User.id==Scores.id).all()
    yearlyScoresDict = {}
    for userScore in userScores:
        yearlyScore = 0
        for weekNum in range(1,totalWeeks+1):
            yearlyScore = yearlyScore + int(getattr(userScore.Scores, "week" + str(weekNum) + "score"))
        yearlyScoresDict[userScore.User.name] = yearlyScore
    yearlyScoresDict = dict(sorted(yearlyScoresDict.items(), key=lambda x: x[1], reverse=True))
    return render_template('yearlyleaguestats.html', name=current_user.name, games=[], userid=current_user.id, selections=[], selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week, yearlyScoresDict=json.dumps(yearlyScoresDict))

