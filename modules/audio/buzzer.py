from gpiozero import TonalBuzzer
from gpiozero.tones import Tone
import time

from pubsub import pub

from modules.audio.melodies.deck_the_halls import MelodyDeckTheHalls
from modules.audio.melodies.happy_birthday import MelodyHappyBirthday
from modules.audio.melodies.notes import MelodyNotes

class Buzzer:
    def __init__(self, **kwargs):
        """
        Buzzer class
        :param kwargs: pin
        
        Install: pip install gpiozero
        
        Subscribe to 'play' and 'buzz' events
        
        Example:
        pub.sendMessage('play', song="happy birthday") # Also available: 'merry christmas'
        pub.sendMessage('buzz', frequency=440, length=0.5)
        
        """
        self.pin = kwargs.get('pin')
        self.buzzer = TonalBuzzer(self.pin)

        pub.subscribe(self.play_song, 'play')
        pub.subscribe(self.buzz, 'buzz')
        
    def buzz(self, frequency, length):
        """
        Buzz the buzzer
        :param frequency: Frequency of the buzz
        :param length: Length of the buzz
        """
        if (frequency == 0):
            time.sleep(length)
            return
        self.buzzer.play(Tone(frequency))
        time.sleep(length)
        self.buzzer.stop()

    def play_song(self, song):
        """
        Play a song
        :param song: Song to play
        """
        if 'merry christmas' in song:
            self.play(MelodyDeckTheHalls.MELODY, MelodyDeckTheHalls.TEMPO, MelodyDeckTheHalls.PAUSE, MelodyDeckTheHalls.PACE)
        if 'happy birthday' in song:
            self.play(MelodyHappyBirthday.MELODY, MelodyHappyBirthday.TEMPO, MelodyHappyBirthday.PAUSE,
                      MelodyHappyBirthday.PACE)
        self.buzzer.stop()

    def play(self, melody, tempo, pause, pace=0.800):
        """
        Play a melody
        :param melody: Melody to play
        :param tempo: Tempo of the melody
        :param pause: Pause between notes
        :param pace: Pace of the melody
        
        See `melodies` for examples
        """
        for i in range(0, len(melody)):  # Play song

            noteDuration = pace / tempo[i]
            if type(melody[i]) is not int:
                melody[i] = MelodyNotes.notes[melody[i]]
            self.buzz(melody[i], noteDuration)  # Change the frequency along the song note

            pauseBetweenNotes = noteDuration * pause
            time.sleep(pauseBetweenNotes)