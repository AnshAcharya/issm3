import numpy as np
import io
import cv2
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from moviepy.editor import ImageSequenceClip
from app import app, Image  # Assuming Image is the SQLAlchemy model for your images

def create_video(duration_increase):
    # Connect to the database
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query all image records from the database
    images = session.query(Image).all()

    # Check if there are any images in the database
    if not images:
        print("No images found in the database.")
        return

    print(f"Total images found: {len(images)}")

    # Extract image data from database records and decode them into NumPy arrays
    image_sequence = []
    max_height = 0
    max_width = 0
    for image in images:
        image_data = np.frombuffer(image.image_data, np.uint8)
        decoded_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        height, width, _ = decoded_image.shape
        max_height = max(max_height, height)
        max_width = max(max_width, width)
        image_sequence.append(decoded_image)

    # Resize images to the maximum dimensions
    image_sequence_resized = [cv2.resize(image, (max_width, max_height)) for image in image_sequence]

    # Duplicate frames to increase video duration
    extended_sequence = []
    for image in image_sequence_resized:
        for _ in range(duration_increase):
            extended_sequence.append(image)

    # Create video clip from extended image sequence
    video_clip = ImageSequenceClip(extended_sequence, fps=24)

    # Specify the output video path within the static folder
    static_folder = app.static_folder
    output_video_path = os.path.join(static_folder, "output_video.mp4")

    # Write the video file
    video_clip.write_videofile(output_video_path, codec="libx264", fps=24)

    print(f"Video created successfully at {output_video_path}.")

if __name__ == "__main__":
    # Increase the duration of the video by adding each frame multiple times
    duration_increase = 20  # Change this value to increase the duration by different amounts
    create_video(duration_increase)
