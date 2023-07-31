import os
import pyttsx3
import RPi.GPIO as GPIO3
import MFRC522
import speech_recognition as sr
import re
import time
from pubsub import pub
from modules import Config

class RFID:
    
    def __init__(self, pin, cards **kwargs):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)
        self.pin = pin
        self.cards = cards
        self.active_duration = 0
        self.access_time = None
        pub.subscribe(self.revoke_check, 'loop:10')
        
    def wait_for_access(self):
        while True:
            time.sleep(10)
            pub.sendMessage('log', msg='[RFID] Waiting for access...')
            pub.sendMessage('tts', msg='Please authenticate your identity.')
            card_id = self.read_rfid()
            if self.authenticate_card(card_id):
                self.active_duration = RFID.get_active_duration()
                self.access_time = time.time()
                pub.sendMessage('log', msg='[RFID] Access granted for {} hours.'.format(self.active_duration))
                pub.sendMessage('tts', msg='Access granted for {} hours.'.format(self.active_duration))
                return
                
    def revoke_check(self):
        if not self.access_valid:
            pub.sendMessage('log', msg='[RFID] Access revoked.')
            pub.sendMessage('tts', msg='Access revoked.')
            self.access_time = None
            self.active_duration = 0
            quit() # not sure if this will work
    
    def access_valid(self):
        if (self.access_time is None):
            return False
        if (time.time() < self.access_time + self.active_duration * 60 * 60):
            return True
        return False
        # This can be changed to fire an exit event `quit()`
        #open_jetson_session()
        #time.sleep(active_duration * 60 * 60)
        #close_jetson_session()
        #tts("SentryBOT active duration completed. Wait for 10 seconds to authenticate your identity.")
        #time.sleep(10)
        pass

    def read_rfid():
        # Function to read RFID card ID from the RFID module
        rfid_value = ""
        while len(rfid_value) != 10:
            rfid_value = ""
            while GPIO.input(self.pin) == 1:
                pass
            while GPIO.input(self.pin) == 0:
                pass
            for i in range(0, 26):
                rfid_value += str(GPIO.input(self.pin))
                time.sleep(0.01)
        return rfid_value


    def authenticate_card(self, card_id):
        # Get name from cards
        name = self.cards.get(card_id)
        if (name):
            pub.sendMessage('tts', msg='Welcome, ' + name + '.')
            return True
        return False

    def get_active_duration():
        # Function to get the desired active duration from the user's voice input
        pub.sendMessage('tts', msg='How long do you want SentryBOT to stay active?')
        time.sleep(0.5)
        pub.sendMessage('tts', msg='For example, say "I want SentryBOT to stay active for 1 hour."')
        r = sr.Recognizer()
        while True:
            try:
                with sr.Microphone() as source:
                    audio = r.listen(source)
                text = r.recognize_google(audio, language="tr-TR") # @todo change this language to use config file
                duration = RFID.extract_duration_from_text(text)
                if duration is not None:
                    return duration
                else:
                    pub.sendMessage('tts', msg="Invalid duration, please try again.")
            except (sr.UnknownValueError, sr.RequestError):
                pub.sendMessage('tts', msg="Voice not understood, please try again.")

    def extract_duration_from_text(text):
        # Function to extract duration from the text
        match = re.search(r"(\d+)\s*(?:hour|hourly)", text)
        if match:
            duration = int(match.group(1))
            return duration
        else:
            return None
