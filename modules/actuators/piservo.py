import RPi.GPIO as GPIO  # Imports the standard Raspberry Pi GPIO library
import threading
from modules.config import Config
from time import sleep
from pubsub import pub

class PiServo:

    def __init__(self, pin, pwm_range, **kwargs):
        self.pin = pin
        self.range = pwm_range
        self.start = kwargs.get('start_pos', 50)
        GPIO.setmode(GPIO.BOARD)                # Sets the pin numbering system to use the physical layout

        GPIO.setup(self.pin, GPIO.OUT)          # Sets up pin to an output (instead of an input)
        self.p = GPIO.PWM(self.pin, 50)         # Sets up pin as a PWM pin
        self.p.start(self.start)                # Starts running PWM on the pin and sets it to the start position

        pub.subscribe(self.mood, 'mood')

    def __del__(self):
        self.p.stop()                           # At the end of the program, stop the PWM
        GPIO.cleanup()                          # Resets the GPIO pins back to defaults

    def move(self, pos):
        self.p.ChangeDutyCycle(pos)             # Changes the pulse width (to move the servo)
        sleep(1)                                # @TODO: Remove this sleep
        
    def mood(self, mood):
        if mood == 'happy':
            self.move(10)  # @TODO: Finalise these values and moods. Make them configurable in yaml
        elif mood == 'sad':
            self.move(50)
        elif mood == 'angry':
            self.move(90)
        else:
            self.move(0)