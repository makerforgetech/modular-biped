# python -m pip install --upgrade pip setuptools wheel
# pip install --upgrade pocketsphinx
# brew install swig / apt-get install swig

import speech_recognition as sr
print(sr.__version__)


r = sr.Recognizer()



harvard = sr.AudioFile('speech.wav')
with harvard as source:
    audio = r.record(source)

r.recognize_sphinx(audio)