import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from bson import ObjectId
from flask_mail import Mail, Message
import secrets
import logging
from logging.handlers import RotatingFileHandler
from forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetForm
logging.basicConfig(level=logging.DEBUG)
from core import limiter, Limiter





# Load environment variables from .env file
load_dotenv()

# Define a function to create and configure the Flask app
def create_app():
    # Initialize Flask app
    app = Flask(__name__, template_folder='templates', static_folder='static')

    limiter.init_app(app)

    # Configure logging
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

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
    

    # Initialize Flask-Session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    Session(app)



    # Initialize Argon2 password hasher with custom parameters
    ph = PasswordHasher(time_cost=2, memory_cost=512000)  # Adjust parameters as needed


    # Verification
    # Define a function to generate a verification code
    def generate_verification_code():
        return secrets.token_hex(4)
    
    # Define function for expiration
    def expiration_timestamp():
        expiration_duration = datetime.timedelta(hours=24)
        # Calculate expiration timestamp
        return datetime.datetime.now() + expiration_duration

    # Insert verification code into MongoDB
    def insert_verification_code(email, hashed_password, verification_code, expiration_time):
        #verification_code = generate_verification_code()
        users.insert_one({
            'email': email,
            'password': hashed_password,
            'verification_code': verification_code,
            'expiration_timestamp': expiration_time
        })

    # Retrieve verification code from MongoDB
    def get_verification_code(email):
        return users.find_one({'email': email})

    # Delete verification code from MongoDB
    def delete_verification_code(email):
        users.delete_one({'email': email})
        
    # Casing
    def title_case(text):
        lowercase_words = ['a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'yet', 'so', 'of', 'at', 'by', 'in', 'on', 'to', 'with', 'as', 'because', 'although', 'since', 'while', 'if', 'when', 'where', 'whether', 'after', 'before']
        words = text.split()
        title_case_words = [word.capitalize() if word.lower() not in lowercase_words else word.lower() for word in words]
        return ' '.join(title_case_words)

    
    # Login form
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            try:
                user = users.find_one({'email': email})
                if user and ph.verify(user['password'], password):
                    session['login_attempts'] = 0
                    session['email'] = email
                    return redirect(url_for('admin'))
                else:
                    session.setdefault('login_attempts', 0)
                    session['login_attempts'] += 1
                    flash('Incorrect email or password. Please try again.')
                    if session['login_attempts'] >= 3:
                        return redirect(url_for('reset_password'))
            except VerifyMismatchError:
                flash('Incorrect email or password. Please try again.')

        return render_template('login.html', form=form, error=form.errors)

    # Log out
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('admin'))

    # Updated Registration Route
    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("10 per day")
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            verification_code = secrets.token_urlsafe(16)
            expiration_time = expiration_timestamp()

            existing_user = users.find_one({'email': email})
            if existing_user:
                flash('Email address is already registered.', 'error')
                return redirect(url_for('register'))

            hashed_password = ph.hash(password)
            
            insert_verification_code(email, hashed_password, verification_code, expiration_time)       
            send_verification_email(email, verification_code)
            flash('Registration successful! A verification email has been sent to your email address.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html', form=form, error=form.errors)

    # Forgot password route 
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            email = form.email.data
            user = users.find_one({'email': email})
            if user:
                token = secrets.token_hex(16)
                password_resets.insert_one({'email': email, 'token': token, 'timestamp': datetime.datetime.now()})
                reset_link = url_for('reset_password', token=token, _external=True)
                msg = Message('FilmFlix Password Reset', recipients=[email])
                msg.body = f'FilmFlix\nYou, or someone else, have requested to reset your password. Please click on the following link to reset your password:\n\n{reset_link}\n\nIf you did not request this change, please ignore this email.\n\nHave a great day!\nFilmFlix Team'
                mail.send(msg)
                flash('An email has been sent with instructions to reset your password.')
                return redirect(url_for('login'))
            else:
                flash('Email address not found.')
        return render_template('forgot_password.html', form=form)
    
    
    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        form = ResetForm()
        reset = password_resets.find_one({'token': token})

        if reset:
            if request.method == 'GET':
                return render_template('reset_password.html', form=form, token=token)
            elif request.method == 'POST' and form.validate_on_submit():
                new_password = form.new_password.data
                confirm_password = form.confirm_password.data
                
                if new_password != confirm_password:
                    flash('Passwords do not match.')
                    return render_template('reset_password.html', form=form)
                
                hashed_password = ph.hash(new_password)
                users.update_one({'email': reset['email']}, {'$set': {'password': hashed_password}})
                password_resets.delete_one({'token': token})
                flash('Your password has been successfully reset. You can now login with your new password.')
                return redirect(url_for('login'))
        
        flash('Invalid or expired token.')
        return redirect(url_for('forgot_password'))



    # Verification
    @app.route('/verify/<email>/<verification_code>')
    def verify_email(email, verification_code):
        user = users.find_one({'email': email, 'verification_code': verification_code})
        if user:
            flash('Your email has been verified. You can now login.')
            users.update_one({'email': email}, {'$unset': {'verification_code': 1}})
            return redirect(url_for('login'))
        else:
            flash('Invalid verification code.')
        return redirect(url_for('verify'))

    # Main site get films. Search.
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/films', methods=['GET'])
    def get_films():
        genre = request.args.get('genre')
        year_released = request.args.get('yearReleased')
        rating = request.args.get('rating')
        title = request.args.get('title')
        query = {}
        if title:
            query['title'] = {"$regex": title, "$options": "i"}
        if genre:
            query['genre'] = {"$regex": genre, "$options": "i"}
        if year_released:
            query['yearReleased'] = int(year_released)
        if rating:
            query['rating'] = {"$regex": rating, "$options": "i"}
        films = list(film_collection.find(query))
        num_films_found = len(films)
        return render_template('films.html', films=films, num_films_found=num_films_found)

    # Admin area, CRUD.
    @app.route('/admin')
    def admin():
        total_films = film_collection.count_documents({})
        films = list(film_collection.find())
        return render_template('admin.html', films=films, total_films=total_films)

