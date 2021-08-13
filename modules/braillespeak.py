import time
from pubsub import pub
import RPi.GPIO as GPIO
#import pysine  #@todo this breaks the microphone (https://trello.com/c/qNVW2I5O/44-audio-reactions)

class Braillespeak:
    """
    Communicate with tones, letters converted to tone pairs
    """
    def __init__(self, pin, **kwargs):
        pub.subscribe(self.send, 'speak')
        self.pin = pin
        self.speaker = False
        self.duration = kwargs.get('duration', 100 / 1000)  # ms to seconds

        if self.speaker is False:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.IN)
            GPIO.setup(pin, GPIO.OUT)

        # https://pages.mtu.edu/~suits/notefreqs.html
        self.notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C4 - C5

        self.brailleLetters = [
            [4, 0],
            [6, 0],
            [4, 4],
            [4, 6],
            [4, 2],
            [6, 4],
            [6, 6],
            [6, 2],
            [2, 4],
            [2, 6],
            [5, 0],
            [7, 0],
            [5, 4],
            [5, 6],
            [5, 2],
            [7, 4],
            [7, 6],
            [7, 2],
            [3, 4],
            [3, 6],
            [5, 1],
            [7, 1],
            [2, 7],
            [5, 5],
            [5, 7],
            [5, 3]
        ]

    def exit(self):
        pass

    def buzz(self, frequency, length):  # create the function "buzz" and feed it the pitch and duration)
        #https://github.com/gumslone/raspi_buzzer_player/blob/master/buzzer_player.py
        period = 1.0 / frequency  # in physics, the period (sec/cyc) is the inverse of the frequency (cyc/sec)
        delayValue = period / 2  # calculate the time for half of the wave
        numCycles = int(length * frequency)  # the number of waves to produce is the duration times the frequency

        for i in range(numCycles):  # start a loop from 0 to the variable "cycles" calculated above
            GPIO.output(self.pin, True)  # set pin to high
            time.sleep(delayValue)  # wait with pin high
            GPIO.output(self.pin, False)  # set pin to low
            time.sleep(delayValue)  # wait with pin low

    def handle_char(self, char):
        if char == ' ':
            time.sleep(self.duration)
            return

        for n in self.brailleLetters[ord(char) - 97]:
            if self.speaker:
                pass
                #pysine.sine(frequency=self.notes[n], duration=self.duration)
            else:
                self.buzz(self.notes[n], self.duration)
        time.sleep(self.duration / 2)

    def send(self, message):
        print(message.lower())
        if message:
            for t in message.lower():
                self.handle_char(t)
