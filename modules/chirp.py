from chirpsdk import ChirpSDK
from pubsub import pub
# Mac:
# brew install portaudio libsndfile
# Raspbian:
# sudo apt-get install python3-dev python3-setuptools portaudio19-dev libffi-dev libsndfile1

# Then:
# pip3 install chirpsdk
# create ~/.chirprc with credentials from https://developers.chirp.io/applications


class Chirp:
    """
    Use chirp (https://chirp.io) to communicate over audio
    """
    def __init__(self, **kwargs):
        self.chirp = ChirpSDK()
        self.chirp.start(send=True, receive=True)

    def __del__(self):
        self.chirp.stop()

    def send(self, message):
        print(message)
        if message:
            pub.sendMessage('audio_on')
            payload = bytearray(message.encode('utf8'))
            # payload = str(message).encode('utf8')
            self.chirp.send(payload, blocking=True)
            pub.sendMessage('audio_off')
