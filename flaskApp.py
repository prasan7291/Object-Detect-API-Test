# Install Flask on your system by writing
#!pip install Flask
#Import all the required libraries
#Importing Flask
#render_template--> To render any html file, template

from flask import Flask, render_template, Response,jsonify,request,session

#FlaskForm--> it is required to receive input from the user
# Whether uploading a video file or assigning a confidence value to our object detection model

from flask_wtf import FlaskForm
from moviepy.video.io.VideoFileClip import VideoFileClip

from wtforms import FileField, SubmitField,StringField,DecimalRangeField,IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired,NumberRange
import os
from PIL import Image

# To style our CSS to render the HTML Pages
from flask_bootstrap import Bootstrap

# Required to run the YOLOv7 model
import cv2

# Hubconfcustom is the python file which contains the code for our object detection model
#Video Detection is the Function which performs Object Detection on Input Video
from hubconfCustom import video_detection, zone_detection

#Video_detection_web is the functon which performs object detection on Live Feed
from hubconfcustomweb import video_detection_web

import json
import math
from flask import Flask, render_template, Response, jsonify, request, session, url_for
from werkzeug.utils import secure_filename, redirect
import moviepy
import itertools
import time
from datetime import datetime


#------------------------------------
#------------------------------------
#Templates Folder contains all the html files which we will use in our application
#Static Folder Contains all the video files, when we want to run Object Detection on any input video
# the input video is saved in the static/files folder
#-----------------------------------------
#-----------------------------------------



#Flask Requirement to initialize any Flask Application
app = Flask(__name__)

# We are styling our application using the Bootstrap Library
Bootstrap(app)


#Here we have configured a secret key,which we will not use in this tutorial
app.config['SECRET_KEY'] = 'pr'

# We will store our input files which we will be uploaded to our application
app.config['UPLOAD_FOLDER'] = 'static/files'


#Rendering the Front page
#Here is how we will be rendering the Front Page
#Use FlaskForm to get input video file and confidence value from user
class UploadFileForm(FlaskForm):
    #We store the uploaded video file path in the FileField in the variable file
    #We have added validators to make sure the user inputs the video in the valid format  and user does upload the
    #video when prompted to do so
    file = FileField("File",validators=[InputRequired()])
    #Slider to get confidence value from user
    conf_slide = IntegerRangeField('Confidence:  ', default=50,validators=[InputRequired()])
    submit = SubmitField("Run")
    

#Generate_frames function takes path of input video file and confidence and  gives us the output with bounding boxes
# around detected objects, also we get the frame rate (FPS), video size,   total objects detected in each frame

#Now we will display the output video with detection, count of object detected in each frame, the resolution of the current
# frame and the FPS

frames = 0
sizeImage = 0
detectedObjects = 0
video_file_path=""

def generate_frames(path_x = '',conf_= 0.35):
    #yolo_output varaible stores the output for each detection, yolo_output will contain all 4 things

    yolo_output = video_detection(path_x,conf_)
    for detection_,FPS_,xl,yl,no_helmet,safety_violations in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)
        global frames
        frames = str(FPS_)
        global sizeImage
        sizeImage = str(xl[0])
        global detectedObjects
        detectedObjects = str(yl)
        global no_helmet_count
        no_helmet_count = str(no_helmet)
        global total_safety_violations
        total_safety_violations = str(safety_violations)
        print("Total Safety Violations: ", total_safety_violations)
        # Any Flask application requires the encoded image to be converted into bytes and rendered into an HTML page
        #.tobytes  convert the encoded image into bytes, We will display the individual frames using Yield keyword,
        #we will loop over all individual frames and display them as video
        #When we want the individual frames to be replaced by the subsequent frames the Content-Type, or Mini-Type
        #will be used
        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')


sizeImageweb = 0
detectedObjectsweb = 0

def generate_frames_web(path_x,conf_= 0.35):
    yolo_output = video_detection_web(path_x,conf_)
    for detection_,xl,yl in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)
        global sizeImageweb
        sizeImageweb = str(xl[0])
        global detectedObjectsweb
        detectedObjectsweb = str(yl)
        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')



