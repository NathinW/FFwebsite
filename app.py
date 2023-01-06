from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import requests
import urllib
from statistics import mean


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'mysql.2021.lakeside-cs.org'
app.config['MYSQL_USER'] = 'student2021'
app.config['MYSQL_PASSWORD'] = 'm545CS42021'
app.config['MYSQL_DB'] = '2021project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

#displays the original page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/error')
def scoreinfo():
    return render_template('error.html')

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    cursor = mysql.connection.cursor()
    query = 'SELECT * FROM nathinwilliams_leaderboard'
    cursor.execute(query)
    mysql.connection.commit()
    data = cursor.fetchall()
    return render_template('leaderboard.html', data=data)

#displays the results webpage
@app.route('/results', methods=['POST'])
def results():
    playerName = request.form.get("playerName")
    response = requests.get("https://api.pushshift.io/reddit/search/submission/?q=" + playerName + "&subreddit=fantasyfootball&after=3d&sort_type=score&sort=desc&size=25")
    jsonResponse = response.json()
    allData = jsonResponse["data"]
    print(allData)
    if allData == []:
        return render_template('error.html')
    else:
        content = organizeContent(allData)
        titles = organizeTitles(allData)
        scores = (organizeScores(allData))
        avgScore = round(mean(scores))

        cur = mysql.connection.cursor()
        query = "SELECT * FROM `nathinwilliams_leaderboard` WHERE `PlayerName` = %s"
        queryVars = (playerName,)
        cur.execute(query, queryVars);
        results = cur.fetchall()
        print(results)
        mysql.connection.commit()

        if results == ():
            cur = mysql.connection.cursor()
            query = "INSERT INTO nathinwilliams_leaderboard (PlayerName, PlayerScore, Searches) VALUES (%s, %s, 1);"
            queryVars = (playerName, avgScore,)
            cur.execute(query, queryVars);
            mysql.connection.commit()
        else:
            cur = mysql.connection.cursor()
            query = "UPDATE `nathinwilliams_leaderboard` SET `Searches`= Searches + 1 WHERE `PlayerName` = %s"
            queryVars = (playerName,)
            cur.execute(query, queryVars);
            mysql.connection.commit()

    return render_template('results.html', content=content, titles=titles, player=playerName, scores=scores, avg=avgScore)


def organizeContent(data):
    content = []
    for post in data:
        try:
            content.append(post["selftext"])
        except KeyError:
            content.append("")
    return content

def organizeTitles(data):
    titles = []
    for post in data:
        titles.append(post["title"])
    return titles

def organizeScores(data):
    scores = []
    for post in data:
        scores.append(round(100*analyze_sentiment(post["title"])))
    return scores


#Source: https://rapidapi.com/japerk/api/text-processing
def analyze_sentiment(words):
    url = "https://japerk-text-processing.p.rapidapi.com/sentiment/"
    encoded_url = urllib.parse.quote(words)
    payload = "language=english&text=" + encoded_url
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'x-rapidapi-key': "951a23d053msh7176dd1a27a9e70p138d36jsnd7835cd12b34",
        'x-rapidapi-host': "japerk-text-processing.p.rapidapi.com"
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    jsonResponse = response.json()
    allData = jsonResponse["probability"]

    return allData["pos"]
