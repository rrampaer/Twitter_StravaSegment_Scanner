# coding: utf8
# This program (a scheduled task run from pythonanywhere.com ) scans for Strava (a popular running/cycling app) segment leaderboards changes.
# Everyday, it checks whether segment records have been broken, and tweet if such was the case
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

# Lists creation - Contain elements of tweets
nochange = ["No new leader today -_- #gogetit #strive #stravabrussels #stravarun",
            "No change today, are people getting slow? #strive #stravabrussels #stravarun",
            "Leaderboards are untouched and set to see another day #strive #stravabrussels #stravarun",
            "No segment record was beaten #MakeStravaFastAgain"]
middle = ["got himself a segment record",
          "gets on top of the segment leaderboard",
          "just beat a segment record"]
hashtags = ["#easyrun #strive #stravarun #stravabrussels",
            "#fastdontlie #strive #stravarun #stravabrussels",
            "#fastlife #strive #stravarun #stravabrussels",
            "#numeroUno #strive #stravarun #stravabrussels",
            "#beatyesterday #strive #stravarun #stravabrussels"]

#URL shortening is crucial given twitter 140 characters restriction
def shorten_url(longUrl):
    url="https://api-ssl.bitly.com/v3/shorten?access_token="+tokenBitly+"&longUrl="+longUrl
    b = requests.get(url)
    resp = b.json()
    shortUrl = resp["data"]["url"]
    return(shortUrl)

def connect_to_twitter_api():
    auth = tweepy.OAuthHandler(CONSUMER_KEY,CONSUMER_SECRET )
    auth.set_access_token(ACCESS_KEY,ACCESS_SECRET )
    return (tweepy.API(auth))

def connect_to_db():
    conn = MySQLdb.connect(databaseHostAdress, username  ,pwd, databaseName)
    return(conn.cursor())

# duo is a table with a column segment and a column leader
def get_last_pairs():
    c.execute("SELECT * FROM duo")
    return(c.fetchall())

def get_changed_leaders(rows):
    changes = []
    for eachRow in rows:
        url = "https://www.strava.com/api/v3/segments/"+str(eachRow[0])+"/leaderboard"
        header = {"Authorization": stravaAuth}
        r = requests.get(url, headers=header)
        update = r.json()
        #Compare them with last DB version, capture changes
        if "entries" not in update.keys():
            print(update)
            raise SystemExit()
            
        elif not update["entries"]:
            print("Can't find leaderboard for segment "+str(eachRow[0]))

        elif update["entries"][0]["athlete_id"] == eachRow[1]:
            pass

        else:
            change = []
            change.append(eachRow[0])
            change.append(update["entries"][0]["athlete_name"])
            change.append(update["entries"][0]["athlete_id"])
            change.append(update["entries"][0]["elapsed_time"])
            change.append(update["entries"][0]["distance"])
            changes.append(change)
    return(changes)

def update_database(c,changes):
    for change in changes:
        c.execute("UPDATE duo SET leader=%s WHERE segment=%s",
            (change[1],change[2]))

def tweet_changes(changes, api):
    if not changes:
        api.update_status(random.choice(nochange))
    else:
        api.update_status("We have "+str(len(changes))+" new leader(s) today! #strive #gameon")
        for change in changes:
            firstName = change[1].split(" ",1)[0].decode('utf8', errors='ignore')
            segmentShortUrl = shorten_url("https://www.strava.com/segments/"+str(change[0]))

            #Generate a status with the different elements and tweet it
            status = firstName + " " + random.choice(middle)  + " " + segmentShortUrl + " " + random.choice(hashtags)
            api.update_status(status)

def get_last_tweet(api):
    id_yesterday =  api.search("StravaBotOutForToday")
    try:
        for entry in id_yesterday:
            if entry.author.screen.name = "StravaBrussels":
                time_ = entry.created_at
                break        
    except AttributeError as err:
        print(err)
    return (time_)

def add_requested_segments(api, rows, time_):
    requestedSegments =  api.search("%40stravabrussels")
    if len(rows) + len(requestedSegments)<600:
        for tweet in requestedSegments:
            if tweet.text.split(' ')[1] == "add" and tweet.created_at > time_:
                seg_to_check = tweet.text.split(' ')[2]
            #Twitter sometimes add a random space after the @user
            elif tweet.text.split(' ')[2] == "add" and tweet.created_at > time_ :
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

def close_the_day(api, time_):
    api.update_status("Request scanning of segments by tweeting \"@StravaBrussels add [segmentid]\"")
    api.update_status("#StravaBotOutForToday last scan at "+str(time_)+" UTC")


def main() :
    api = connect_to_twitter_api()
    c = connect_to_db()
    rows = get_last_pairs()
    changes = get_changed_leaders(rows)
    update_database(c,changes)
    tweet_changes(changes, api)
    lastTime = get_last_tweet(api)
    add_requested_segments(api, rows, lastTime)
    close_the_day(api, lastTime)
    conn.commit()
      
if __name__ == "__main__":
    main()
