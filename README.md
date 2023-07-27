# Object-Detect-API-Test
Repository to hold object detection API testing code


Instructions:
1) Install python version 3.10.11 using the link https://www.python.org/downloads/release/python-31011/
2) open command prompt and navigate to the github repository cloned folder
3) Run command "pip install -r requirements.txt
4) Once all dependencies are installed without errors, use the command "python flaskApp.py" to run the python code. When you run it, it will give you an IP address that you can open on a chrome browser.
5) Once the page is open click on the "Video" button on the top left corner of the screen which will take you to a separate page
6) In the video processing page, click on the "Choose file..." button to open the windows explorer button. Navigate to the static/files folder in the project directory and select "Test-video.mp4".
7) Once the video is selected, click on submit button. This will run the object detection code in the background and return a json string for an API request "detectionCount"
8) In postmant, copy paste the URL that was generated when running the python code and add "/detectionCount" in front of it to get access to the data