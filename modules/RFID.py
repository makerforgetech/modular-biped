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
    
    def __init__(self, **kwargs):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RFID_PIN, GPIO.IN)
        self.active_duration = 0
        self.access_time = None
        pub.subscribe(self.revoke_check, 'loop:10')
        
    def wait_for_access(self):
        while True:
            time.sleep(10)
            pub.sendMessage('log', msg='[RFID] Waiting for access...')
            pub.sendMessage('tts', msg='Please authenticate your identity.')
            card_id = read_rfid()
            if authenticate_card(card_id):
                self.active_duration = get_active_duration()
                self.access_time = time.time()
                pub.sendMessage('log', msg='[RFID] Access granted for {} hours.'.format(self.active_duration))
                pub.sendMessage('tts', msg='Access granted for {} hours.'.format(self.active_duration))
                
    def revoke_check(self):
        if self.access_valid is False:
            pub.sendMessage('log', msg='[RFID] Access revoked.')
            pub.sendMessage('tts', msg='Access revoked.')
            self.access_time = None
            self.active_duration = 0
            quit()
    
    def access_valid(self):
        if (self.access_time is None):
            return False
        if (time.time() < self.access_time + self.active_duration * 60 * 60):
            return True
        return false
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
            while GPIO.input(Config.RFID_PIN) == 1:
                pass
            while GPIO.input(Config.RFID_PIN) == 0:
                pass
            for i in range(0, 26):
                rfid_value += str(GPIO.input(Config.RFID_PIN))
                time.sleep(0.01)
        return rfid_value


    def authenticate_card(card_id):
        # Get name from Config.RFID_CARDS
        name = Config.RFID_CARDS.get(card_id)
        if (name):
            pub.sendMessage('tts', msg='Welcome, ' + name + '.')
            return True
        return False
        
        
        # # Function to authenticate the RFID card
        # if card_id == AUTHORIZED_CARD_ID0:
        #     tts("Welcome, SentryCoder.Devloper")    #where SentryCoder.developer is meant define rfid card 0 for the owner of the robot change it for yourself
        #     return True
        # if card_id == AUTHORIZED_CARD_ID1:
        #     tts("Welcome,'name' ")
        #     return True
        # if card_id == AUTHORIZED_CARD_ID2:
        #     tts("Welcome,'name'")
        #     return True
        # if card_id == AUTHORIZED_CARD_ID3:
        #     tts("Welcome,'name'")
        #     return True
        # if card_id == AUTHORIZED_CARD_ID4:
        #     tts("Welcome,'name'")
        #     return True
        # if card_id == AUTHORIZED_CARD_ID5:
        #     tts("Welcome,'name'")
        #     return True    
        # else:
        #     tts("Unauthorized person")
        #     return False

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
                duration = extract_duration_from_text(text)
                if duration is not None:
                    return duration
                else:
                    pub.sendMessage('tts', msg="Invalid duration, please try again.")
            except (sr.UnknownValueError, sr.RequestError):
                pub.sendMessage('tts', msg="Voice not understood, please try again.")

        return duration


    def extract_duration_from_text(text):
        # Function to extract duration from the text
        match = re.search(r"(\d+)\s*(?:hour|hourly)", text)
        if match:
            duration = int(match.group(1))
            return duration
        else:
            return None

# Initialize the TTS engine
# engine = pyttsx3.init()
# engine.setProperty("rate", 170)  # speech rate
# voices = engine.getProperty('voices') 
# engine.setProperty('voice', voices[64].id)  # Turkish voice  @todo change this voice



# # Set the root password
# ROOT_PASSWORD = "rootroot"

# # Default duration in hours
# DEFAULT_DURATION = 0

# # RFID card IDs
# AUTHORIZED_CARD_ID0 = "1234567890"  # Replace with your authorized card ID
# AUTHORIZED_CARD_ID1 = "1234567890"  # Replace with your authorized card ID
# AUTHORIZED_CARD_ID2 = "1234567890"  # Replace with your authorized card ID
# AUTHORIZED_CARD_ID3 = "1234567890"  # Replace with your authorized card ID
# AUTHORIZED_CARD_ID4 = "1234567890"  # Replace with your authorized card ID
# AUTHORIZED_CARD_ID5 = "1234567890"  # Replace with your authorized card ID

# Configure RFID module
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(RFID_PIN, GPIO.IN)





# def open_jetson_session():
#     # Function to open Jetson Nano session
#     os.system("sudo -S <<< {} startx".format(ROOT_PASSWORD))


# def close_jetson_session():
#     # Function to close Jetson Nano session
#     os.system("sudo -S <<< {} pkill -u jetson".format(ROOT_PASSWORD))


# def main():
#     unauthorized_attempts = 0
#     wait_time = 0


# def main():
#     while True:
#         close_jetson_session()
#         time.sleep(10)
#         tts("Please authenticate your identity.")
#         card_id = read_rfid()
#         if authenticate_card(card_id):
#             active_duration = get_active_duration()
#             tts("SentryBOT activated for {} hours.".format(active_duration))
#             open_jetson_session()
#             time.sleep(active_duration * 60 * 60)
#             close_jetson_session()
#             tts("SentryBOT active duration completed. Wait for 10 seconds to authenticate your identity.")
#             time.sleep(10)



