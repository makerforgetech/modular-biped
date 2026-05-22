import os
import subprocess
import speech_recognition as sr
from time import sleep
from threading import Thread
from modules.base_module import BaseModule

class SpeechInput(BaseModule):
    """
    Use speech_recognition to detect and interpret audio
    """
    def __init__(self, **kwargs):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 2

        self.device_name = kwargs.get('device_name', 'pulse')
        self.device = self.get_device_index(self.device_name)
        self.sample_rate = kwargs.get('sample_rate', 16000)

        self.mic = sr.Microphone(device_index=self.device, sample_rate=self.sample_rate)
        self.listening = False
        
        self.start_on_boot = kwargs.get('start_on_boot', False)
        self.wake_word = kwargs.get('wake_word', None)
        
        self.capture_detections = kwargs.get('capture_detections', False)
        self.repeat_captures = kwargs.get('repeat_captures', False)
        print('SpeechInput initialized with device ' + str(self.device) + ' and sample rate ' + str(self.sample_rate) + '. Start on boot: ' + str(self.start_on_boot))
    
    def setup_messaging(self):
        self.subscribe('speech:listen', self.start)
        self.subscribe('rest', self.stop)
        self.subscribe('sleep', self.stop)
        self.subscribe('exit', self.stop)
        self.log('Mapping mic to index ' + str(self.device))
        if self.start_on_boot:
            self.start()

    def __del__(self):
        self.stop()

    def start(self):
        self.listening = True
        self.log('Starting speech detection')
        Thread(target=self.detect, args=()).start()
        return self

    def get_device_index(self, device_name):
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
            if name == device_name:
                print('Mapping mic to index ' + str(index))
                return index
            # throw exception if device name is not found
        raise Exception('Device name ' + device_name + ' not found. Available devices: ' + str(sr.Microphone.list_microphone_names()))

    def detect(self):
        """
        Not background
        :return:
        """
        self.log('Initialising Detection')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            # self.recognizer.energy_threshold = 300  # Adjust based on your environment
            self.log('Detecting...')
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                    val = self.recognizer.recognize_google(audio)
                    
                    if self.wake_word and self.wake_word not in val.lower():
                        self.log('Wake word "' + self.wake_word + '" not detected in "' + val + '". Ignoring.')
                        continue
                    
                    if self.capture_detections:
                        #save audio with filename as val substituting any non alphanumeric characters with underscores
                        filename = str(val).replace(' ', '_').replace('[^a-zA-Z0-9]', '_')
                        with open("speech_" + filename +  ".wav", "wb") as f:
                            f.write(audio.get_wav_data())
                        if self.repeat_captures:
                            # play back file via speakers
                            self.log('Playing back audio')
                            subprocess.call(['aplay', '-D', 'plughw:cm5i2saudio,1', "speech_" + filename +  ".wav"])
                    
                    self.log('I heard: ' + str(val))
                    self.publish('speech', text=val.lower())
                    self.publish('tts', msg='I heard ' + val.lower())
                except sr.WaitTimeoutError as e:
                    self.publish('log/error', message='[Speech] Timeout Error: ' + str(e))
                except sr.UnknownValueError as e:
                    pass
                    # self.publish('log/error', msg='[Speech] Detection Error: ' + str(e))
                # finally:
                    # self.publish('led', identifiers='top5', color='off')

    def stop(self):
        self.listening = False
        self.log('Stopping')
        
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