from pubsub import pub
from time import sleep
import pyttsx3

import elevenlabs
import os


class TTSModule:
    
    def __init__(self, **kwargs):
        """
        TTS class
        :param kwargs: translator, service, voice_id
        :param translator: translator object
        :param service: pyttsx3 or elevenlabs
        :param voice_id: elevenlabs voice id
        
        Install: pip install pyttsx3 elevenlabs
        
        Requires API key environment variable ELEVENLABS_KEY or use pyttsx3
        
        Subscribes to 'tts' to speak message
        - Argument: msg (string) - message to speak
        
        Example:
        pub.sendMessage('tts', msg='Hello, World!')
        """
        self.translator = kwargs.get('translator', None)
        self.service = kwargs.get('service', 'pyttsx3')
        # print(self.service)
        self.voice_id = kwargs.get('voice_id', '')
        # print(self.voice_id)
        if self.service == 'elevenlabs':
            self.init_elevenlabs(self.voice_id)
        else:
            self.init_pyttsx3()
        # Set subscribers
        pub.subscribe(self.speak, 'tts')

    def speak(self, msg):
        # print('Attempting to speak with service: ' + self.service)
        if self.service == 'elevenlabs':
            self.speak_elevenlabs(msg)
        else:
            self.speak_pyttsx3(msg)
        
    def init_pyttsx3(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        #rate = engine.getProperty('rate')
        #engine.setProperty('rate', rate+100)
        #for i in voices:
        engine.setProperty('voice', voices[10].id)
        print('voice' + voices[10].id)
        self.engine = engine        

    def speak_pyttsx3(self, msg):
        pub.sendMessage('log', msg="[TTS] {}".format(msg))
        if self.translator is not None:
            msg = self.translator.request(msg)

        self.engine.say(f"{msg}. I have spoken.") # Apparently this is the only way to get pyttsx3 to output anything (by including actual text)
        # self.engine.say(msg) # This doesn't output anything
        self.engine.runAndWait()
    
    def init_elevenlabs(self, voice_id):
        self.ttsclient = elevenlabs.ElevenLabs(
            api_key=os.getenv('ELEVENLABS_KEY') or ''
        )
        self.voice_id = voice_id
        
    def speak_elevenlabs(self, msg):
        # This uses ElevenLabs, create an API key and export in your .bashrc file using `export ELEVENLABS_KEY=<KEY>` before use
        output = self.ttsclient.text_to_speech.convert(
            voice_id=self.voice_id,
            optimize_streaming_latency="0",
            output_format="mp3_22050_32",
            text=msg,
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.1,
                similarity_boost=0.3,
                style=0.2,
            ),
        )

        elevenlabs.play(output)
                
if __name__ == '__main__':
    # test with `myenv/bin/python3 modules/audio/ttsmodule.py`
    tts = TTSModule()
    tts.speak("this is a test") # broken currently, thinks espeak-ng is not installed
    
    tts2 = TTSModule(service='elevenlabs', voice_id='pMsXgVXv3BLzUgSXRplE')
    tts2.speak('Test')
    
    # import speechinput as speechinput
    # speech = speechinput.SpeechInput(device_name='pulse', start_on_boot=True)
        