# Define get_next_film_id function
    def get_next_film_id():
        # Find the last film ID in the collection
        last_film = film_collection.find_one(sort=[('filmID', DESCENDING)])
        
        if last_film:
            # Increment the last film ID by 1 to generate the next film ID
            next_film_id = last_film['filmID'] + 1
        else:
            # If no films are in the collection, start with ID 1
            next_film_id = 1
        
        return next_film_id


    @app.route('/add_film', methods=['POST'])
    def add_film():
        if session.get('additions_count', 0) >= 3:
            flash('You have reached the maximum limit for adding films.', 'error')
            return redirect(url_for('admin'))
        
        session['additions_count'] = session.get('additions_count', 0) + 1
        
        next_film_id = get_next_film_id()
        title = title_case(request.form['title'])
        genre = title_case(request.form['genre'])
        rating = request.form['rating']
        poster = request.form['poster']
        year_released = int(request.form['yearReleased'])
        duration = int(request.form['duration'])
        
        film_data = {
            'filmID': next_film_id,
            'title': title,
            'genre': genre,
            'yearReleased': year_released,
            'rating': rating,
            'duration': duration,
            'poster': poster
        }
        
        film_collection.insert_one(film_data)
        flash('Film added successfully!', 'success')
        return redirect(url_for('admin'))

    @app.route('/modify_film/<film_id>', methods=['POST'])
    def modify_film(film_id):
        if session.get('modifications_count', 0) >= 3:
            flash('You have reached the maximum limit for modifying films.', 'error')
            return redirect(url_for('admin'))
        
        session['modifications_count'] = session.get('modifications_count', 0) + 1
        
        new_poster = request.form['poster']
        new_title = title_case(request.form['title'])
        new_genre = title_case(request.form['genre'])
        new_rating = request.form['rating']
        new_year_released = int(request.form['yearReleased'])
        new_duration = int(request.form['duration'])
        
        film_data = {
            'title': new_title,
            'genre': new_genre,
            'yearReleased': new_year_released,
            'rating': new_rating,
            'duration': new_duration,
            'poster': new_poster
        }
        
        film_collection.update_one({'_id': ObjectId(film_id)}, {'$set': film_data})
        flash('Film modified successfully!', 'success')
        return redirect(url_for('admin'))

    @app.route('/delete_film/<film_id>', methods=['POST'])
    def delete_film(film_id):
        if session.get('deletions_count', 0) >= 3:
            flash('You have reached the maximum limit for deleting films.', 'error')
            return redirect(url_for('admin'))
        
        session['deletions_count'] = session.get('deletions_count', 0) + 1
        
        film_id = ObjectId(film_id)
        result = film_collection.delete_one({'_id': film_id})

        if result.deleted_count == 1:
            flash('Film deleted successfully!', 'success')
        else:
            flash('Film not found or deletion failed', 'error')

        return redirect(url_for('admin'))

    # Email
    def send_verification_email(email, verification_code):
        subject = "FilmFlix Verify Your Email"
        sender = "saslam1023@icloud.com"
        recipient = email
    # msg = Message('FilmFlix Verify Your Email', recipients=[email])
        verify_url = url_for('verify_email', email=email, verification_code=verification_code, _external=True)
        msg = Message(subject, sender=sender, recipients=[recipient])
        msg.body = f'FilmFlix\nClick the following link to verify your email: {verify_url}\n\nHave a great day!\nFilmFlix Team'
        mail.send(msg)

    def send_reset_password_email(user_email, reset_token):
        subject = "FilmFlix Password Reset Request"
        sender = "saslam1023@icloud.com"
        recipient = user_email
        reset_link = url_for('reset_password', token=reset_token, _external=True)
        body = f"FilmFlix\nYou, or someone else, have requested to reset your password. Please click on the following link to reset your password:\n\n{reset_link}\n\nIf you did not request this change, please ignore this email.\n\nHave a great day!\nFilmFlix Team"
        msg = Message(subject, sender=sender, recipients=[recipient])
        msg.body = body
        mail.send(msg)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)

