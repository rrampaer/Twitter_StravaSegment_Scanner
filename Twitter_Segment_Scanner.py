# coding: utf8
# This program (a scheduled task run from pythonanywhere.com ) scans for Strava (a popular running/cycling app) segment leaderboards changes.
# Everyday, it checks whether segment records have been broken, and tweet it if such was the case
# The "bot" also allows people to add segments to the "to-be-scanned" list by tweeting it the following:"@stravabrussels add [segmentid]"

import MySQLdb
import requests
import tweepy
import random

#Access codes and tokens - Insert your own
tokenBitly = Add yours
stravaAuth = Add yours
databaseHostAdress = Add yours
username = Add yours
pwd = Add yours
databaseName = Add yours
CONSUMER_KEY = Add yours
CONSUMER_SECRET = Add yours
ACCESS_KEY = Add yours
ACCESS_SECRET = Add yours

#Function to shorten URL
def shorten_url(longUrl):
    url="https://api-ssl.bitly.com/v3/shorten?access_token="+tokenBitly+"&longUrl="+longUrl
    b = requests.get(url)
    resp = b.json()
    shortUrl = resp["data"]["url"]
    return(shortUrl)

# Lists creation - Contain elements of tweets
nochange = ["No new leader today -_- #gogetit #strive #stravabrussels #stravarun", "No change today, are people getting slow? #strive #stravabrussels #stravarun", "Leaderboards are untouched and set to see another day #strive #stravabrussels #stravarun", "No segment record was beaten #MakeStravaFastAgain"]
middle = ["got himself a segment record", "gets on top of the segment leaderboard", "just beat a segment record"]
hashtags = ["#easyrun #strive #stravarun #stravabrussels", "#fastdontlie #strive #stravarun #stravabrussels", "#fastlife #strive #stravarun #stravabrussels", "#numeroUno #strive #stravarun #stravabrussels", "#beatyesterday #strive #stravarun #stravabrussels"]

#Establish connection with twitter API
auth = tweepy.OAuthHandler(CONSUMER_KEY,CONSUMER_SECRET )
auth.set_access_token(ACCESS_KEY,ACCESS_SECRET )
api = tweepy.API(auth)

#Establish connection with DB
conn = MySQLdb.connect(databaseHostAdress, username  ,pwd, databaseName)
c = conn.cursor()

#Get last version of (segment,leader) pairs in DB
c.execute("SELECT * FROM duo")
rows = c.fetchall()

#Create a list that will populated with changes to be made
changes = []

#GET request issued to Strava API - Checks, for each segment, whether leader has changed
for eachRow in rows:
    url = "https://www.strava.com/api/v3/segments/"+str(eachRow[0])+"/leaderboard"
    header = {"Authorization": stravaAuth}
    r = requests.get(url, headers=header)
    update = r.json()
    #Compare them with last DB version, capture changes
    if "entries" in update.keys():
        if len(update["entries"]) == 0:
            print("Can't find leaderboard for segment "+str(eachRow[0]))
        elif len(update["entries"]) > 0 :
            if update["entries"][0]["athlete_id"] == eachRow[1]:
                pass
            else:
                change = []
                change.append(eachRow[0])
                change.append(update["entries"][0]["athlete_name"])
                change.append(update["entries"][0]["athlete_id"])
                change.append(update["entries"][0]["elapsed_time"])
                change.append(update["entries"][0]["distance"])
                changes.append(change)
    else:
        print(update)
        raise SystemExit()

#DB UPDATE
for change in changes:
    c.execute("UPDATE duo SET leader=%s WHERE segment=%s",
               (change[1],change[0]))

#Actions depends whether segment leaders have changed or not
if len(changes) == 0:
    api.update_status(random.choice(nochange))
else:
    api.update_status("We have "+str(len(changes))+" new leader(s) today! #strive #gameon")
    for change in changes:
        firstName = change[1].split(" ",1)[0].decode('utf8', errors='ignore')
        segmentShortUrl = shorten_url("https://www.strava.com/segments/"+str(change[0]))

        #Generate a status with the different elements and tweet it
        status = firstName + " " + random.choice(middle)  + " " + segmentShortUrl + " " + random.choice(hashtags)
        api.update_status(status)

#Get id and time of last EOD tweet
id_yesterday =  api.search("StravaBotOutForToday")
try:
    for i in range(len(id_yesterday)):
        if id_yesterday[i].author.screen_name == "StravaBrussels":
            id = id_yesterday[i].text.split(' ')[4]
            time = id_yesterday[i].created_at
            break
except Exception as err:
    print(err)

#Add segments requested by users via tweet - "Tweet" = "@stravabrussels add [segmentid]"
requestedSegments =  api.search("%40stravabrussels")
if len(rows) + len(requestedSegments)<600:
    for tweet in requestedSegments:
        if tweet.text.split(' ')[1] == "add" and tweet.created_at > time:
            seg_to_check = tweet.text.split(' ')[2]
        #Twitter sometimes add a random space after the @user
        elif tweet.text.split(' ')[2] == "add" and tweet.created_at > time :
            seg_to_check = tweet.text.split(' ')[3]
        else:
            pass
        try:
            seg_to_add = int(seg_to_check)
            url = "https://www.strava.com/api/v3/segments/"+str(seg_to_check)+"/leaderboard"
            header = {"Authorization": stravaAuth}
            r = requests.get(url, headers=header)
            update = r.json()
            lead_to_add = update["entries"][0]["athlete_id"]
            c.execute("REPLACE INTO duo SET segment=%s, leader=%s",
           (seg_to_add,lead_to_add))
            api.update_status("The following segment was added for daily scan: "+shorten_url("https://www.strava.com/segments/"+str(seg_to_add))+" #gogetit #strive #stravabot")
            print("Added leader "+str(lead_to_add)+" for segment "+str(seg_to_add))
        except Exception as err:
            print("Error while grabbing leaderboard")
else:
    api.update_status("Could not add more segment because limit of 600 has been reached")

api.update_status("Request scanning of segments by tweeting \"@StravaBrussels add [segmentid]\"")
api.update_status("#StravaBotOutForToday last scan at "+str(time)+" UTC")
