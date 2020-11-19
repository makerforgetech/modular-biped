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
from modules.hotword import HotWord
from modules.chirp import Chirp
from modules.speechinput import SpeechInput
# from modules.chatbot.chatbot import MyChatBot
from modules.arduinoserial import ArduinoSerial
from modules.led import LED
from modules.personality import Personality
from modules.battery import Battery

MODE_TRACK_MOTION = 0
MODE_TRACK_FACES = 1
MODE_SLEEP = 2
MODE_ANIMATE = 3
MODE_OFF = 4
MODE_KEYBOARD = 5
MODE_RANDOM_BEHAVIOUR = 6


def main():
    # GPIO Management
    pi = pigpio.pi()

    # Power Management
    # power = None# Power(Config.POWER_ENABLE_PIN, pi=pi)

    # Arduino connection
    serial = ArduinoSerial()

    # Actuators
    tilt = Servo(Config.TILT_PIN, Config.TILT_RANGE, start_pos=Config.TILT_START_POS, serial=serial)
    pan = Servo(Config.PAN_PIN, Config.PAN_RANGE, start_pos=Config.PAN_START_POS, serial=serial)
    neck = Servo(Config.NECK_PIN, Config.NECK_RANGE, start_pos=Config.NECK_START_POS, serial=serial)

    led = LED(Config.LED_COUNT)
    signal.signal(signal.SIGTERM, led.exit)
    #serial.send(ArduinoSerial.DEVICE_PIN, 12, 1)
    #sleep(5)
    #serial.send(ArduinoSerial.DEVICE_PIN, 12, 0)

    # animate = Animate(pan, tilt)
    motion = Sensor(Config.MOTION_PIN, pi=pi)

    # Vision / Tracking
    vision = Vision(preview=True, mode=Vision.MODE_FACES)
    # tracking = Tracking(vision, pan, tilt)

    # Voice
    hotword = HotWord(Config.HOTWORD_MODEL)
    hotword.start()  # @todo can these be moved into hotword?
    #hotword.start_recog(sleep_time=Config.HOTWORD_SLEEP_TIME)
    sleep(1)  # @todo is this needed?

    speech = SpeechInput()

    # Chat bot
    # chatbot = MyChatBot()

    # Output
    chirp = Chirp()

    # Keyboard Input
    key_mappings = {
        Keyboard.KEY_LEFT: (pan.move_relative, 5),
        Keyboard.KEY_RIGHT: (pan.move_relative, -5),
        Keyboard.KEY_UP: (tilt.move_relative, 5),
        Keyboard.KEY_DOWN: (tilt.move_relative, -5),
        Keyboard.KEY_BACKSPACE: (neck.move_relative, 5),
        Keyboard.KEY_RETURN: (neck.move_relative, -5),
        ord('l'): (led.flashlight, True),
        ord('o'): (led.flashlight, False),
        ord('c'): (chirp.send, 'hi')
        # ord('h'): (animate.animate, 'head_shake')
    }
    keyboard = None

    # Initialise mode
    mode = MODE_RANDOM_BEHAVIOUR

    personality = Personality(debug=True)

    #animate.animate('wake')
    # px.blink(Config.PIXEL_EYES, (0, 0, 255))

    # chirp.send('Hi!')

    if mode == MODE_RANDOM_BEHAVIOUR:
        start = time()  # random behaviour trigger
        random.seed()
        delay = random.randint(1, 5)
        action = 1
        # chirp.send('hi')

    battery = Battery(0, serial)

    loop = True
    try:
        while loop:

            # print(serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, None))
            if not battery.safe_voltage():
                subprocess.call(['shutdown', '-h'], shell=False)
                loop = False
                quit()
            sleep(2)
            continue

            """
            Basic behaviour:
            
            If asleep, wait for movement using microwave sensor then wake
            If awake, look for motion. 
            |-- If motion detected move to top of largest moving object then look for faces
               |-- If faces detected, track largest face 
            |-- If no motion detected for defined period, go to sleep
            
            If waiting for keyboard input, disable motion and facial tracking
            """

            personality.behave()
            #print(motion.read())
            #print((datetime.datetime.now() - vision.last_match).total_seconds())



            if mode == MODE_RANDOM_BEHAVIOUR:
                if time() - start > delay:

                    if action == 1:
                        led.eye('green')
                    elif action == 2:
                        pan.move_relative(15)
                    elif action == 3:
                        pan.move_relative(-15)
                    elif action == 4:
                        tilt.move_relative(15)
                    elif action == 5:
                        tilt.move_relative(-15)
                    elif action == 6:
                        led.set(Config.LED_MIDDLE, (random.randint(0, 5), random.randint(0, 5), random.randint(0, 5)))

                    action = action + 1
                    if action == 7:
                        action = 1
                    start = time()
                    delay = random.randint(2, 15)

                    # vision.detect()
                    print(delay)

            elif mode == MODE_SLEEP:
                if motion.read() == 1:
                    mode = MODE_TRACK_FACES
                    #animate.animate('wake')
                    #tilt.reset()
                    vision.last_match = datetime.datetime.now()
                    print("Motion!")
                    led.eye('green')
                    # listening = True
                else:
                    sleep(1)

            elif mode == MODE_TRACK_MOTION:
                if vision.mode != Vision.MODE_MOTION:
                    vision = Vision(mode=Vision.MODE_MOTION)
                    print('Looking for motion')
                # if tracking.track_largest_match():
                #     mode = MODE_TRACK_FACES
                #     chirp.send('Looking for faces')

            elif mode == MODE_TRACK_FACES:
                if vision.mode != Vision.MODE_FACES:
                    vision = Vision(mode=Vision.MODE_FACES)
                    print('Looking for faces')
                # if not tracking.track_largest_match():
                #     #mode = MODE_TRACK_MOTION
                #     #print('No face, switching to motion')
                #     pass

            elif mode == MODE_KEYBOARD:
                if keyboard is None:
                    keyboard = Keyboard(mappings=key_mappings)
                # Manual keyboard input for puppeteering
                key = keyboard.handle_input()
                if key == ord('q'):
                    loop = False
                elif key == ord('d'):
                    serial.send(ArduinoSerial.DEVICE_SERVO, 8, 0)
                #else:
                #    chirp.send(key)

            # Sleep if nothing has been detected for a while
            if (mode == MODE_TRACK_MOTION or mode == MODE_TRACK_FACES) and \
                    vision.last_match < datetime.datetime.now() - datetime.timedelta(minutes=Config.SLEEP_TIMEOUT):
                mode = MODE_SLEEP
                #pan.reset()
                #tilt.move(0)
                print('Sleeping')
                led.eye('red')
                sleep(3)

            # repeat what I hear
            voice_input = speech.detect()
            if voice_input:
                print(voice_input)
                if voice_input == 'shut down':
                    loop = False
                    quit()
                elif voice_input == 'light on':
                    led.flashlight(True)
                elif voice_input == 'light off':
                    led.flashlight(False)

                # print('response:')
                # print(chatbot.get_response(voice_input)) # @todo This is awful, improve

    except (KeyboardInterrupt, ValueError) as e:
        print(e)
        loop = False
        quit()

    finally:
        led.exit()
        #chirp.send('off')
        chirp.exit()
        hotword.exit()
        # pan.reset()
        # tilt.reset()

if __name__ == '__main__':
    main()
