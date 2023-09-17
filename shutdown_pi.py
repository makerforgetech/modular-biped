#!/usr/bin/env python

import RPi.GPIO as GPIO
import subprocess

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.wait_for_edge(26, GPIO.FALLING)

subprocess.call(['pkill', '-f', 'main.py'], shell=False) # ana scripti güvenle sonlandır
subprocess.call(['shutdown', '-h', 'now'], shell=False)  # cihazın falling anında hemen kapanmasını sağlar 

