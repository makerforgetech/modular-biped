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

        self.device = kwargs.get('device_index', self.get_device_index('lp'))
        self.sample_rate = kwargs.get('sample_rate', 16000)

        self.mic = sr.Microphone(device_index=self.device, sample_rate=self.sample_rate)
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

    def get_device_index(self, device_name):
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            # print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
            if name == device_name:
                pub.sendMessage('log', msg='[Speech] Mapping mic to index ' + str(index))
                return index

    def detect(self):
        """
        Not background
        :return:
        """
        pub.sendMessage('log', msg='[Speech] Initialising Detection')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            pub.sendMessage('log', msg='[Speech] Detecting...')
            while self.listening:
                try:
                    audio = self.recognizer.listen(source)#, timeout=10, phrase_time_limit=5)
                    pub.sendMessage('led', identifiers='top5', color='white')
                    # pub.sendMessage('log', msg='[Speech] End Detection')

                    val = self.recognizer.recognize_google(audio)
                    pub.sendMessage('log', msg='[Speech] I heard: ' + str(val))
                    pub.sendMessage('speech', msg=val.lower())
                except sr.WaitTimeoutError as e:
                    pub.sendMessage('log:error', msg='[Speech] Timeout Error: ' + str(e))
                except sr.UnknownValueError as e:
                    pass
                    # pub.sendMessage('log:error', msg='[Speech] Detection Error: ' + str(e))
                finally:
                    pub.sendMessage('led', identifiers='top5', color='off')

    def stop(self):
        self.listening = False
        pub.sendMessage('log', msg='[Speech] Stopping')