# Pyhton program to implement 
# WebCam Motion Detector
# https://www.geeksforgeeks.org/webcam-motion-detector-python/

# importing OpenCV, time and Pandas library 
import cv2, time#, pandas
import pigpio
from time import sleep

# importing datetime class from datetime library 
from datetime import datetime


pi = pigpio.pi()
pi.set_mode(17, pigpio.OUTPUT)
pi.set_mode(27, pigpio.OUTPUT)

pi.set_servo_pulsewidth(17, 1330)
pi.set_servo_pulsewidth(27, 1540)
sleep(0.25)

INCREMENT = 70

def set_servo(pi, servo, pwm):
    if pwm < 25:
        pwm = 25
    if pwm > 40000:
        pwm = 40000
    pi.set_servo_pulsewidth(servo, pwm)

# Assigning our static_back to None 
static_back = None

# List when any moving object appear 
#motion_list = [ None, None ] 

# Time of movement 
#time = [] 

# Initializing DataFrame, one column is start 
# time and other column is end time 
#df = pandas.DataFrame(columns = ["Start", "End"]) 

# Capturing video 
video = cv2.VideoCapture(0)

margin = 60
width = 640
height = 480

def resetRef():
    global static_back
    global video
    #sleep(2)
    static_back = None
#    video.release()
#    video = cv2.VideoCapture(0)

def flagMovement(c, frame):
    global margin
    global height
    global width
    global cv2
    global static_back
    
    (x, y, w, h) = cv2.boundingRect(c)
    
    if x+w >= width and x+h >= height:
        return
    
    if x < margin:
        cv2.line(frame,(margin,0),(margin,480),(255,0,255),5)
        set_servo(pi, 27, pi.get_servo_pulsewidth(27)+INCREMENT)
        resetRef()
    elif (x+w) > (width-margin):
        cv2.line(frame,(640-margin,0),(640-margin,480),(255,0,255),5)
        set_servo(pi, 27, pi.get_servo_pulsewidth(27)-INCREMENT)
        resetRef()
    if y < margin:
        cv2.line(frame,(0,margin),(640,margin),(255,0,255),5)
        set_servo(pi, 17, pi.get_servo_pulsewidth(17)-INCREMENT)
        resetRef()
    elif (y+h) > (height-margin):
        set_servo(pi, 17, pi.get_servo_pulsewidth(17)+INCREMENT)
        cv2.line(frame,(0,480-margin),(640,480-margin),(255,0,255),5)
        resetRef()

# Infinite while loop to treat stack of image as video 
while True:
#    if static_back is None:
#        print('waiting for reference')
#        sleep(5)
    # Reading frame(image) from video 
    check, frame = video.read()
    frame = cv2.flip(frame, -1)

    # Initializing motion = 0(no motion) 
    #motion = 0

    # Converting color image to gray_scale image 
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 

    # Converting gray scale image to GaussianBlur 
    # so that change can be find easily 
    gray = cv2.GaussianBlur(gray, (21, 21), 0) 

    # In first iteration we assign the value 
    # of static_back to our first frame 
    if static_back is None:
        print('setting reference')
        static_back = gray 
        continue

    # Difference between static background 
    # and current frame(which is GaussianBlur) 
    diff_frame = cv2.absdiff(static_back, gray) 

    # If change in between static background and 
    # current frame is greater than 30 it will show white color(255) 
    thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1] 
    thresh_frame = cv2.dilate(thresh_frame, None, iterations = 2) 

    # Finding contour of moving object 
    (_, cnts, _) = cv2.findContours(thresh_frame.copy(), 
                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    cv2.line(frame,(margin,0),(margin,480),(255,0,0),2)
    cv2.line(frame,(640-margin,0),(640-margin,480),(255,0,0),2)
    cv2.line(frame,(0,margin),(640,margin),(0,0,255),2)
    cv2.line(frame,(0,480-margin),(640,480-margin),(0,0,255),2)
    
    biggest = None

    for contour in cnts: 
        if cv2.contourArea(contour) < 10000: 
            continue
        #motion = 1
        if biggest is None or cv2.contourArea(contour) > cv2.contourArea(biggest):
            biggest = contour
            
        
        (x, y, w, h) = cv2.boundingRect(contour) 
        # making green rectangle arround the moving object 
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
    
    # Displaying color frame with contour of motion of object 
#    cv2.imshow("Color Frame", frame)
    
#    cv2.imshow("Diff", static_back)
    
    if biggest is not None:
        flagMovement(biggest, frame)
#        

    

    key = cv2.waitKey(1) 
    # if q entered whole process will stop 
    if key == ord('q'):
        pi.set_servo_pulsewidth(17, 1330)
        pi.set_servo_pulsewidth(27, 1540)
        sleep(0.25)
        # if something is movingthen it append the end time of movement 
        #if motion == 1: 
        #   time.append(datetime.now()) 
        break

# Appending time of motion in DataFrame 
#for i in range(0, len(time), 2): 
#   df = df.append({"Start":time[i], "End":time[i + 1]}, ignore_index = True) 

# Creating a csv file in which time of movements will be saved 
#df.to_csv("Time_of_movements.csv") 

video.release() 

# Destroying all the windows 
cv2.destroyAllWindows() 
