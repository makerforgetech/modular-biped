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

# from modules.chirp import Chirp
from modules.speechinput import SpeechInput
# from modules.chatbot.chatbot import MyChatBot
from modules.arduinoserial import ArduinoSerial
from modules.led import LED
from modules.personality import Personality
from modules.battery import Battery
from modules.braillespeak import Braillespeak

def main():

    mode = Config.MODE_RANDOM_BEHAVIOUR
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
#    signal.signal(signal.SIGTERM, led.exit) # @todo not sure what this is for anymore - should have added comments

    if Config.MOTION_PIN is not None:
        motion = Sensor(Config.MOTION_PIN, pi=gpio)

    # Vision / Tracking
    vision = Vision(preview=False, mode=Vision.MODE_FACES, rotate=True)
    tracking = Tracking(vision)

    # Voice
    if Config.HOTWORD_MODEL is not None:
        hotword = HotWord(Config.HOTWORD_MODEL)
        hotword.start()  # @todo can these be moved into hotword?
        # hotword.start_recog(sleep_time=Config.HOTWORD_SLEEP_TIME)
        sleep(1)  # @todo is this needed?
        speech = SpeechInput()

    # Output
    if Config.BUZZER_PIN is not None:
        speak = Braillespeak(Config.BUZZER_PIN, duration=80/1000)

    # Keyboard Input
    key_mappings = {
        # @todo these won't work because the mapping is not correct yet. Need to research this
        # Keyboard.KEY_LEFT: (pub.sendMessage, ['servo:pan:mv', 5]),
        # Keyboard.KEY_RIGHT: (pub.sendMessage, {'servo:pan:mv', -5}),
        Keyboard.KEY_UP: (servos['tilt'].move_relative, 5),
        Keyboard.KEY_DOWN: (servos['tilt'].move_relative, -5),
        Keyboard.KEY_BACKSPACE: (servos['neck'].move_relative, 5),
        Keyboard.KEY_RETURN: (servos['neck'].move_relative, -5),

        # LEFT LEG MOVEMENT
        # ord('t'): (leg_l_hip.move_relative, -5),
        # ord('g'): (leg_l_knee.move_relative, -5),
        # ord('b'): (leg_l_ankle.move_relative, -5),
        # ord('w'): (leg_l_hip.move_relative, 5),
        # ord('s'): (leg_l_knee.move_relative, 5),
        # ord('x'): (leg_l_ankle.move_relative, 5),
        #
        # # RIGHT LEG MOVEMENT
        # ord('e'): (leg_r_hip.move_relative, -5),
        # ord('d'): (leg_r_knee.move_relative, -5),
        # ord('c'): (leg_r_ankle.move_relative, -5),
        # ord('r'): (leg_r_hip.move_relative, 5),
        # ord('f'): (leg_r_knee.move_relative, 5),
        # ord('v'): (leg_r_ankle.move_relative, 5),

        # ord('l'): (pub.sendMessage('led:flashlight', on=True)),
        # ord('o'): (pub.sendMessage('led:flashlight', on=False)),
        # ord('c'): (pub.sendMessage('speak', message='hi'))
        # ord('h'): (animate.animate, 'head_shake')
    }

    voice_mappings = {
        'shut down': quit
        # 'light on': (pub.sendMessage('led:flashlight', on=True)),
        # 'light off': (pub.sendMessage('led:flashlight', on=False)),
    }
    keyboard = None

    animate = Animate()
    personality = Personality(debug=True)

    if mode == Config.MODE_RANDOM_BEHAVIOUR or mode == Config.MODE_KEYBOARD:
        start = time()  # random behaviour trigger
        random.seed()
        delay = random.randint(1, 5)
        action = 1
        pub.sendMessage("animate", action="stand")
        if mode == Config.MODE_RANDOM_BEHAVIOUR:
            pub.sendMessage('speak', message='hi')

    battery_check_time = time()

    battery = Battery(0, serial)



    loop = True
    try:
        while loop:
            sleep(1 / Config.LOOP_FREQUENCY)
            """
            Basic behaviour:

            If asleep, wait for movement using microwave sensor then wake
            If awake, look for motion. 
            |-- If motion detected move to top of largest moving object then look for faces
               |-- If faces detected, track largest face 
            |-- If no motion detected for defined period, go to sleep

            If waiting for keyboard input, disable motion and facial tracking
            """

            # personality.behave()

            if battery_check_time < time() - 2:
                battery_check_time = time()
                if not battery.safe_voltage():
                    subprocess.call(['shutdown', '-h'], shell=False)
                    loop = False
                    quit()

            if mode == Config.MODE_RANDOM_BEHAVIOUR:
                if tracking.track_largest_match():
                    pub.sendMessage('led:eye', color="green")
                elif motion.read() <= 0:
                    pub.sendMessage('led:eye', color="red")
                else:
                    pub.sendMessage('led:eye', color="blue")

                if time() - start > delay:
                    # action = action + 1
                    # if action == 6:
                    #     action = 1
                    start = time()
                    delay = random.randint(2, 15)
            elif mode == Config.MODE_KEYBOARD:
                if keyboard is None:
                    keyboard = Keyboard(mappings=key_mappings)
                # Manual keyboard input for puppeteering
                key = keyboard.handle_input()
                if key == ord('q'):
                    loop = False

                elif key == ord('1'):
                    pub.sendMessage("animate", action="sit")
                    print('sit')
                elif key == ord('2'):
                    pub.sendMessage("animate", action="stand")
                    print('stand')
                elif key == ord('3'):
                    pub.sendMessage("animate", action="wake")
                    print('neck up')
                elif key == ord('4'):
                    pub.sendMessage("animate", action="sleep")
                    print('neck down')
                elif key == ord('5'):
                    pub.sendMessage("animate", action="head_shake")
                elif key == ord('6'):
                    pub.sendMessage("animate", action="head_nod")

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
        pub.sendMessage("animate", action="sit")
        pub.sendMessage("animate", action="sleep")
        pub.sendMessage("power:exit")
        led.exit()
        # speak.send('off')

if __name__ == '__main__':
    main()