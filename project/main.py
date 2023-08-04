from flask import Blueprint, render_template, Flask, request, redirect, url_for, render_template_string
from flask_login import login_required, current_user
from .ncaa.lib.ncaa import NCAAAPI
from .models import User, Scores, Adminselections
from datetime import datetime
from . import db
import requests
import json
import os
import traceback

main = Blueprint('main', __name__)

ncaa_api_client = NCAAAPI()

week = ncaa_api_client.get_current_week()
year = 2023
totalWeeks=13

@main.route('/')
def index():
    games=[]
    return render_template('index.html', week=week)

@main.route('/admin/<week>')
@login_required
def admin(week):
    games=ncaa_api_client.get_weekly_matchups(year, week)
    if current_user.admin == 0:
        return render_template('failedadmin.html', name=current_user.name)
    else:
        return render_template('admin.html', name=current_user.name, games=games, week=week, weekText="Game Options for week " + week)


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name, week=week)


@main.route('/myscores/<week>')
@login_required
def myscores(week):
    try:
        data =  getattr(Adminselections.query.filter_by(year=year).first(), "week" + week).split(',')
    except:
        return render_template('myscores.html', name=str(current_user.name), message="You have not made any picks yet for week " + week + " please go make your selections", selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week)
    if data is not None:
        games=ncaa_api_client.get_weekly_matchups(year, week, data)
    else:
        return render_template('myscores.html', name=str(current_user.name), message="You have not made any picks yet for week " + week + " please go make your selections", selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week)
    picks=getattr(Scores.query.filter_by(id=current_user.id).first(), "week" + week + "picks")

    orderedGameNames = {}
    for game in games:
        orderedGameNames[game['home_team_details'].split(':')[0]] = game['kickoff']
        orderedGameNames[game['away_team_details'].split(':')[0]] = game['kickoff']

    if picks is not None:
        correctSelections=[]
        incorrectSelections=[]
        selectionDisplay={}
        selectionDisplayParsed={}
        totalScore = 0
        picks = json.loads(picks)
        for pick in picks:
            for selection in pick.keys():
                team = ""
                points = pick[selection]["confidence"]
                if pick[selection]["selection"] == "1":
                    for game in games:
                        if str(selection) == str(game["game_id"]):
                            team = game["home_team_details"].split(":")[0]
                else:
                    for game in games:
                        if str(selection) == str(game["game_id"]):
                            team = game["away_team_details"].split(":")[0]
                selectionDisplay[team] = points
        for i in range(len(games)):
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
        for team in orderedGameNames.keys():
            if team in selectionDisplay.keys():
                selectionDisplayParsed[team] = selectionDisplay[team]
        return render_template('myscores.html', message="", name=current_user.name, selectionDisplay=json.dumps(selectionDisplayParsed), correctSelections=correctSelections, incorrectSelections=incorrectSelections, totalScore=totalScore, week=week)
    else:
        return render_template('myscores.html', message="You have not made any picks yet for week " + week + " please go make your selections", name=current_user.name, selectionDisplay=[], correctSelections=[], incorrectSelections=[], totalScore=0, week=week)

@main.route('/schedule/<week>')
@login_required
def schedule(week):
    try:
        data =  getattr(Adminselections.query.filter_by(year=year).first(), "week" + week).split(',')
        games=ncaa_api_client.get_weekly_matchups(year, week, data)
        userSelectedScores = getattr(Scores.query.filter_by(id=current_user.id).first(), "week" + week + "picks")
        print
        return render_template('schedule.html', message="", games=games, userid=current_user.id, selections=userSelectedScores, week=week, isAdmin=current_user.admin)
    except:
        return render_template('schedule.html', message="Game choices for week " + week + " have not been chosen by an admin yet, please check back later", games=[], userid=current_user.id, selections=[], week=week, isAdmin=current_user.admin)

@main.route('/admin_adjust')
@login_required
def admin_select_user():
    users=User.query.all()
    userList = []
    for user in users:
        userList.append({user.name:user.id})
    return render_template('adminadjust.html', name=current_user.name, userList=json.dumps(userList), week=week)


@main.route('/admin_adjust/<week>/<user_id>', methods=['POST'])
@login_required
def admin_adjust_picks(week, user_id):
    if current_user.admin == 0:
        return render_template('failedadmin.html', name=current_user.name)
    else:
        try:
            data =  getattr(Adminselections.query.filter_by(year=year).first(), "week" + week).split(',')
            games=ncaa_api_client.get_weekly_matchups(year, week, data)
            userSelectedScores = getattr(Scores.query.filter_by(id=user_id).first(), "week" + week + "picks")
            return render_template('schedule.html', message="", games=games, userid=user_id, selections=userSelectedScores, week=week, isAdmin=1)
        except:
            return render_template('schedule.html', message="Game choices for week " + week + " have not been chosen by an admin yet, please check back later", games=[], userid=current_user.id, selections=[], week=week, isAdmin=1)


