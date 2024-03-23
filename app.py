
import os
import pymongo
import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from bson import ObjectId
from flask_mail import Mail, Message
import random
import string
import secrets
from datetime import timedelta


# Load environment variables from .env file
load_dotenv()


# Define a function to create and configure the Flask app
def create_app():
    # Initialize Flask app
    app = Flask(__name__, template_folder='templates')

    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')


    # Initialize Flask-Mail
    mail = Mail(app)

    # MongoDB connection
    app.secret_key = os.getenv('SECRET_KEY')  # Set secret key for session management
    MONGO_URI = os.getenv('MONGO_URI')
    client = MongoClient(MONGO_URI)
    db = client['filmflix']
    film_collection = db['films']
    users = db['users']
    password_resets = db['password_resets']
    verification_codes_collection = db['verification_codes']


    # Initialize Flask-Session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    Session(app)

    # Configure rate limiting
    limiter = Limiter(app, default_limits=["5 per minute"])


    # Initialize Argon2 password hasher
    ph = PasswordHasher()

    # Classes

    # Define login form
    class LoginForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired(), Email()])
        password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
        submit = SubmitField('Login')

    # Define registration form
    class RegistrationForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired(), Email()])
        password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8)])
        submit = SubmitField('Register')
        
        
    # Define forgot password form
    class ForgotPasswordForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired(), Email()])
        submit = SubmitField('Submit')

    # Define verification form 
    class VerifyCodeForm(FlaskForm):
        verification_code = StringField('Verification Code', validators=[DataRequired()])
        submit = SubmitField('Submit')

    # Casing

    def title_case(text):
        lowercase_words = ['a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'yet', 'so','of', 'at', 'by', 'in', 'on', 'to', 'with', 'as', 'because', 'although',
        'since', 'while', 'if', 'when', 'where', 'whether', 'after', 'before']
        
        # Split the text into words
        words = text.split()
        
        # Capitalize the first letter of each word, unless it's in the list of lowercase words
        title_case_words = [word.capitalize() if word.lower() not in lowercase_words else word.lower() for word in words]
        
        # Join the title-cased words back into a string
        title_case_text = ' '.join(title_case_words)
        
        return title_case_text

    # Verification

    # Define a function to generate a verification code
    def generate_verification_code():
        # Generate a random verification code
        return secrets.token_hex(4)  # Generate a 4-byte (8-character) hexadecimal token


    # Insert verification code into MongoDB
    def insert_verification_code(email, verification_code,expiration_timestamp):
        verification_code = generate_verification_code()  # Generate a verification code
        verification_codes_collection.insert_one({
            'email': email,
            'verification_code': verification_code,
            'expiration_timestamp': expiration_timestamp
        })



    # Retrieve verification code from MongoDB
    def get_verification_code(email):
        return db.verification_codes_collection.find_one({'email': email})

    # Delete verification code from MongoDB
    def delete_verification_code(email):
        db.verification_codes_collection.delete_one({'email': email})


    # Restrictions on deletion/addition/modification

    MAX_ADDITIONS = 3
    MAX_MODIFICATIONS = 3
    MAX_DELETIONS = 3

    # Counter variables to keep track of the number of additions, modifications, and deletions
    additions_count = 0
    modifications_count = 0
    deletions_count = 0




    # Login form
    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("3 per minute")
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            try:
                # Verify password
                user = db.users.find_one({'email': email})
                if user and ph.verify(user['password'], password):
                    # Reset login attempt count on successful login
                    session['login_attempts'] = 0
                    session['email'] = email
                    return redirect(url_for('admin'))
                else:
                    # Increment login attempt count
                    session.setdefault('login_attempts', 0)
                    session['login_attempts'] += 1

                    # Display error message for incorrect password
                    flash('Incorrect email or password. Please try again.')

                    # Check login attempt count
                    if session['login_attempts'] >= 3:
                        # Redirect to password reset page after 3 failed attempts
                        return redirect(url_for('reset_password'))

            except VerifyMismatchError:
                # Display error message for incorrect password
                flash('Incorrect email or password. Please try again.')

        return render_template('login.html', form=form, error=form.errors)


    # Log out
    @app.route('/logout')
    def logout():
        # Clear the session data
        session.clear()
        # Redirect the user to the homepage or any other desired page after logout
        return redirect(url_for('admin'))


    # Updated Registration Route
    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("1 per day")
    def register():
        form = RegistrationForm()  # Assuming RegistrationForm is imported and defined correctly

        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            
        # Generate verification code
            verification_code = secrets.token_urlsafe(16) 

            # Check if the email already exists in the database
            existing_user = users.find_one({'email': email})
            if existing_user:
                flash('Email address is already registered.', 'error')
                return redirect(url_for('register'))

            # Hash the password using Argon2
            hashed_password = ph.hash(password)

            # Store the email and hashed password in the database
            db.users.insert_one({'email': email, 'password': hashed_password})
            
            # Send verification email
            send_verification_email(email, verification_code)

            # Redirect to a success page or perform additional actions
            flash('Registration successful! A verification email has been sent to your email address.', 'success')
            return redirect(url_for('login'))

        # If the form is not submitted or validation fails, render the registration form
        return render_template('register.html', form=form, error=form.errors)





    # Forgot password route 
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            email = form.email.data
            user = db.users.find_one({'email': email})
            if user:
                # Generate unique token
                token = secrets.token_hex(16)
                
                # Store token in the database
                db.password_resets.insert_one({'email': email, 'token': token, 'timestamp': datetime.datetime.now()})
                
                # Send reset password email
                reset_link = url_for('reset_password', token=token, _external=True)
                msg = Message('FilmFlix Password Reset', recipients=[email])
                msg.body = f'Click the following link to reset your password: {reset_link}'
                mail.send(msg)
                
                flash('An email has been sent with instructions to reset your password.')
                return redirect(url_for('login'))
            else:
                flash('Email address not found.')
        return render_template('forgot_password.html', form=form)




    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        reset = db.password_resets.find_one({'token': token})
        if reset:
            if request.method == 'POST':
                new_password = request.form['new_password']
                confirm_password = request.form['confirm_password']
                
                if new_password != confirm_password:
                    flash('Passwords do not match.')
                    return redirect(url_for('reset_password', token=token))
                
                # Hash the new password using Argon2
                hashed_password = ph.hash(new_password)
                
                # Update user's password in the database with the hashed password
                db.users.update_one({'email': reset['email']}, {'$set': {'password': hashed_password}})
                
                # Delete token from the password_resets collection
                db.password_resets.delete_one({'token': token})
                
                flash('Your password has been successfully reset. You can now login with your new password.')
                return redirect(url_for('login'))
            else:
                # Render the password reset form
                return render_template('reset_password.html', token=token)
        else:
            flash('Invalid or expired token.')
            return redirect(url_for('forgot_password'))



    # Verification
    @app.route('/verify/<email>/<verification_code>')
    def verify_email(email, verification_code):
        # Check if the verification code is valid
        user = db.users_collection.find_one({'email': email, 'verification_code': verification_code})
        if user:
            # Remove the verification code from the database
            db.users_collection.update_one({'email': email}, {'$unset': {'verification_code': 1}})
            flash('Your email has been verified. You can now login.')
        else:
            flash('Invalid verification code.')
        return redirect(url_for('login'))




    # Main site get films. Search.
    @app.route('/')
    def index():
        # Retrieve all films from the database
        films = list(film_collection.find())
        return render_template('index.html', films=films)

    @app.route('/films', methods=['GET'])
    def get_films():
        # Get filter parameters from request
        genre = request.args.get('genre')
        year_released = request.args.get('yearReleased')
        rating = request.args.get('rating')
        title = request.args.get('title')

        # Construct query based on filter parameters
        query = {}
        if title:
            query['title'] = {"$regex": title, "$options": "i"}  # Case-insensitive search for rating
        if genre:
            query['genre'] = {"$regex": genre, "$options": "i"}  # Case-insensitive search for genre
        if year_released:
            query['yearReleased'] = int(year_released)
        if rating:
            query['rating'] = {"$regex": rating, "$options": "i"}  # Case-insensitive search for rating

        # Query MongoDB collection
        films = list(film_collection.find(query))
        
        # Get the count of films found
        num_films_found = len(films)

        
        return render_template('index.html', films=films, num_films_found=num_films_found)

        

    # Admin area, CRUD.
    @app.route('/admin')
    def admin():
        total_films = film_collection.count_documents({})

        # Retrieve all films from the database
        films = list(film_collection.find())
        return render_template('admin.html', films=films, total_films=total_films)

    @app.route('/add_film', methods=['POST'])
    def add_film():
        
        global additions_count
        if additions_count >= MAX_ADDITIONS:
            flash('You have reached the maximum limit for adding films.', 'error')
            return redirect(url_for('admin'))
        
        # Increment the additions count
        additions_count += 1
        
        # Generate the next filmID
        next_film_id = get_next_film_id()
        
        # Get form data
        title = title_case(request.form['title'])
        genre = title_case(request.form['genre'])
        rating = request.form['rating']
        poster = request.form['poster']
        year_released = int(request.form['yearReleased'])
        duration = int(request.form['duration'])

        
        # Insert new film into the database
        db.films.insert_one({
            'filmID': next_film_id,
            'title': title,
            'genre': genre,
            'yearReleased': year_released,
            'rating': rating,
            'duration': duration,
            'poster': poster
        })
        flash('Film added successfully!', 'success')
        return redirect(url_for('admin'))

    @app.route('/modify_film/<film_id>', methods=['POST'])
    def modify_film(film_id):
        
        global modifications_count
        if modifications_count >= MAX_MODIFICATIONS:
            flash('You have reached the maximum limit for modifying films.', 'error')
            return redirect(url_for('admin'))
        
        # Increment the modifications count
        modifications_count += 1
        
        new_poster = request.form['poster']
        new_title = title_case(request.form['title'])
        new_genre = title_case(request.form['genre'])
        new_rating = request.form['rating']
        # Convert yearReleased and duration to numbers
        new_year_released = int(request.form['yearReleased'])
        new_duration = int(request.form['duration'])

        
        # Retrieve the last filmID from the database
        last_film = db.films.find_one({}, sort=[("filmID", pymongo.DESCENDING)])
        if last_film:
            last_film_id = last_film.get("filmID", 0)
            next_film_id = last_film_id + 1
        else:
            next_film_id = 1  # If no films exist, start from 1

        # Update the film in the database with the new data
        db.films.update_one({'_id': ObjectId(film_id)}, {'$set': {'filmID': next_film_id, 'title': new_title, 'genre': new_genre, 'yearReleased': new_year_released, 'rating': new_rating, 'duration': new_duration, 'poster': new_poster}})
        
        flash('Film modified successfully!', 'success')
        return redirect(url_for('admin'))

    def get_next_film_id():
        last_film = db.films.find_one({}, sort=[("filmID", pymongo.DESCENDING)])
        if last_film:
            last_film_id = last_film.get("filmID", 0)
            return last_film_id + 1
        else:
            return 1  # If no films exist, start from 1



    @app.route('/delete_film/<film_id>', methods=['POST'])
    def delete_film(film_id):
        
        global deletions_count
        if deletions_count >= MAX_DELETIONS:
            flash('You have reached the maximum limit for deleting films.', 'error')
            return redirect(url_for('admin'))
        
        # Increment the deletions count
        deletions_count += 1
        
        # Convert film_id to ObjectId
        film_id = ObjectId(film_id)

        # Query the database to find the film by its ID and delete it
        result = db.films.delete_one({'_id': film_id})

    # Check if the film was successfully deleted
        if result.deleted_count == 1:
            flash('Film deleted successfully!', 'success')
        else:
            flash('Film not found or deletion failed', 'error')

        return redirect(url_for('admin'))


    # Email
    # Send verification email function
    def send_verification_email(email, verification_code):
        msg = Message('Verify Your Email', recipients=[email])
        msg.body = f'Click the following link to verify your email: {url_for("verify_email", email=email, verification_code=verification_code, _external=True)}'
        mail.send(msg)

    # Email reset
    def send_reset_password_email(user_email, reset_token):
        # Compose the email message
        subject = "Password Reset Request"
        sender = "FilmFlix"
        recipient = user_email
        reset_link = url_for('reset_password', token=reset_token, _external=True)  # Assuming route name is reset_password
        body = f"You have requested to reset your password. Please click on the following link to reset your password:\n\n{reset_link}\n\nIf you did not request this change, please ignore this email.\n\nHave a great day!\nFilmFlix Team"

        # Send the email
        msg = Message(subject, sender=sender, recipients=[recipient])
        msg.body = body
        mail.send(msg)


    return app

# Run the app if executed directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)