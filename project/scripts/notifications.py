import os
import json
import requests
from twilio.rest import Client
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('YOUR_DATABASE')

metadata = MetaData(bind=None)

user = Table(
    'user',
    metadata,
    autoload=True,
    autoload_with=engine
)

scores = Table(
    'scores',
    metadata,
    autoload=True,
    autoload_with=engine
)


Session = sessionmaker(bind=engine)
session = Session()
users = session.query(user).all()
scores = session.query(scores).all()
userslist = []
scoreslist = []

for user in users:
    userslist.append(dict(user))
for score in scores:
    scoreslist.append(dict(score))

week = str(json.loads(requests.get("https://api.sportsdata.io/v3/cfb/scores/json/CurrentSeasonDetails?key=169d1d38eced4347897c7da9b81214a1").text)['ApiWeek'])

submittedUsers = []
textList = []
submittedNumbers = []

for score in scoreslist:
    if(score["week"+week+"picks"] is not None):
        submittedUsers.append(score["id"])

for user in userslist:
    if(user["id"] in submittedUsers and user["phonenumber"] is not None):
        submittedNumbers.append(user["phonenumber"])
    if(user["phonenumber"] is not None):
        textList.append(user["phonenumber"])

message_body_not_done = f"Our records indicate you have not yet submitted your picks for College Pickem Week {week} -- visit https://rjspickem.com/schedule/{week} and login to make your selections, good luck!"


message_body_done = f"Our records indicate you have already submitted your picks for College Pickem Week {week} -- thanks and good luck!"

# fetch below values here: https://console.twilio.com/?frameUrl=%2Fconsole%3Fx-target-region%3Dus1
account_sid = 'YOUR_TWILIO_SID'
auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
client = Client(account_sid, auth_token)

for user in textList:
    if user not in submittedNumbers:
        messagetext=message_body_not_done
        message = client.messages \
            .create(
	            body=messagetext,
	            from_='+15034617975',
	            to=f"+1{user}",
	        )
        print("Successfully sent message")
        print(user)
        print(message.sid)
        print(messagetext)
    else:
        print(user)
        print("User has submitted, doing nothing")
