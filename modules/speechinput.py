import speech_recognition as sr


class SpeechInput:
    """
    Use speech_recognition to detect and interpret audio
    """
    def __init__(self, **kwargs):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

    def detect(self):
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        return self.recognizer.recognize_sphinx(audio)

    def detect_from_file(self, file):
        f = sr.AudioFile(file)
        with f as source:
            audio = self.recognizer.record(source)
        return self.recognizer.recognize_sphinx(audio)
