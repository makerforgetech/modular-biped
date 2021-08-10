import RPi.GPIO as GPIO
import subprocess
import threading


MOTION_PIN = 3
GPIO.setmode(GPIO.BCM)  # set up BCM GPIO numbering
GPIO.setup(MOTION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Detect motion from PIR or microwave sensor on pin MOTION_PIN
# Also supports switch. If input of MOTION_PIN is set to HIGH (switch on), shutdown timer is cancelled.
# If input is low, shutdown will occur in 60 seconds unless HIGH input is received again from switch or motion sensor.

def detect_motion(channel):
    global MOTION_PIN
    global timer

    if GPIO.input(MOTION_PIN):
        print("Rising")
        timer.cancel()

    else:
        print("Falling")
        timer.start()


def shutdown():
    subprocess.call(['shutdown', '-h', 'now'], shell=False)


timer = threading.Timer(60.0, shutdown)


# else is happening in the program, the function my_callback will be run
GPIO.add_event_detect(MOTION_PIN, GPIO.BOTH, callback=detect_motion)