# Rendering the Home Page/ Root Rage
#Now lets make a Root page for the application
#Use 'app.route()' method, to render the root page at "/" or "/home"

@app.route("/",methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])

#When ever the user requests a root page "/" ot root "/home" page our applciation will call this function
def home():
    #seesion.clear()--clears the session storage if i doesnot clear it and rerun the script the previous video will appear
    session.clear()
    #This return a render template of indexproject.html
    return render_template('indexproject.html')

# Rendering the Webcam Rage
#Now lets make a Webcam page for the application
#Use 'app.route()' method, to render the Webcam page at "/webcam"
@app.route("/webcam", methods=['GET','POST'])

def webcam():
    session.clear()
    return render_template('ui.html')

#When the user requests the front page, our application will call this function

@app.route('/FrontPage',methods=['GET','POST'])
def front():
    # session.clear()
    #Upload File Form: Create an instance for the Upload File Form
    form = UploadFileForm()
    if form.validate_on_submit():
        #Our uploaded video file path is saved here
        file = form.file.data
        video_file_path = file
        #print ("Uploaded File Path: ", video_file_path)
        # conf_ = form.text.data
        #We will save the confidence value from slider into this variable
        conf_ = form.conf_slide.data
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
        #Use session storage to save video file path and confidence value
        session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))
        # we store the confidence value in the session storage
        session['conf_'] = conf_
    return render_template('videoprojectnew.html',form=form)

#To display Output Video on Front Page
@app.route('/video')
def video():
    return Response(generate_frames(path_x = session.get('video_path', None),conf_=round(float(session.get('conf_', None))/100,2)),mimetype='multipart/x-mixed-replace; boundary=frame')
# To display the Output Video on Webcam page
@app.route('/webapp')
def webapp():
    #return Response(generate_frames(path_x = session.get('video_path', None),conf_=round(float(session.get('conf_', None))/100,2)),mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(generate_frames_web(path_x=0,conf_=0.35), mimetype='multipart/x-mixed-replace; boundary=frame')
#Lets create a URL using @app.route('/fpsgenerate') which is fpsgenerate
#go to generate_frames function where we perform object detection on input video, there we store the number of frames as
#global frames
@app.route('/fpsgenerate',methods = ['GET'])
def fps_fun():
    global frames
    frames_string = "Test"
    # Now we will jsonify the frames we stored earlier
    frames_json = jsonify(result=frames)
    return jsonify(frames_string=frames_string, frames_json=frames_json.json)

@app.route('/sizegenerate',methods = ['GET'])
def size_fun():
    global sizeImage
    return jsonify(imageSize=sizeImage)

frames_with_safety_violations = []

