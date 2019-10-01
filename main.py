try:
    import pigpio
except ModuleNotFoundError as e:
    from modules.mocks.mock_pigpio import MockPiGPIO
    import pigpio
    from modules.mocks.mock_cv2 import MockCV2

# Import modules
# from modules import *
from modules.config import Config
from modules.actuators.servo import Servo
from modules.vision import Vision
from modules.tracking import Tracking
from modules.actuators.stepper import StepperMotor
from modules.actuators.linear_actuator import LinearActuator
from modules.animate import Animate
from modules.power import Power
from modules.keyboard import Keyboard
from modules.pixels import NeoPixel


def main():
    # GPIO Management
    pi = pigpio.pi()

    # Power Management
    power = Power(Config.POWER_ENABLE_PIN, pi=pi)

    # Actuators
    tilt = Servo(Config.TILT_PIN, Config.TILT_RANGE, start_pos=Config.TILT_START_POS, power=power, pi=pi)
    pan = Servo(Config.PAN_PIN, Config.PAN_RANGE, start_pos=Config.PAN_START_POS, power=power, pi=pi)
    stepper = StepperMotor(Config.LEG_PINS, power=power)
    leg = LinearActuator(Config.LEG_PINS, Config.LEG_RANGE, Config.LEG_START_POS, power=power)
    animate = Animate(pan, tilt)
         
    
    # Vision / Tracking
    vision = Vision(preview=True)
    #tracking = Tracking(vision, pan, tilt)

    # Pixels
    #px = NeoPixel(Config.PIXEL_PIN, Config.PIXEL_COUNT)
    #px.set(0, (0, 0, 255))

    # Keyboard Input
    key_mappings = {
        Keyboard.KEY_LEFT: (pan.move_relative, 5),
        Keyboard.KEY_RIGHT: (pan.move_relative, -5),
        Keyboard.KEY_UP: (tilt.move_relative, 30),
        Keyboard.KEY_DOWN: (tilt.move_relative, -30),
        Keyboard.KEY_BACKSPACE: (stepper.c_step, None),
        Keyboard.KEY_RETURN: (stepper.cc_step, None),
        ord('h'): (animate.animate, 'head_shake')
    }
    keyboard = Keyboard(mappings=key_mappings)

    loop = True
    while loop:
        try:
            #stepper.setDelay()
            # Manual keyboard input for puppeteering
            key = keyboard.handle_input()
            if 49 <= key <= 57:
                stepper.manual_step(key-48)
            if key == ord('q'):
                loop = False
            else:
                print(key)
            vision.detect()
            # tracking.track_largest_match()
        except (KeyboardInterrupt, ValueError) as e:
            loop = False
            print(e)


if __name__ == '__main__':
    main()
