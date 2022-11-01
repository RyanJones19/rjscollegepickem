import os
import json
import requests
from twilio.rest import Client
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

engine = create_engine('DB_CONNECTION_STRING')

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

week = str(json.loads(requests.get("https://api.sportsdata.io/v3/cfb/scores/json/CurrentSeasonDetails?key=1cad9502a7fb41309dd027faa659317f").text)['ApiWeek'])

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

message_body_not_done = f"Our records indicate you have not yet submitted your picks for College Pickem Week {week} -- visit http://testcomms-1812807762.us-west-2.elb.amazonaws.com/schedule/{week} and login to make your selections, good luck!"


message_body_done = f"Our records indicate you have already submitted your picks for College Pickem Week {week} -- thanks and good luck!"

account_sid = 'ACb8b4d121c8196cb8d5fbe8ceaa234eb0'
auth_token = '36f3731f9f389c9175c4015148c7b04f'
client = Client(account_sid, auth_token)

for user in textList:
    if user in submittedNumbers:
        messagetext=message_body_done
    else:
        messagetext=message_body_not_done
    message = client.messages \
        .create(
	body=messagetext,
	from_='+15034617975',
	to=f"+1{user}",
	)
    print("Successfully sent message")
    print(message.sid)
    print(messagetext)