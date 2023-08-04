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
from hubconfCustom import video_detection, video_splitter

#Video_detection_web is the functon which performs object detection on Live Feed
from hubconfcustomweb import video_detection_web

import json
import math
from flask import Flask, render_template, Response, jsonify, request, session, url_for
from werkzeug.utils import secure_filename, redirect
import moviepy


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
    conf_slide = IntegerRangeField('Confidence:  ', default=25,validators=[InputRequired()])
    submit = SubmitField("Run")
    

#Generate_frames function takes path of input video file and confidence and  gives us the output with bounding boxes
# around detected objects, also we get the frame rate (FPS), video size,   total objects detected in each frame

#Now we will display the output video with detection, count of object detected in each frame, the resolution of the current
# frame and the FPS

frames = 0
sizeImage = 0
detectedObjects = 0
video_file_path=""

def generate_frames(path_x = '',conf_= 0.25):
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

def generate_frames_web(path_x,conf_= 0.25):
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
    return Response(generate_frames_web(path_x=0,conf_=0.25), mimetype='multipart/x-mixed-replace; boundary=frame')
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
'''
def fps_fun():
    global frames
    frames_string = "Test"
    # Now we will jsonify the frames we stored earlier
    return jsonify(result=frames)'''

@app.route('/sizegenerate',methods = ['GET'])
def size_fun():
    global sizeImage
    return jsonify(imageSize=sizeImage)

'''@app.route('/detectionCount',methods = ['GET'])
def detect_fun():
    global detectedObjects
    return jsonify(detectCount=detectedObjects,NoHelmetCount=no_helmet_count,TotalSafetyViolations=total_safety_violations)'''

frames_with_safety_violations = []
@app.route('/detectionCount', methods=['POST'])
def detect_fun():
    global frames_with_safety_violations  # Declare the global variable
    # Get the uploaded video file
    video_file = request.files.get('video')
    if not video_file:
        return jsonify(message="Please upload a video first.")

    # Save the uploaded video file to a specific location
    video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video_file.filename))
    video_file.save(video_file_path)

    # Perform object detection on the video
    yolo_output = video_detection(video_file_path, conf_=0.25)
    frames, sizeImage, detectedObjects, no_helmet_count, total_safety_violations = 0, 0, 0, 0, 0
    safety_violation_frames = []

    for frame_number, (_, FPS_, xl, yl, no_helmet, safety_violations) in enumerate(yolo_output):
        frames = str(FPS_)
        sizeImage = str(xl)
        detectedObjects = str(yl)
        no_helmet_count = str(no_helmet)
        total_safety_violations = str(safety_violations)

        if int(safety_violations) > 0:
            frames_with_safety_violations.append(frame_number)
            capture_screenshot(video_file_path, frame_number)
            safety_violation_frames.append(frame_number)  # Append frame number with safety violation

    response = {
        'results': [
            {'id': 'detectCount', 'frames': safety_violation_frames},
            {'id': 'NoHelmetCount', 'frames': frames_with_safety_violations},
            {'id': 'TotalSafetyViolations', 'value': total_safety_violations}
        ]
    }

    return jsonify(response)


def capture_screenshot(video_path, frame_number):
    video_capture = cv2.VideoCapture(video_path)
    video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video_capture.read()

    if ret:
        screenshot_folder = os.path.join(app.config['UPLOAD_FOLDER'], "Processed Video Data")
        os.makedirs(screenshot_folder, exist_ok=True)

        screenshot_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_{frame_number}.jpg"
        screenshot_path = os.path.join(screenshot_folder, screenshot_filename)

        cv2.imwrite(screenshot_path, frame)
        print(f"Screenshot saved: {screenshot_path}")
    else:
        print(f"Error capturing screenshot for frame {frame_number}")

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
        output_filename = os.path.join(output_folder, f"{os.path.splitext(parent_filename)[0]}_Part {i + 1}.mp4")
        subclip.write_videofile(output_filename, codec='libx264')

        thumbnail_filename = f"{os.path.splitext(parent_filename)[0]}_Part {i + 1}_thumbnail.jpg"
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


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=80)
