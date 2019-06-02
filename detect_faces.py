import cv2
import sys
import logging as log
import datetime as dt
from time import sleep
import subprocess
from os import listdir
from random import randrange

cascPath = "/home/pi/really-useful-robot/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascPath)
log.basicConfig(filename='webcam.log',level=log.INFO)

video_capture = cv2.VideoCapture(0)
anterior = 0
found = False
DEBOUNCE_TIME = 3
debounce = DEBOUNCE_TIME
VOLUME = '-3000'

DISPLAY_ON_SCREEN = True

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
        if anterior != len(faces):
            anterior = len(faces)
            log.info("faces: "+str(len(faces))+" at "+str(dt.datetime.now()))
    
        # Display the resulting frame
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False
        # Display the resulting frame
        cv2.imshow('Video', frame)
    elif d == DEBOUNCE_TIME:
        #print('sleeping')
        #print(d)
        sleep(.5)
        
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
    frame = cv2.flip(frame, 0)

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

