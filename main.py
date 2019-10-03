try:
    import pigpio
except ModuleNotFoundError as e:
    from modules.mocks.mock_pigpio import MockPiGPIO
    import pigpio
    from modules.mocks.mock_cv2 import MockCV2

import datetime
from time import sleep

# Import modules
# from modules import *
from modules.config import Config
from modules.actuators.servo import Servo
from modules.vision import Vision
from modules.tracking import Tracking
from modules.animate import Animate
from modules.power import Power
from modules.keyboard import Keyboard
from modules.pixels import NeoPixel
from modules.sensor import Sensor

MODE_TRACK_MOTION = 0
MODE_TRACK_FACES = 1
MODE_SLEEP = 2
MODE_ANIMATE = 3
MODE_OFF = 4
MODE_KEYBOARD = 5


def main():
    # GPIO Management
    pi = pigpio.pi()

    # Power Management
    power = Power(Config.POWER_ENABLE_PIN, pi=pi)

    # Actuators
    tilt = Servo(Config.TILT_PIN, Config.TILT_RANGE, start_pos=Config.TILT_START_POS, power=power, pi=pi)
    pan = Servo(Config.PAN_PIN, Config.PAN_RANGE, start_pos=Config.PAN_START_POS, power=power, pi=pi)
    animate = Animate(pan, tilt)
    motion = Sensor(Config.MOTION_PIN, pi=pi)

    # Vision / Tracking
    vision = Vision(preview=False, mode=Vision.MODE_FACES)
    tracking = Tracking(vision, pan, tilt)

    # Pixels
    #px = NeoPixel(Config.PIXEL_PIN, Config.PIXEL_COUNT)
    #px.set(Config.PIXEL_FRONT, (0, 0, 255))
    #px.set(Config.PIXEL_HEAD, (0, 255, 0))

    # Keyboard Input
    key_mappings = {
        Keyboard.KEY_LEFT: (pan.move_relative, 5),
        Keyboard.KEY_RIGHT: (pan.move_relative, -5),
        Keyboard.KEY_UP: (tilt.move_relative, 30),
        Keyboard.KEY_DOWN: (tilt.move_relative, -30),
        # Keyboard.KEY_BACKSPACE: (stepper.c_step, None),
        # Keyboard.KEY_RETURN: (stepper.cc_step, None),
        ord('h'): (animate.animate, 'head_shake')
    }
    keyboard = None

    # Initialise mode
    mode = MODE_TRACK_FACES
    #animate.animate('wake')
    # px.blink(Config.PIXEL_EYES, (0, 0, 255))

    loop = True
    try:
        while loop:
            """
            Basic behaviour:
            
            If asleep, wait for movement using microwave sensor then wake
            If awake, look for motion. 
            |-- If motion detected move to top of largest moving object then look for faces
               |-- If faces detected, track largest face 
            |-- If no motion detected for defined period, go to sleep
            
            If waiting for keyboard input, disable motion and facial tracking
            """
            #print(motion.read())
            #print((datetime.datetime.now() - vision.last_match).total_seconds())

            if mode == MODE_SLEEP:
                if motion.read() == 1:
                    mode = MODE_TRACK_FACES
                    #animate.animate('wake')
                    tilt.reset()
                    vision.last_match = datetime.datetime.now()
                    print("I sense you, I'm awake!")
                else:
                    sleep(1)

            elif mode == MODE_TRACK_MOTION:
                if vision.mode != Vision.MODE_MOTION:
                    vision = Vision(mode=Vision.MODE_MOTION)
                if tracking.track_largest_match():
                    mode = MODE_TRACK_FACES
                    print('Found motion, switching to face recognition')

            elif mode == MODE_TRACK_FACES:
                if vision.mode != Vision.MODE_FACES:
                    vision = Vision(mode=Vision.MODE_FACES)
                if not tracking.track_largest_match():
                    #mode = MODE_TRACK_MOTION
                    #print('No face, switching to motion')
                    pass

            elif mode == MODE_KEYBOARD:
                if keyboard is None:
                    keyboard = Keyboard(mappings=key_mappings)
                # Manual keyboard input for puppeteering
                key = keyboard.handle_input()
                if key == ord('q'):
                    loop = False
                else:
                    print(key)

            # Sleep if nothing has been detected for a while
            if (mode == MODE_TRACK_MOTION or mode == MODE_TRACK_FACES) and \
                    vision.last_match < datetime.datetime.now() - datetime.timedelta(minutes=Config.SLEEP_TIMEOUT):
                mode = MODE_SLEEP
                pan.reset()
                tilt.move(0)
                print('bored now, sleeping')
                sleep(3)

    except (KeyboardInterrupt, ValueError) as e:
        print(e)
        loop = False
        quit()

    finally:
        pan.reset()
        tilt.reset()


if __name__ == '__main__':
    main()