@app.route('/detectionCount', methods=['POST'])
def detect_fun():
    global frames_with_safety_violations  # Declare the global variable
    # Get the uploaded video file
    video_url = request.form.get('video_path')
    #video_file = request.files.get('video')
    if not video_url:
        return jsonify(message="Please upload a video first.")

    video_file_path = video_url.replace("http://", "").split("/", 1)[-1]

    # Modify the video path to match the desired format
    video_file_path = video_file_path.lstrip("/").replace("%20", " ")

    # Get the absolute path of the script's parent directory
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Join the script's parent directory with the modified video path
    absolute_video_file_path = os.path.join(script_directory, video_file_path)

    # Replace forward slashes with backslashes in the absolute video file path
    absolute_video_file_path = absolute_video_file_path.replace("/", "\\")
    print("New Video File Path: ", absolute_video_file_path)


    # Check if the video file exists
    if not os.path.exists(absolute_video_file_path):
        return jsonify(message="Video file not found.")


    # Save the uploaded video file to a specific location
    #video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video_file.filename))
    #video_file.save(video_file_path)

    # Perform object detection on the video
    yolo_output = video_detection(absolute_video_file_path, conf_=0.35)
    frames_with_safety_violations = {}  # Reset the frames_with_safety_violations dictionary
    frame_images_data = []
    no_coverall_frame_numbers = []
    no_gloves_frame_numbers = []
    no_glasses_frame_numbers = []

    #Get the parent directory of the video file
    #parent_directory = os.path.dirname(absolute_video_file_path)
    parent_directory = os.path.join(app.config['UPLOAD_FOLDER'], "Processed Video Data")
    print("Parent Directory: ", parent_directory)

    # Create the "Processed Video Data" folder if it doesn't exist
    #processed_data_folder = os.path.join(parent_directory, "Processed Video Data")
    processed_data_folder = parent_directory
    print("Processed Data Folder: ", processed_data_folder)
    os.makedirs(processed_data_folder, exist_ok=True)

    for frame_number, (frame_image, FPS_, xl, no_coverall_count, no_helmet_count, no_gloves_count, total_safety_violations, class_counts, no_glasses_count) in enumerate(yolo_output):
        frames = str(FPS_)
        sizeImage = str(xl)
        no_coverall_count = str(no_coverall_count)
        print("No Coverall Count in Frame: ", no_coverall_count)
        no_helmet_count = str(no_helmet_count)
        no_gloves_count = str(no_gloves_count)
        print("No Gloves Count: ", no_gloves_count)
        no_glasses_count = str(no_glasses_count)
        print ("No Glasses Count: ", no_glasses_count)
        total_safety_violations = str(total_safety_violations)

        if int(total_safety_violations) > 0:
            frames_with_safety_violations.setdefault('detectCount', []).append(frame_number)
            if int(no_coverall_count) > 0:
                frames_with_safety_violations.setdefault('NoCoverallCount', []).append(frame_number)

                # Calculate timestamp based on frame number and frame rate
                no_coverall_frame_numbers.append(frame_number)
                no_coverall_timestamp = time.time()
                no_coverall_formatted_timestamp = datetime.fromtimestamp(no_coverall_timestamp).strftime('%Y-%m-%d %I:%M:%S %p')

                # Save the processed frame image
                frame_filename = f"{os.path.splitext(os.path.basename(video_file_path))[0]}_{frame_number}_NoCoverall.jpg"
                frame_path = os.path.join("static/files/Processed Video Data", frame_filename)
                cv2.imwrite(frame_path, frame_image, [cv2.IMWRITE_JPEG_QUALITY, 100])

                frame_images_data.append({
                    'frame_number': frame_number,
                    'frame_image_path': frame_path,
                    'class_id': 'No Coverall',
                    'timestamp': no_coverall_formatted_timestamp
                })

            if int(no_gloves_count) > 0:
                frames_with_safety_violations.setdefault('NoGlovesCount', []).append(frame_number)

                # Calculate timestamp based on frame number and frame rate
                no_gloves_frame_numbers.append(frame_number)
                no_gloves_timestamp = time.time()
                no_gloves_formatted_timestamp = datetime.fromtimestamp(no_gloves_timestamp).strftime(
                    '%Y-%m-%d %I:%M:%S %p')

                # Save the processed frame image
                frame_filename = f"{os.path.splitext(os.path.basename(video_file_path))[0]}_{frame_number}_NoGloves.jpg"
                frame_path = os.path.join("static/files/Processed Video Data", frame_filename)
                cv2.imwrite(frame_path, frame_image, [cv2.IMWRITE_JPEG_QUALITY, 90])

                frame_images_data.append({
                    'frame_number': frame_number,
                    'frame_image_path': frame_path,
                    'class_id': 'No Gloves',
                    'timestamp': no_gloves_formatted_timestamp
                })

            if int(no_glasses_count) > 0:
                frames_with_safety_violations.setdefault('NoGlassesCount', []).append(frame_number)

                # Calculate timestamp based on frame number and frame rate
                no_glasses_frame_numbers.append(frame_number)
                no_glasses_timestamp = time.time()
                no_glasses_formatted_timestamp = datetime.fromtimestamp(no_glasses_timestamp).strftime(
                    '%Y-%m-%d %I:%M:%S %p')

                # Save the processed frame image
                frame_filename = f"{os.path.splitext(os.path.basename(video_file_path))[0]}_{frame_number}_NoGlasses.jpg"
                frame_path = os.path.join("static/files/Processed Video Data", frame_filename)
                cv2.imwrite(frame_path, frame_image, [cv2.IMWRITE_JPEG_QUALITY, 100])

                frame_images_data.append({
                    'frame_number': frame_number,
                    'frame_image_path': frame_path,
                    'class_id': 'No Glasses',
                    'timestamp': no_glasses_formatted_timestamp
                })
    response = {
        'frame_images': frame_images_data
    }

    return jsonify(response)

