# Move the mouse anywhere in the game window to record the position.
import json
import pygame # pip install pygame

import os
import datetime
# from numpy import interp

filename = "../animations/" + datetime.datetime.now().strftime("%I:%M:%S %B-%d-%Y") + ".json"
f = open(filename,"w+")
tstart = datetime.datetime.now()
tstep = tstart

from pygame.locals import *  #just so that some extra functions work
pygame.init() #this turns pygame 'on'


MAX_X = 640
MAX_Y = 480

x = y = 0
running = 1
screen = pygame.display.set_mode((MAX_X, MAX_Y))

animations = []

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

while running:
    event = pygame.event.poll()
    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
        running = 0
        f.write(json.dumps(animations))
        print(json.dumps(animations))
    elif event.type == pygame.MOUSEMOTION:
        x, y = event.pos
        x = translate(x, 0, MAX_X, -1, 1)
        y = translate(y, 0, MAX_Y, -1, 1)
        print("mouse at " + str(x) + ', ' + str(y))

        # f.write(str({"x": x, "y": y, "t": (datetime.datetime.now() - tstart).microseconds}) + ',')
        animations.append({"x": x, "y": y, "t": (datetime.datetime.now() - tstep).total_seconds()})
        tstep = datetime.datetime.now()
        # if event.pos == (MAX_X / 2, MAX_Y / 2):
        #     screen = pygame.display.set_mode((400, 500))
    screen.fill((0, 0, 0))
    pygame.display.flip()

