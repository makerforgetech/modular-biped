from time import sleep
import curses  # keyboard input
import pigpio

# Import modules
from modules.pins import Pins
from modules.actuators.servo import Servo
# from modules.rgb import RGB
from modules.vision import Vision
from modules.tracking import Tracking
from modules.actuators.stepper import StepperMotor
from modules.actuators.linear_actuator import LinearActuator
from modules.animate import Animate
from modules.power import Power


def main(stdscr):
    print("Main function")
    pi = pigpio.pi()
    power = Power(Pins.powerEnabledPin, pi=pi)
    tilt = Servo(Pins.servoTop, (1560, 1880), start_pos=40, power=power, pi=pi)
    pan = Servo(Pins.servoBottom, (560, 2450), start_pos=55, power=power, pi=pi)
    # rgb = RGB(Pins.ledRed,Pins.ledGreen,Pins.ledBlue)
    vision = Vision('motion', True)
    tracking = Tracking(vision, pan, tilt)
    stepper = StepperMotor(Pins.stepper1, Pins.stepper2, Pins.stepper3, Pins.stepper4, power=power)
    leg = LinearActuator(Pins.stepper1, Pins.stepper2, Pins.stepper3, Pins.stepper4, (0, 100), 0, power=power)
    animate = Animate(pan, tilt, 'animations')

    # Configure keyboard input
    #stdscr = curses.initscr()
    stdscr.keypad(True)
#    curses.cbreak()
#    curses.noecho()

    loop = True

    # @todo use this instead of if/else blocks
    key_mappings = {
        'KEY_LEFT': {pan.move_relative, 5},
        'KEY_RIGHT': {pan.move_relative, -5},
        'KEY_UP': {tilt.move_relative, 30},
        'KEY_DOWN': {tilt.move_relative, -30},
        ord('w'): {stepper.doСlockwiseStep},
        ord('s'): {stepper.doСounterclockwiseStep},
        ord('h'): {animate.animate, 'head_shake'}
    }

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
            
#            stdscr.clear()
#            key = ''
            print(key)
#            print(ord("KEY_LEFT"))
            if key == "KEY_LEFT":
                pan.move_relative(5)
            elif key == "KEY_RIGHT":
                pan.move_relative(-5)
            elif key == "KEY_UP":
                tilt.move_relative(30)
            elif key == "KEY_DOWN":
                tilt.move_relative(-30)
            else:
                ch = stdscr.getch() # @todo this is wrong, it requires input twice
                print(ch)
                if ch == ord('w'):
                    stepper.doСlockwiseStep()
                elif ch == ord('s'):
                    stepper.doСounterclockwiseStep()
                elif ch == ord('h') or ch == 'h':
                    print('head_shake')
                    animate.animate('head_shake')
                elif ch == ord('n'):
                    print('head_swirl')
                    animate.animate('head_swirl')                
                else:
                    print(ch)  # tell me what the key is

            # tracking.track_largest_match()

        except (KeyboardInterrupt, ValueError) as e:
            print('EXITING!')
            pan.reset()
            tilt.reset()
            # rgb.reset()
            loop = False
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
    
if __name__ == '__main__':
    curses.wrapper(main)