@app.route('/sizegenerateweb',methods = ['GET'])
def size_fun_web():
    global sizeImageweb
    return jsonify(imageSize=sizeImageweb)

@app.route('/detectionCountweb',methods = ['GET'])
def detect_fun_web():
    global detectedObjectsweb
    return jsonify(detectCount=detectedObjectsweb)

ALLOWED_EXTENSIONS = {'mp4'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def split_video_into_chunks(video_path, parent_filename):
    print("split_video_into_chunks function RAN!!!!")
    video_file = VideoFileClip(video_path)
    duration = video_file.duration
    chunk_duration = 1 * 60  # 5 minutes in seconds
    num_chunks = int(math.ceil(duration / chunk_duration))
    output_folder = os.path.join(os.path.dirname(video_path), "Split Videos")
    os.makedirs(output_folder, exist_ok=True)

    for i in range(num_chunks):
        start_time = i * chunk_duration
        end_time = min((i + 1) * chunk_duration, duration)
        subclip = video_file.subclip(start_time, end_time)
        output_filename = os.path.join(output_folder, f"{os.path.splitext(parent_filename)[0]}_Part_{i + 1}.mp4")
        subclip.write_videofile(output_filename, codec='libx264')

        thumbnail_filename = f"{os.path.splitext(parent_filename)[0]}_Part_{i + 1}_thumbnail.jpg"
        thumbnail_path = os.path.join(output_folder, thumbnail_filename)
        thumbnail_image = subclip.get_frame(0)  # Get the first frame of the video part as the thumbnail
        Image.fromarray(thumbnail_image).save(thumbnail_path)

    print(f"Video split into {num_chunks} parts.")

@app.route('/split_video', methods=['GET','POST'])
def split_video():
    video_file = request.files.get('file')
    if not video_file:
        return jsonify(message="Please upload a video first.")

    # Save the uploaded video file to a specific location
    video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video_file.filename))
    video_file.save(video_file_path)

    # Call the function to split the video into chunks
    split_video_into_chunks(video_file_path,video_file.filename)
    # Return JSON response
    return jsonify(message="Video split into chunks successfully.")
@app.route('/split_video_details', methods=['GET'])
def split_video_details():
    output_folder = os.path.join(app.config['UPLOAD_FOLDER'], "Split Videos")
    print("Output Folder: ", output_folder)
    files_and_durations = []
    ip_address = request.url_root

    # Get the video file selected by the user
    for filename in os.listdir(output_folder):
        if filename.lower().endswith('.mp4'):  # Check if the file has the .mp4 extension
            file_path = os.path.join(output_folder, filename)
            duration_in_secs = VideoFileClip(file_path).duration
            duration_in_mins = round(duration_in_secs / 60, 2)
            file_url = url_for('static', filename=os.path.join('files', 'Split Videos', filename))
            print("File URL: ", file_url)
            file_url_with_ip = ip_address + file_url
            thumbnail_name = file_url_with_ip.replace(".mp4", "_thumbnail.jpg")  # Generate the thumbnail filename

            # Split the filename based on "_ Part"
            parent_file_name = filename.split("_ Part")[0].rsplit('_', 1)[0].strip()  # Extract the parent file name from the filename
            parent_file_url_with_ip = ip_address + url_for('static', filename=os.path.join('files', 'Split Videos',
                                                                                           parent_file_name + ".mp4"))
            print("Parent File Name: ",parent_file_name)
            files_and_durations.append({
                'parent_file_name': parent_file_url_with_ip,
                'file_name': filename,
                'duration_in_mins': duration_in_mins,
                'file_url': file_url_with_ip,
                'thumbnail': thumbnail_name
            })
    # Return the list of file parts as a JSON response
    print("Files and Durations: ", files_and_durations)
    return jsonify(file_parts=files_and_durations)

