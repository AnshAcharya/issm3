from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, decode_token
import datetime
import numpy as np
import cv2
from moviepy.editor import ImageSequenceClip
import os

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = 'SecurityKeyOfTeanmLAB--4>'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Ansh%402006@127.0.0.1/media_library' 
app.config['DEBUG'] = True
jwt = JWTManager(app)
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
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

        password_token = create_access_token(identity=password, expires_delta=datetime.timedelta(days=1))  # Expires in 1 day

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
    return render_template('homePage.html')

# from flask import render_template, redirect, request, session
# from your_flask_app import app, db  # Replace 'your_flask_app' with the actual name of your Flask app
# from models import image  # Assuming Image is the SQLAlchemy model for your images

import base64

@app.route('/video', methods=['GET', 'POST'])
def video():
    user_id = session.get('user_id')
    images = Image.query.filter_by(user_id=user_id).all()

    # Encode image data to base64 before passing it to the template
    encoded_images = [base64.b64encode(image.image_data).decode('ascii') for image in images]
    image_sequence = []
    max_height = 0
    max_width = 0
    for image in images:
        image_data = np.frombuffer(image.image_data, np.uint8)
        decoded_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        # Convert image to RGB color space
        rgb_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
        height, width, _ = rgb_image.shape
        max_height = max(max_height, height)
        max_width = max(max_width, width)
        image_sequence.append(rgb_image)

    # Resize images to the maximum dimensions
    image_sequence_resized = [cv2.resize(image, (max_width, max_height)) for image in image_sequence]

    # Duplicate frames to increase video duration
    extended_sequence = []
    for image in image_sequence_resized:
        for _ in range(20):
            extended_sequence.append(image)

    # Create video clip from extended image sequence
    video_clip = ImageSequenceClip(extended_sequence, fps=24)

    # Specify the output video path within the static folder
    static_folder = app.static_folder
    output_video_path = os.path.join(static_folder, "output_video.mp4")

    # Write the video file
    video_clip.write_videofile(output_video_path, codec="libx264", fps=24)
    video_path = 'static/output_video.mp4'

    return render_template('videoPage.html', images=encoded_images, video_path=video_path)



# @app.route('/video', methods=['GET', 'POST'])
# def vedio():
#     return render_template('videoPage.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)