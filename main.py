from modules.pins import Pins
from modules.servo import Servo
# from modules.rgb import RGB
from modules.vision import Vision
from modules.tracking import Tracking
from modules.stepperMotor import StepperMotor
print("Loading...")

import curses  # keyboard input


def main():
    print("Main function")
    tilt = Servo(Pins.servoTop, (1560, 1880), 60)
    pan = Servo(Pins.servoBottom, (560, 2450))
    # rgb = RGB(Pins.ledRed,Pins.ledGreen,Pins.ledBlue)
    vision = Vision('motion', True)
    tracking = Tracking(vision, pan, tilt)
    stepper = StepperMotor(Pins.stepper1, Pins.stepper2, Pins.stepper3, Pins.stepper4)

    # Configure keyboard input
    stdscr = curses.initscr()
    stdscr.keypad(True)
    curses.cbreak()
    curses.noecho()

    
    loop = True
    
    while loop:
        try:
            # rgb.breathe(Pins.ledRed)
            #rgb.breathe(Pins.ledGreen)
            #rgb.breathe(Pins.ledBlue)
            pan.move(45)
            pan.move(55)
            tilt.move(0)
            tilt.move(100)

            # for i in range(2048):
            #     stepper.doСlockwiseStep()

            key = stdscr.getkey()
            if key == "KEY_LEFT":
                pan.move_relative(10)
            elif key == "KEY_RIGHT":
                pan.move_relative(-10)
            elif key == "KEY_UP":
                tilt.move_relative(10)
            elif key == "KEY_DOWN":
                tilt.move_relative(-10)
            else:
                print(key)

            # tracking.track_largest_match()
        except KeyboardInterrupt as e:
            print('EXITING!')
            pan.reset()
            tilt.reset()
            # rgb.reset()
            loop = False
    
if __name__ == '__main__':
    main()
