import os
import requests
import pymongo


from dotenv import load_dotenv
from flask import Flask, render_template, url_for, redirect
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

app = Flask(__name__)

app.secret_key = b"dsadsadsa"
# OAuth2 must make use of HTTPS in production environment.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"      # !! Only in development environment.

app.config["DISCORD_CLIENT_ID"] = 1296964599597240331
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("CLIENT_SECRET", "")
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"
app.config["DISCORD_BOT_TOKEN"] = os.getenv("TOKEN", "")


discord = DiscordOAuth2Session(app)


def mongo(db):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    return client[f"{db}"]

@app.route('/')
def index():
    reviews = get_revs()
    formatted_reviews = [
        {
            'pfpurl': get_pfp_url(rev.get('user_id')),
            'username': rev.get('username', 'Anonymous'),
            'user_id': rev.get('user_id'),
            'review': rev.get('review', 'No review available'),
            'rating': rev.get('stars', 'No rating')  # You can add more fields if needed
        }
        for rev in reviews
    ]

    return render_template('reviews.html', reviews=formatted_reviews)


def get_revs():
    db = mongo("reviews")
    collection = db["Reviews"]
    reviews = collection.find()
    return list(reviews)

def get_user(user_id):
    url = f"https://discord.com/api/v10/users/{user_id}"
    headers = {
        "Authorization": f"Bot {app.config['DISCORD_BOT_TOKEN']}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_pfp_url(user_id):
    user_data = get_user(user_id)

    if user_data:
        avatar_hash = user_data.get("avatar")
        discriminator = user_data.get("discriminator", "0000")

        if avatar_hash:
            return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
        else:
            return f"https://cdn.discordapp.com/embed/avatars/{int(discriminator) % 5}.png"
    return None

# @app.route('/reviews/')
# def show_review():
#     reviews = get_revs()
#     formatted_reviews = [
#         {
#             'pfpurl': get_pfp_url(rev.get('user_id')),
#             'username': rev.get('username', 'Anonymous'),
#             'user_id': rev.get('user_id'),
#             'review': rev.get('review', 'No review available'),
#             'rating': rev.get('stars', 'No rating')  # You can add more fields if needed
#         }
#         for rev in reviews
#     ]

#     return render_template('reviews.html', reviews=formatted_reviews)

@app.route('/dashboard/')
def dashboard():
    return "hello world"

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))


@app.route("/me/")
@requires_authorization
def me():
    user = discord.fetch_user()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>"""


if __name__ == "__main__":
    app.run(debug=True)