from modules.pins import Pins
from modules.servo import Servo
# from modules.rgb import RGB
from modules.vision import Vision
from modules.tracking import Tracking
from modules.stepper import StepperMotor
from time import sleep
print("Loading...")

import curses  # keyboard input


def main(stdscr):
    print("Main function")
    tilt = Servo(Pins.servoTop, (1560, 1880), 40)
    pan = Servo(Pins.servoBottom, (560, 2450), 55)
    # rgb = RGB(Pins.ledRed,Pins.ledGreen,Pins.ledBlue)
    vision = Vision('motion', True)
    tracking = Tracking(vision, pan, tilt)
    stepper = StepperMotor(Pins.stepper1, Pins.stepper2, Pins.stepper3, Pins.stepper4)

    # Configure keyboard input
    #stdscr = curses.initscr()
    stdscr.keypad(True)
    curses.cbreak()
    curses.noecho()

    loop = True
    
    while loop:
        try:
            # rgb.breathe(Pins.ledRed)
            # rgb.breathe(Pins.ledGreen)
            # rgb.breathe(Pins.ledBlue)
#            pan.move(30)
#            pan.move(70)
#            tilt.move(30)
#            tilt.move(70)

            # for i in range(2048):
            #     stepper.doСlockwiseStep()

            # Manual keyboard input for puppeteering
            key = stdscr.getkey()
            stdscr.clear()
            if key == "KEY_LEFT":
                pan.move_relative(5)
            elif key == "KEY_RIGHT":
                pan.move_relative(-5)
            elif key == "KEY_UP":
                tilt.move_relative(30)
            elif key == "KEY_DOWN":
                tilt.move_relative(-30)
            elif key == ord('w'):
                stepper.doСlockwiseStep()
            elif key == ord('s'):
                stepper.doСounterclockwiseStep()
            else:
                print(key)  # tell me what the key is

            # tracking.track_largest_match()

        except (KeyboardInterrupt, ValueError) as e:
            print('EXITING!')
            pan.reset()
            tilt.reset()
            # rgb.reset()
            loop = False
    
if __name__ == '__main__':
    curses.wrapper(main)
