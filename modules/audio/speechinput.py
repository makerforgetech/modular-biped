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
        self.recognizer.pause_threshold = 2

        self.device_name = kwargs.get('device_name', 'lp')
        self.device = self.get_device_index(self.device_name)
        self.sample_rate = kwargs.get('sample_rate', 16000)

        self.mic = sr.Microphone(device_index=self.device, sample_rate=self.sample_rate)
        self.listening = False

        pub.subscribe(self.start, 'speech:listen')
        pub.subscribe(self.stop, 'rest')
        pub.subscribe(self.stop, 'sleep')
        pub.subscribe(self.stop, 'exit')
        
        if kwargs.get('start_on_boot', True):
            self.start()

    def __del__(self):
        self.stop()

    def start(self):
        self.listening = True
        Thread(target=self.detect, args=()).start()
        return self

    def get_device_index(self, device_name):
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
            if name == device_name:
                pub.sendMessage('log', msg='[Speech] Mapping mic to index ' + str(index))
                print('Mapping mic to index ' + str(index))
                return index

    def detect(self):
        """
        Not background
        :return:
        """
        pub.sendMessage('log', msg='[Speech] Initialising Detection')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            # self.recognizer.energy_threshold = 300  # Adjust based on your environment
            pub.sendMessage('log', msg='[Speech] Detecting...')
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                    # pub.sendMessage('led', identifiers='top5', color='white')
                    # pub.sendMessage('log', msg='[Speech] End Detection')
                    with open("speech.wav", "wb") as f:
                        f.write(audio.get_wav_data())

                    val = self.recognizer.recognize_google(audio)
                    pub.sendMessage('log', msg='[Speech] I heard: ' + str(val))
                    pub.sendMessage('speech', text=val.lower())
                    pub.sendMessage('tts', msg='I heard ' + val.lower())
                except sr.WaitTimeoutError as e:
                    pub.sendMessage('log:error', msg='[Speech] Timeout Error: ' + str(e))
                except sr.UnknownValueError as e:
                    pass
                    # pub.sendMessage('log:error', msg='[Speech] Detection Error: ' + str(e))
                # finally:
                    # pub.sendMessage('led', identifiers='top5', color='off')

    def stop(self):
        self.listening = False
        pub.sendMessage('log', msg='[Speech] Stopping')
        
# allow script to be run directly
if __name__ == '__main__':
    import os
    from pubsub import pub
    import logging
    logging.basicConfig(filename=os.path.dirname(__file__) + '/app.log', level=logging.DEBUG, format='%(levelname)s: %(asctime)s %(message)s',
                                datefmt='%m/%d/%Y %I:%M:%S %p') 
    from logwrapper import LogWrapper
    log = LogWrapper(path=os.path.dirname(__file__))
    speech = SpeechInput()
    speech.start()