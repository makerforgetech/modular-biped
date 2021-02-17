import time
from pubsub import pub
from modules.arduinoserial import ArduinoSerial
import pysine

# @todo refactor to use pi buzzer
class Braillespeak:
    """
    Communicate with tones, letters converted to tone pairs
    """
    def __init__(self, audio_en_pin, **kwargs):
        pub.subscribe(self.send, 'speak')
        self.audio_en_pin = audio_en_pin
        self.duration = kwargs.get('duration', 100 / 1000)  # ms to seconds

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

    def handle_char(self, char):
        if char == ' ':
            time.sleep(self.duration)
            return

        for n in self.brailleLetters[ord(char) - 97]:
            pysine.sine(frequency=self.notes[n], duration=self.duration)
        time.sleep(self.duration / 2)

    def send(self, message):
        print(message)
        if message:
            pub.sendMessage('serial', type=ArduinoSerial.DEVICE_PIN, identifier=self.audio_en_pin, message=1)
            for t in message:
                self.handle_char(t)
            pub.sendMessage('serial', type=ArduinoSerial.DEVICE_PIN, identifier=self.audio_en_pin, message=0)