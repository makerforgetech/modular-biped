#!/usr/bin/env python

import RPi.GPIO as GPIO
import subprocess

GPIO.setmode(GPIO.BCM)
GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.wait_for_edge(3, GPIO.FALLING)

print('Detected falling')

#subprocess.call(['shutdown', '-h', 'now'], shell=False)