@main.route('/submitpicks/<week>/<user_id>', methods=['POST'])
@login_required
def submit_picks(week, user_id):
    if str(user_id) != str(current_user.id) and current_user.admin == 0:
        return render_template('failedadmin.html', name=current_user.name)
    else:
        scores = Scores.query.filter_by(id=user_id).first()
        args = request.args
        setattr(scores, "week" + week + "picks", str(args.get("picks")))
        db.session.commit()
        return redirect(f"/myscores/{week}")

@main.route('/selectweeklygames/<week>', methods=['POST'])
@login_required
def select_games(week):
    args = request.args
    adminSelections = Adminselections.query.filter_by(year=year).first()
    setattr(adminSelections, "week" + week, str(args.get("selections")))
    db.session.commit()
    return redirect(url_for('main.profile'))

@main.route('/weeklyleaguestats/<week>')
@login_required
def weeklyleaguestats(week):
    try:
        data =  getattr(Adminselections.query.filter_by(year=year).first(), "week" + week).split(',')
    except:
        return render_template('weeklyleaguestats.html', message="An error occurred loading all other teams picks, please reachout to an admin", selectionDisplay=[], correctSelections=[], incorrectSelections=[], week=week)
    if data is not None:
        games=ncaa_api_client.get_weekly_matchups(year, week, data)
    else:
        return render_template('weeklyleaguestats.html', message="An error occurred loading all other teams picks, please reachout to an admin", selectionDisplay=[], correctSelections=[], incorrectSelections=[], week=week)

    for game in range(len(games)):
        if datetime.strptime(games[0]['kickoff'], '%Y-%m-%dT%H:%M:%S') < datetime.now():
            break
        return render_template('weeklyleaguestats.html', message="Games for week " + week + " have not started yet, please check back after the first game kicks off", selectionDisplay=[], correctSelections=[], incorrectSelections=[], week=week)

    allPicks=db.session.query(User,Scores).filter(User.id==Scores.id).all()
    groupSelectionDisplay={}
    orderedGameNames = {}
    for game in games:
        orderedGameNames[game['home_team_details'].split(':')[0]] = game['kickoff']
        orderedGameNames[game['away_team_details'].split(':')[0]] = game['kickoff']

    correctSelections=[]
    incorrectSelections=[]
    for i in range(len(games)):
        if int(games[i]['home_team_details'].split(":")[1]) > int(games[i]['away_team_details'].split(":")[1]) and games[i]['isClosed']:
            correctSelections.append(games[i]['home_team_details'].split(":")[0])
            incorrectSelections.append(games[i]['away_team_details'].split(":")[0])
        elif games[i]['isClosed']:
            correctSelections.append(games[i]['away_team_details'].split(":")[0])
            incorrectSelections.append(games[i]['home_team_details'].split(":")[0])
        else:
            print("Game has not yet concluded")

    if allPicks is not None:
        for picks in allPicks:
            username = picks.User.name
            userid = picks.User.id
            totalScore = 0
            userSelectionDisplay={}
            userSelectionDisplayParsed={}
            picks = getattr(picks.Scores, "week" + week + "picks")
            if picks is None:
                groupSelectionDisplay[username] = {
                    'selections': {},
                    'score': 0
                }
                continue
            picks = json.loads(picks)
            for pick in picks:
                for selection in pick.keys():
                    team = ""
                    points = pick[selection]["confidence"]
                    if pick[selection]["selection"] == "1":
                        for game in games:
                            if str(selection) == str(game["game_id"]):
                                team = game["home_team_details"].split(":")[0]
                    else:
                        for game in games:
                            if str(selection) == str(game["game_id"]):
                                team = game["away_team_details"].split(":")[0]
                    userSelectionDisplay[team] = points

            for team in orderedGameNames.keys():
                if team in userSelectionDisplay.keys():
                    userSelectionDisplayParsed[team] = userSelectionDisplay[team]
            for winner in correctSelections:
                if winner in userSelectionDisplay:
                    totalScore = totalScore + int(userSelectionDisplay[winner])
            groupSelectionDisplay[username] = {
                'selections': userSelectionDisplayParsed,
                'score': totalScore
            }
            # Update all users scores
            scores = Scores.query.filter_by(id=userid).first()
            setattr(scores, "week" + week + "score", str(totalScore))
            db.session.commit()
        groupSelectionDisplay = sorted(groupSelectionDisplay.items(), key=lambda x: x[1]['score'], reverse=True)
        return render_template('weeklyleaguestats.html', message="", selectionDisplay=json.dumps(groupSelectionDisplay), correctSelections=correctSelections, incorrectSelections=incorrectSelections, week=week)
    else:
        return render_template('weeklyleaguestats.html', message="You have not made any picks yet for week " + week + " please go make your selections", correctSelections=[], incorrectSelections=[], week=week)

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
    return render_template('yearlyleaguestats.html', message="", yearlyScoresDict=json.dumps(yearlyScoresDict), week=week)

@main.route('/emailformsubmit')
@login_required
def emailformsubmit():
    return render_template('emailformsubmit.html')
