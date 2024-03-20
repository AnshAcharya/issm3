from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, decode_token
import datetime
import numpy as np
import cv2
from moviepy.editor import ImageSequenceClip
import os
from flask import jsonify
from moviepy.editor import ImageClip, concatenate_videoclips,AudioFileClip
from sqlalchemy import create_engine

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine, text


# Initialize Flask app
app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'DefaultSecretKey')
# Set SQLAlchemy database URI from environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'cockroachdb://likhitbhogadi:X34a6UmwvQJT8pr5f8wcdQ@crawly-ewe-9007.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/issproject?sslmode=verify-full')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', True)

# Initialize JWT Manager
jwt = JWTManager(app)

# Initialize SQLAlchemy database instance
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)

# Establish connection and execute SQL query
engine = create_engine(os.environ["DATABASE_URL"])
conn = engine.connect()
res = conn.execute(text("SELECT now()")).fetchall()
print(res)

    
class Image(db.Model):
    image_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    image_data = db.Column(db.BLOB, nullable=False)  # This line should match the column in your database

@app.route('/', methods=['GET', 'POST'])
def landing_and_login_page():

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username.lower()).first()

        if user:
            stored_password = user.password
            decoded_token = decode_token(stored_password)
            decoded_password = decoded_token['sub']
            if password == decoded_password:
                session['user_id'] = user.user_id
                global tempUser
                tempUser=username
                if 'users' not in session:
                    session['users'] = []
                if username not in session['users']:
                    session['users'].append(username)
                return redirect('/home')

        return render_template('landing&loginPage.html', message='Invalid username or password')

    return render_template('landing&loginPage.html')

# Route for signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template('signupPage.html', message='Username already exists')

        password_token = create_access_token(identity=password, expires_delta=datetime.timedelta(days=30))  # Expires in 1 day

        try:
            # new_image = Image(imge)
            new_user = User(username=username, email=email, password=password_token)
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            print(f"Error occurred while querying the database: {str(e)}")
            return render_template('signupPage.html', message='Error occurred while creating user')

        session['user_id'] = new_user.user_id
        return redirect('/')

    return render_template('signupPage.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    is_admin = False

    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            is_admin = user.username == 'admin'
    if request.method == 'POST':
        user_id = session.get('user_id')
        if 'images[]' in request.files:
            images = request.files.getlist('images[]')
            for image in images:
                if image:
                    filename = image.filename
                    image_data = image.read()  # Read the binary data of the image
                    new_image = Image(user_id=user_id, filename=filename, image_data=image_data)
                    db.session.add(new_image)
                    db.session.commit()
            return redirect('/video')
        else:
            # Handle case when no images are uploaded
            return render_template('homePage.html', message='No images uploaded')
    return render_template('homePage.html', tempUser=tempUser,is_admin=is_admin)

# from flask import render_template, redirect, request, session
# from your_flask_app import app, db  # Replace 'your_flask_app' with the actual name of your Flask app
# from models import image  # Assuming Image is the SQLAlchemy model for your images

import base64

from moviepy.editor import ImageClip, concatenate_videoclips
import numpy as np
@app.route('/video', methods=['GET', 'POST'])
def video():
    user_id = session.get('user_id')
    images = Image.query.filter_by(user_id=user_id).all()
    print(f"no.of images: {len(images)}")
    if not images:
        return render_template('videoPage.html', message='No images found')

    # Encode image data to base64 before passing it to the template
    encoded_images = [base64.b64encode(image.image_data).decode('ascii') for image in images]
    # Determine the selected transition effect
    transition_effect = request.form.get('transitionSelect')
    print(f"Selected transition effect: {transition_effect}")
    # Create video clip with the selected transition effect between images
    clips = []
    total_duration = 0
    for i in range(len(images)):
        image_data = np.frombuffer(images[i].image_data, np.uint8)
        decoded_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
        height, width, _ = rgb_image.shape
        clip = ImageClip(rgb_image, duration=3).set_position(('center', 'center'))  # Adjust duration as needed

        if transition_effect == "fade-in":
            fadein_duration = 2
            clip = clip.fadein(fadein_duration)
        elif transition_effect == "fade-out":
            fadeout_duration = 2
            clip = clip.fadeout(fadeout_duration)
        elif transition_effect == "crossfade-in":
            crossfade_duration = 2
            clip = clip.crossfadein(crossfade_duration)
        elif transition_effect == "crossfade-out":
            crossfade_duration = 2
            clip = clip.fadeout(crossfade_duration)
        elif transition_effect == "fade-in-fade-out":
            fadein_duration = 1
            fadeout_duration = 1
            clip = clip.fadein(fadein_duration).fadeout(fadeout_duration)
        elif transition_effect == "crossfadeinout":
            crossfade_duration = 2
            clip = clip.fadein(crossfade_duration).fadeout(crossfade_duration)
        elif transition_effect=="null":
            pass

        clips.append(clip)
        total_duration += clip.duration

    # Add a final transition at the end of the video to smoothly end it
    if transition_effect == "fade-out":
        final_transition = clips[-1].fadeout(2)  # Use the same fadeout duration as other transitions
    elif transition_effect == "crossfade-out":
        final_transition = clips[-1].fadeout(2)
    else:
        final_transition = clips[-1].crossfadeout(2)  # Default transition for ending the video

    clips.append(final_transition)

    # Calculate the total duration of the video
    # total_duration = sum(clip.duration for clip in clips)

    # Concatenate all clips to create the final video
    final_clip = concatenate_videoclips(clips, method="compose")
    audio_file_path = request.form.get('selectedAudio')  # Assuming 'selectedAudio' is the name of the audio select field
    if audio_file_path:
        audio_clip = AudioFileClip(audio_file_path)
        final_clip = final_clip.set_audio(audio_clip)

    # final_clip = final_clip.set_duration(total_duration)

    # Specify the output video path within the static folder
    static_folder = app.static_folder
    output_video_path = os.path.join(static_folder, "output_video.mp4")

    # Write the video file
    final_clip.write_videofile(output_video_path, codec="libx264", fps=24)
    video_path = 'static/output_video.mp4'

    print(f"Video created successfully at {output_video_path}.")
    return render_template('videoPage.html', images=encoded_images, video_path=video_path)

@app.route('/admin')
def admin():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user and user.username == 'admin':
            users = session.get('users', [])
            print("Current users:", users)  # Print the current users for debugging
            return render_template('adminPage.html', username=user.username, users=users)
    
    return redirect('/home')
# @app.route('/video', methods=['GET', 'POST'])
# def vedio():
#     return render_template('videoPage.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port="5038")