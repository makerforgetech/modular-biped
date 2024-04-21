import RPi.GPIO as GPIO
import time

from pubsub import pub

from modules.melodies.deck_the_halls import MelodyDeckTheHalls
from modules.melodies.happy_birthday import MelodyHappyBirthday
from modules.melodies.notes import MelodyNotes


class Buzzer:
    def buzz(self, frequency, length):  # create the function "buzz" and feed it the pitch and duration)

        if (frequency == 0):
            time.sleep(length)
            return
        period = 1.0 / frequency  # in physics, the period (sec/cyc) is the inverse of the frequency (cyc/sec)
        delayValue = period / 2  # calcuate the time for half of the wave
        numCycles = int(length * frequency)  # the number of waves to produce is the duration times the frequency

        for i in range(numCycles):  # start a loop from 0 to the variable "cycles" calculated above
            GPIO.output(self.pin, True)  # set pin 27 to high
            time.sleep(delayValue)  # wait with pin 27 high
            GPIO.output(self.pin, False)  # set pin 27 to low
            time.sleep(delayValue)  # wait with pin 27 low


    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)
        GPIO.setup(pin, GPIO.OUT)

        pub.subscribe(self.speech, 'speech')

        # print("MERRY CHRISTMAS")
        # self.play(MelodyHappyBirthday.MELODY, MelodyHappyBirthday.TEMPO, MelodyHappyBirthday.PAUSE, MelodyHappyBirthday.PACE)
        # self.deck_the_halls()


    def __del__(self):
        GPIO.cleanup()  # Release resource

    def speech(self, msg):
        if 'merry christmas' in msg:
            self.deck_the_halls()
        if 'birthday today' in msg:
            self.play(MelodyHappyBirthday.MELODY, MelodyHappyBirthday.TEMPO, MelodyHappyBirthday.PAUSE,
                      MelodyHappyBirthday.PACE)

    def deck_the_halls(self):
        self.play(MelodyDeckTheHalls.MELODY, MelodyDeckTheHalls.TEMPO, MelodyDeckTheHalls.PAUSE, MelodyDeckTheHalls.PACE)

    def play(self, melody, tempo, pause, pace=0.800):
        for i in range(0, len(melody)):  # Play song

            noteDuration = pace / tempo[i]
            if type(melody[i]) is not int:
                melody[i] = MelodyNotes.notes[melody[i]]
            self.buzz(melody[i], noteDuration)  # Change the frequency along the song note

            pauseBetweenNotes = noteDuration * pause
            time.sleep(pauseBetweenNotes)