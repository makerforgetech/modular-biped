import os
import pyttsx3
import RPi.GPIO as GPIO
import speech_recognition as sr
import re
import time

# Initialize the TTS engine
engine = pyttsx3.init()
engine.setProperty("rate", 170)  # speech rate
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[64].id)  # Turkish voice

# GPIO pin for RFID module
RFID_PIN = 18

# Set the root password
ROOT_PASSWORD = "rootroot"

# Default duration in hours
DEFAULT_DURATION = 0

# RFID card IDs
AUTHORIZED_CARD_ID = "1234567890"  # Replace with your authorized card ID

# Configure RFID module
GPIO.setmode(GPIO.BCM)
GPIO.setup(RFID_PIN, GPIO.IN)


def read_rfid():
    # Function to read RFID card ID from the RFID module
    rfid_value = ""
    while len(rfid_value) != 10:
        rfid_value = ""
        while GPIO.input(RFID_PIN) == 1:
            pass
        while GPIO.input(RFID_PIN) == 0:
            pass
        for i in range(0, 26):
            rfid_value += str(GPIO.input(RFID_PIN))
            time.sleep(0.01)
    return rfid_value


def tts(text):
    # Function to convert text to speech
    engine.say(text)
    engine.runAndWait()


def authenticate_card(card_id):
    # Function to authenticate the RFID card
    if card_id == AUTHORIZED_CARD_ID:
        tts("Welcome, SentryCoder.Devloper")
        return True
    else:
        tts("Unauthorized person")
        return False


def authenticate_owner():
    # Function to perform owner's identity authentication
    tts("Authenticate your voice.")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
    text = r.recognize_google(audio, language="tr-TR")
    if text.lower() == "identity verification":
        tts("Say the login identity to verify your identity.")
        with sr.Microphone() as source:
            audio = r.listen(source)
        text = r.recognize_google(audio, language="tr-TR")
        if text.lower() == "devloper 366":
            tts("SentryBOT unlocked.")
            return True
        else:
            tts("Invalid login identity. Unauthorized person detected.")
            return False
    else:
        tts("Identity verification failed. Please try again.")
        return False


def get_active_duration():
    # Function to get the desired active duration from the user's voice input
    tts("How long do you want SentryBOT to stay active?")
    time.sleep(0.5)
    tts('For example, say "I want SentryBOT to stay active for 1 hour."')
    r = sr.Recognizer()
    while True:
        try:
            with sr.Microphone() as source:
                audio = r.listen(source)

            text = r.recognize_google(audio, language="tr-TR")
            duration = extract_duration_from_text(text)
            if duration is not None:
                break
            else:
                tts("Invalid duration, please try again.")
        except (sr.UnknownValueError, sr.RequestError):
            tts("Voice not understood, please try again.")

    return duration


def extract_duration_from_text(text):
    # Function to extract duration from the text
    match = re.search(r"(\d+)\s*(?:hour|hourly)", text)
    if match:
        duration = int(match.group(1))
        return duration
    else:
        return None


def open_jetson_session():
    # Function to open Jetson Nano session
    os.system("sudo -S <<< {} startx".format(ROOT_PASSWORD))


def close_jetson_session():
    # Function to close Jetson Nano session
    os.system("sudo -S <<< {} pkill -u jetson".format(ROOT_PASSWORD))


def main():
    unauthorized_attempts = 0
    wait_time = 0

    while True:
        if unauthorized_attempts > 5:
            if not authenticate_owner():
                tts("Unauthorized person identified. Robot locked.")
                wait_time += 5
                time.sleep(wait_time * 60)
                continue

        if unauthorized_attempts % 5 == 0 and unauthorized_attempts != 0:
            wait_time += 5
            tts(f"You have entered unauthorized access {unauthorized_attempts} times. Access will be granted in {wait_time} minutes.")
            time.sleep(wait_time * 60)

        tts("Please authenticate your identity.")
        card_id = read_rfid()
        if not authenticate_card(card_id):
            unauthorized_attempts += 1
            tts("Unauthorized person identified.")
            continue

        unauthorized_attempts = 0  # Reset unauthorized attempts counter
        wait_time = 0  # Reset wait time counter

        active_duration = get_active_duration()
        tts("SentryBOT activated for {} hours.".format(active_duration))
        open_jetson_session()
        time.sleep(active_duration * 60 * 60)
        close_jetson_session()
        tts("SentryBOT active duration completed. Wait for 10 seconds to authenticate your identity.")
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
