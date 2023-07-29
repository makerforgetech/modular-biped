from pubsub import pub
from time import sleep
import pyttsx3

class TTS:
    
    def __init__(self, **kwargs):
        self.translator = kwargs.get('translator', None)
        
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        #rate = engine.getProperty('rate')
        #engine.setProperty('rate', rate+100)
        #for i in voices:
        engine.setProperty('voice', voices[10].id)
        print('voice' + voices[10].id)
        #engine.say('Hello, World!')
        #engine.runAndWait()
        self.engine = engine

        # Set subscribers
        pub.subscribe(self.speak, 'tts')

    def speak(self, msg):
        pub.sendMessage('log', msg="[TTS] {}".format(msg))
        if self.translator is not None:
            msg = self.translator.request(msg)
        self.engine.say(msg)
        self.engine.runAndWait()
        
if __name__ == '__main__':
    tts = TTS()
    tts.speak('Test')
