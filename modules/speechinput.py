import speech_recognition as sr
from pubsub import pub
from time import sleep
from threading import Thread

class SpeechInput:
    """
    Use speech_recognition to detect and interpret audio
    """
    def __init__(self, **kwargs):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1
        self.device = kwargs.get('device_index', 0)
        print('device ' + str(self.device))
        self.mic = sr.Microphone(device_index=self.device)
        self.listening = False

        pub.subscribe(self.start, 'wake')
        pub.subscribe(self.stop, 'rest')
        pub.subscribe(self.stop, 'sleep')
        pub.subscribe(self.stop, 'exit')

    def __del__(self):
        self.stop()

    def start(self):
        self.listening = True
        Thread(target=self.detect, args=()).start()
        return self

    def detect(self):
        """
        Not background
        :return:
        """
        pub.sendMessage('log', msg='[Speech] Initialising Detection')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)

            while self.listening:
                pub.sendMessage('log', msg='[Speech] Detecting...')

                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                pub.sendMessage('led:eye', color='white')
                pub.sendMessage('log', msg='[Speech] End Detection')
                try:
                    val = self.recognizer.recognize_google(audio)
                    pub.sendMessage('log', msg='[Speech] I heard: ' + str(val))
                    pub.sendMessage('speech', msg=val.lower())
                    pub.sendMessage('led:eye', color='red')
                except sr.UnknownValueError as e:
                    pub.sendMessage('log:error', msg='[Speech] Detection Error: ' + str(e))
                finally:
                    pub.sendMessage('led:eye', color='off')

    def stop(self):
        self.listening = False
        pub.sendMessage('log', msg='[Speech] Stopping')