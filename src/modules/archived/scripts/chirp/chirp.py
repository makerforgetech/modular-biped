
# Mac:
# brew install portaudio libsndfile
# Raspbian:
# sudo apt-get install python3-dev python3-setuptools portaudio19-dev libffi-dev libsndfile1

# Then:
# pip3 install chirpsdk

from chirpsdk import ChirpSDK, CallbackSet

chirp = ChirpSDK()
chirp.start(send=True, receive=True)


# Send data
identifier = 'hello'
payload = identifier.encode('utf8')
chirp.send(payload, blocking=True)


# Stop
chirp.stop()