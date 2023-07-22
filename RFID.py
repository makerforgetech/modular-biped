import RPi.GPIO as GPIO
import time
import MFRC522

class Rfid:
    def __init__(self):
        # GPIO pin for RFID module
        self.RFID_PIN = 18

        # RFID card IDs
        self.AUTHORIZED_CARD_IDS = [
            "1234567890",  # Replace with your authorized card IDs
            "1234567890",
            "1234567890",
            "1234567890",
            "1234567890",
            "1234567890"
        ]

        # Configure RFID module
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RFID_PIN, GPIO.IN)

    def read_rfid(self):
        # Function to read RFID card ID from the RFID module
        rfid_value = ""
        while len(rfid_value) != 10:
            rfid_value = ""
            while GPIO.input(self.RFID_PIN) == 1:
                pass
            while GPIO.input(self.RFID_PIN) == 0:
                pass
            for i in range(0, 26):
                rfid_value += str(GPIO.input(self.RFID_PIN))
                time.sleep(0.01)
        return rfid_value

    def authenticate_card(self, card_id):
        # Function to authenticate the RFID card
        if card_id in self.AUTHORIZED_CARD_IDS:
            return True
        else:
            return False
