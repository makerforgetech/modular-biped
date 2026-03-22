import time
#import pysine  #@todo this breaks the microphone (https://trello.com/c/qNVW2I5O/44-audio-reactions)

from modules.base_module import BaseModule

class BrailleSpeak(BaseModule):
    """
    Communicate with tones, letters converted to tone pairs
    Uses Buzzer module to play tones via pubsub
    
    :param kwargs: pin, duration
    
    Subscribes to 'speak' event
    
    Example:
    self.publish('speak', msg="Hi")

    """
    def __init__(self, **kwargs):
        
        self.pin = kwargs.get('pin')
        self.speaker = False
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
        
    def setup_messaging(self):
        self.subscribe('speak', self.send)

    def exit(self):
        pass

    def handle_char(self, char):
        if char == ' ':
            time.sleep(self.duration)
            return

        for n in self.brailleLetters[ord(char) - 97]:
            if self.speaker:
                pass
                #pysine.sine(frequency=self.notes[n], duration=self.duration)
            else:
                self.publish('buzz', frequency=self.notes[n], length=self.duration)
        time.sleep(self.duration / 2)

    def send(self, msg):
        print(msg.lower())
        if msg:
            for t in msg.lower():
                self.handle_char(t)
