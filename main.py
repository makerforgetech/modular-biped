import logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

try:
    import pigpio
except ModuleNotFoundError as e:
    from modules.mocks.mock_pigpio import MockPiGPIO
    import pigpio
    from modules.mocks.mock_cv2 import MockCV2

import datetime
from time import sleep, time
import random
from pubsub import pub
import signal
import subprocess

# Import modules
# from modules import *
from modules.config import Config
from modules.actuators.servo import Servo
from modules.vision import Vision
from modules.tracking import Tracking
from modules.animate import Animate
from modules.power import Power
from modules.keyboard import Keyboard
from modules.sensor import Sensor
try:
    from modules.hotword import HotWord
except ModuleNotFoundError as e:
    pass

import sys
import os

# from modules.chirp import Chirp
from modules.speechinput import SpeechInput
# from modules.chatbot.chatbot import MyChatBot
from modules.arduinoserial import ArduinoSerial
from modules.led import LED
from modules.personality import Personality
from modules.battery import Battery
from modules.braillespeak import Braillespeak

def main():
    mode = Config.MODE_LIVE
    path = os.path.dirname(__file__)
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        mode = Config.MODE_KEYBOARD

    # POWER
    power = Power(Config.POWER_ENABLE_PIN)

    # GPIO
    gpio = pigpio.pi()

    # Arduino connection
    serial = ArduinoSerial()

    servos = dict()
    for key in Config.servos:
        s = Config.servos[key]
        servos[key] = Servo(s['pin'], key, s['range'], start_pos=s['start'])

    led = LED(Config.LED_COUNT)

    # Send exit command when script is terminated
    signal.signal(signal.SIGTERM, Config.exit) # @todo doesn't work all the time, throwing exception for now

    if Config.MOTION_PIN is not None:
        motion = Sensor(Config.MOTION_PIN, pi=gpio)

    # Vision / Tracking
    vision = Vision(mode=Vision.MODE_FACES, rotate=True, path=path)

    tracking_active = False
    if mode == Config.MODE_LIVE:
        tracking_active = True
    tracking = Tracking(vision, active=tracking_active)

    # Voice
    if Config.HOTWORD_MODEL is not None:

        hotword = HotWord(Config.HOTWORD_MODEL)
        hotword.start()  # @todo this starts the thread. can it be moved into hotword?
        # hotword.start_recog(sleep_time=Config.HOTWORD_SLEEP_TIME)
        sleep(1)  # @todo is this needed?
        # @todo this is throwing errors: ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'defaults.bluealsa.device'
        # speech = SpeechInput()

    # Output
    if Config.BUZZER_PIN is not None:
        speak = Braillespeak(Config.BUZZER_PIN, duration=80/1000)

    voice_mappings = {
        'shut down': quit
        # 'light on': (pub.sendMessage('led:flashlight', on=True)),
        # 'light off': (pub.sendMessage('led:flashlight', on=False)),
    }
    keyboard = None
    if mode == Config.MODE_KEYBOARD:
        keyboard = Keyboard()

    animate = Animate()
    personality = Personality(mode=mode, debug=False)

    battery = Battery(0, serial, path=path) # note: needs ref for pubsub to work

    second_loop = time()
    minute_loop = time()
    loop = True
    try:
        while loop:
            pub.sendMessage('loop')
            if time() - second_loop > 1:
                second_loop = time()
                pub.sendMessage('loop:1')
            if time() - minute_loop > 60:
                minute_loop = time()
                pub.sendMessage('loop:60')

            # if Config.HOTWORD_MODEL is not None:
            #     # repeat what I hear
            #     voice_input = speech.detect()
            #     if voice_input:
            #         print(voice_input)
            #         if voice_mappings is not None:
            #             if key in voice_mappings:
            #                 method_info = voice_mappings.get(key)
            #                 if method_info[1] is not None:
            #                     method_info[0](method_info[1])
            #                 else:
            #                     method_info[0]()

    except (Exception) as e:
        print(e)
        loop = False
        sleep(5)
        quit()

    finally:
        pub.sendMessage("exit")
        pub.sendMessage("animate", action="sit")
        pub.sendMessage("animate", action="sleep")
        pub.sendMessage("power:exit")
        # speak.send('off')

if __name__ == '__main__':
    main()
