from modules.pins import Pins
from modules.servo import Servo
from modules.rgb import RGB

print("Loading...")


def main():
    print("Main function")
    top = Servo(Pins.servoTop, (1280, 2050))
    bottom = Servo(Pins.servoBottom, (560, 2450))
    rgb = RGB(Pins.ledRed,Pins.ledGreen,Pins.ledBlue)
    
    loop = True
    
    while loop:
        try:
            rgb.breathe(Pins.ledRed)
            rgb.breathe(Pins.ledGreen)
            rgb.breathe(Pins.ledBlue)
            top.move(0)
            top.move(100)
            bottom.move(0)
            bottom.move(100)
        except KeyboardInterrupt as e:
            print('EXITING!')
            top.reset()
            bottom.reset()
            rgb.reset()
            loop = False
    
if __name__ == '__main__':
    main()
