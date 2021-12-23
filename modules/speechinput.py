import speech_recognition as sr
from pubsub import pub
from time import sleep

class SpeechInput:
    """
    Use speech_recognition to detect and interpret audio
    """
    def __init__(self, **kwargs):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone(device_index=1) # @todo work with i2s, overriden to USB mic for now
        self.listening = False
        self.background = True
        self.stop_listening = None

        # with self.mic as source:
        #     self.recognizer.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening
        #     print('adjusted for ambient noise')
        #
        # self.stop_listening = self.recognizer.listen_in_background(self.mic, SpeechInput.background_callback)
        # print('listening in background')

        pub.subscribe(self.enable, 'wake')
        pub.subscribe(self.disable, 'rest')
        pub.subscribe(self.disable, 'sleep')
        # pub.subscribe(self.detect, 'loop:1')

    def __del__(self):
        self.stop_listening(wait_for_stop=False)

    def enable(self):
        pub.sendMessage('log', msg='[Speech] Listening')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(
                source)  # we only need to calibrate once, before we start listening
            print('adjusted for ambient noise')

        self.stop_listening = self.recognizer.listen_in_background(self.mic, SpeechInput.background_callback)
        print('listening in background')
        # self.listening = True

    def disable(self):
        pub.sendMessage('log', msg='[Speech] Not Listening')
        if self.stop_listening:
            print('not listening anymore')
            self.stop_listening(wait_for_stop=False)
        # self.listening = False

    def detect(self):
        if not self.listening:
            return None
        pub.sendMessage('log', msg='[Speech] Initialising Detection')
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            pub.sendMessage('log', msg='[Speech] Detecting...')
            audio = self.recognizer.listen(source)
        pub.sendMessage('log', msg='[Speech] End Detection')
        try:
            val = self.recognizer.recognize_google(audio)
            pub.sendMessage('log', msg='[Speech] I heard: ' + str(val))
            self.disable()
            return val
        except sr.UnknownValueError as e:
            pub.sendMessage('log:error', msg='[Speech] Detection Error: ' + str(e))
            self.disable()
            return None

    def detect_from_file(self, file):
        f = sr.AudioFile(file)
        with f as source:
            audio = self.recognizer.record(source)
        return self.recognizer.recognize_sphinx(audio)

    @staticmethod
    def background_callback(recognizer, audio):
        # @todo this is very inconsistent - needs a 10 second timeout in main loop to work
        pub.sendMessage('led:eye', color='white')
        # received audio data, now we'll recognize it using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            text = recognizer.recognize_google(audio)
            pub.sendMessage('log', msg='[Speech] I heard: ' + text)
            pub.sendMessage('speech', msg=text)
            print("Google Speech Recognition thinks you said " + text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

        pub.sendMessage('led:eye', color='red')
