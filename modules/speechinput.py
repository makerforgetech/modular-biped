import speech_recognition as sr
from pubsub import pub

class SpeechInput:
    """
    Use speech_recognition to detect and interpret audio
    """
    def __init__(self, **kwargs):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.listening = False

        pub.subscribe(self.enable, 'hotword')

    def enable(self):
        self.listening = True

    def detect(self):
        if not self.listening:
            return None
        print('setting up speech recognition')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print('listening')
            audio = self.recognizer.listen(source)
        print('done listening')
        try:
            val = self.recognizer.recognize_google(audio)
            self.listening = False
            return val
        except sr.UnknownValueError:
            return None




    def detect_from_file(self, file):
        f = sr.AudioFile(file)
        with f as source:
            audio = self.recognizer.record(source)
        return self.recognizer.recognize_sphinx(audio)
