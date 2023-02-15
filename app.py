import os
from functools import wraps
from random import random

from flask import Flask, jsonify, render_template, session, redirect

import json
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for

from controller.database import Database

app = Flask(__name__)
app.database = Database()
app.secret_key = os.environ['FLASK_SECRET']
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.environ["AUTH0_CLIENT_ID"],
    client_secret=os.environ["AUTH0_CLIENT_SECRET"],
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ["AUTH0_DOMAIN"]}/.well-known/openid-configuration'
)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            print(f"Missing profile because session is {session} ")
            # Redirect to Login page here
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated


@app.route('/api/fact')
def getFact():
    return jsonify(id=3, author="xd", text="lol")


@app.route('/')
def hello():
    return render_template('hello.html', session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route('/secret')
@requires_auth
def secret():
    return render_template('secret.html', secret='sauce')


## START AUTH0 SAMPLE


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    session["picture"] = token['userinfo']['picture']
    result = app.database.recordLogin(token['userinfo']['email'])
    if result is None:
        return redirect('/newUser')
    else:
        return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + os.environ["AUTH0_DOMAIN"]
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("hello", _external=True),
                "client_id": os.environ["AUTH0_CLIENT_ID"],
            },
            quote_via=quote_plus,
        )
    )


@app.route('/newUser')
def newUser():
    return render_template('info.html')
