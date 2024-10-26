import cv2
import sys
import logging as log
import datetime as dt
from time import sleep
import subprocess
from os import listdir
from random import randrange
import pigpio

cascPath = "/home/pi/really-useful-robot/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascPath)
log.basicConfig(filename='webcam.log',level=log.INFO)

video_capture = cv2.VideoCapture(0)
anterior = 0
found = False
DEBOUNCE_TIME = 3
debounce = DEBOUNCE_TIME
VOLUME = '-3000'

pi = pigpio.pi()
pi.set_mode(17, pigpio.OUTPUT)
pi.set_mode(27, pigpio.OUTPUT)

pi.set_servo_pulsewidth(17, 1330)
pi.set_servo_pulsewidth(27, 1540)
sleep(0.25)

DISPLAY_ON_SCREEN = True

margin = 60
width = 640
height = 480
INCREMENT = 30

def set_servo(pi, servo, pwm):
    if pwm < 25:
        pwm = 25
    if pwm > 40000:
        pwm = 40000
    pi.set_servo_pulsewidth(servo, pwm)
#    sleep(0.25)
    
def flagMovement(x,y,w,h, frame):
    global margin
    global height
    global width
    global cv2
        
    if x+w >= width and x+h >= height:
        return
    
    if x < margin:
        cv2.line(frame,(margin,0),(margin,480),(255,0,255),5)
        set_servo(pi, 27, pi.get_servo_pulsewidth(27)+INCREMENT)
    elif (x+w) > (width-margin):
        cv2.line(frame,(640-margin,0),(640-margin,480),(255,0,255),5)
        set_servo(pi, 27, pi.get_servo_pulsewidth(27)-INCREMENT)
    if y < margin:
        cv2.line(frame,(0,margin),(640,margin),(255,0,255),5)
        set_servo(pi, 17, pi.get_servo_pulsewidth(17)-INCREMENT)
    elif (y+h) > (height-margin):
        set_servo(pi, 17, pi.get_servo_pulsewidth(17)+INCREMENT)
        cv2.line(frame,(0,480-margin),(640,480-margin),(255,0,255),5)

def manageState(iSeeFaces, f, d):
    global debounce
    global found
    
    if (iSeeFaces == True):
        #print('f+')
        if (found == False):
            debounce -= 1
        else:
            debounce = DEBOUNCE_TIME
    else:
        #print('f-')
        if (found == True):
            debounce -= 1
        else:
            debounce = DEBOUNCE_TIME
            
    #print(debounce)
    if (debounce <= 0):
        found = iSeeFaces
        if found:
            #print('found face')
            playSound('face_found')
        else:
            #print('face lost')
            playSound('face_lost')

def manageDisplay(d):
    global DISPLAY_ON_SCREEN
    global faces
    global cv2
    global anterior
    global debounce
    global DEBOUNCE_TIME
    
    if (DISPLAY_ON_SCREEN):
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            flagMovement(x,y,w,h, frame)
            
        if anterior != len(faces):
            anterior = len(faces)
            log.info("faces: "+str(len(faces))+" at "+str(dt.datetime.now()))
    
        # Display the resulting frame
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            pi.set_servo_pulsewidth(17, 1330)
            pi.set_servo_pulsewidth(27, 1540)
            sleep(0.25)
            return False
        # Display the resulting frame
        cv2.imshow('Video', frame)
    elif d == DEBOUNCE_TIME:
        pass
        #print('sleeping')
        #print(d)
#        sleep(.5)
        
    return True
    

def playSound(folder):
    global VOLUME
    files = listdir("/home/pi/really-useful-robot/sounds/"+folder+"/")
    choice = randrange(len(files))
    #print("/home/pi/really-useful-robot/sounds/"+folder+"/" + files[choice])
    subprocess.run(["omxplayer", "--vol", VOLUME, "/home/pi/really-useful-robot/sounds/"+folder+"/" + files[choice]])
    

while True:
    if not video_capture.isOpened():
        print('Unable to load camera.')
        sleep(5)
        pass

    # Capture frame-by-frame
    ret, frame = video_capture.read()
    frame = cv2.flip(frame, -1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    if (len(faces) == 0):
        manageState(False, found, debounce)
    else:
        manageState(True, found, debounce)

    if manageDisplay(debounce) == False:
        break;

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()

