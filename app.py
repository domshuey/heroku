from flask_bcrypt import Bcrypt
from flask import Flask, request, redirect, render_template, flash, get_flashed_messages, session
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from models import User, connect_db, db, Tweet
from forms import UserForm, TweetForm
from psycopg2 import connect
from sqlalchemy.exc import IntegrityError

# app setups
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hashing"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = 'abc123'
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

# other setups
toolbar = DebugToolbarExtension(app)
bcrypt = Bcrypt()
connect_db(app)



# routes

@app.route('/')
def show_home():
    tweets = Tweet.query.all()
    return render_template('home.html', tweets=tweets)

@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        new_user = User.register(username, password)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username already in use.')
            return render_template('signup.html', form=form)
        session['user_id'] = new_user.id
        flash('Successfully created account!', 'success')
        return redirect('/tweets')
    return render_template('signup.html', form=form)

@app.route('/tweets', methods=["GET", "POST"])
def show_tweets():
    if 'user_id' not in session:
        flash('Please login first','danger')
        return redirect('/login')

    form = TweetForm()
    all_tweets = Tweet.query.all()

    if form.validate_on_submit():
        text = form.text.data
        # user = session['user_id']
        new_tweet = Tweet(text=text, user_id=session['user_id'])
        db.session.add(new_tweet)
        db.session.commit()
        form.text.data = ''
        flash('Tweet created!', 'info')
        return redirect('/tweets')
    return render_template('tweets.html', form=form, tweets=all_tweets)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            flash(f'Welcome back, {user.username}!', 'primary')
            session['user_id'] = user.id
            return redirect('/tweets')
        else:
            form.username.errors = ['Invalid username/password']
    return render_template('login.html', form=form)

@app.route('/tweets/<int:id>', methods=['POST'])
def delete_tweet(id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/tweets')
    tweet = Tweet.query.get_or_404(id)
    if tweet.user.id == session["user_id"]:
        db.session.delete(tweet)
        db.session.commit()
        flash("tweet deleted.", 'success')
        return redirect('/tweets')
    flash('You do not have authorization to delete tweet.', 'danger')
    return redirect('/tweets')


@app.route('/logout')
def log_out():
    flash('Goodbye', 'primary')
    session.pop('user_id')
    return redirect('/')