@app.route('/zoneDetection', methods=['POST'])
def zone_detect():
    global frames_with_safety_violations  # Declare the global variable
    # Get the uploaded video file
    video_url = request.form.get('video_path')
    #video_file = request.files.get('video')
    if not video_url:
        return jsonify(message="Please upload a video first.")

    video_file_path = video_url.replace("http://", "").split("/", 1)[-1]

    # Modify the video path to match the desired format
    video_file_path = video_file_path.lstrip("/").replace("%20", " ")

    # Get the absolute path of the script's parent directory
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Join the script's parent directory with the modified video path
    absolute_video_file_path = os.path.join(script_directory, video_file_path)

    # Replace forward slashes with backslashes in the absolute video file path
    absolute_video_file_path = absolute_video_file_path.replace("/", "\\")
    print("New Video File Path: ", absolute_video_file_path)

    # Save the uploaded video file to a specific location
    #video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video_file.filename))
    #video_file.save(video_file_path)

    # Open the video to get the number of frames
    video = cv2.VideoCapture(absolute_video_file_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))  # Get the total number of frames in the video
    video.release()  # Release the video object
    print("NUmber of Frames: ", total_frames)

    # Perform object detection on the video
    zone_detect_output = zone_detection(absolute_video_file_path, conf_=0.5, warning_threshold=120)
    frames_with_safety_violations = {}  # Reset the frames_with_safety_violations dictionary
    frame_images_data = []
    warning_frame_numbers = []

    # Get the parent directory of the video file
    parent_directory = os.path.join(app.config['UPLOAD_FOLDER'], "Processed Video Data")
    print("Parent Directory: ", parent_directory)

    # Create the "Processed Video Data" folder if it doesn't exist
    # processed_data_folder = os.path.join(parent_directory, "Processed Video Data")
    processed_data_folder = parent_directory
    print("Processed Data Folder: ", processed_data_folder)
    os.makedirs(processed_data_folder, exist_ok=True)

    for frame_number, (
    frame_image, FPS_, xl, warning_count, total_violations) in enumerate(zone_detect_output):
        print(f"Processing frame {frame_number + 1}/{total_frames}")
        frames = str(FPS_)
        sizeImage = str(xl)
        warning_count = str(warning_count)
        total_violations = str(total_violations)

        if int(total_violations) > 0:
            frames_with_safety_violations.setdefault('detectCount', []).append(frame_number)
            if int(warning_count) > 0:
                frames_with_safety_violations.setdefault('WarningCount', []).append(frame_number)

                # Calculate timestamp based on frame number and frame rate
                warning_frame_numbers.append(frame_number)
                warning_timestamp = time.time()
                warning_formatted_timestamp = datetime.fromtimestamp(warning_timestamp).strftime(
                    '%Y-%m-%d %I:%M:%S %p')

                # Save the processed frame image
                frame_filename = f"{os.path.splitext(os.path.basename(video_file_path))[0]}_{frame_number}_Warning.jpg"
                frame_path = os.path.join("static/files/Processed Video Data", frame_filename)
                cv2.imwrite(frame_path, frame_image, [cv2.IMWRITE_JPEG_QUALITY, 100])

                frame_images_data.append({
                    'frame_number': frame_number,
                    'frame_image_path': frame_path,
                    'class_id': 'Warning',
                    'timestamp': warning_formatted_timestamp
                })

    response = {
        'frame_images': frame_images_data
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=81)
