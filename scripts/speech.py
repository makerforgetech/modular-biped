import speech_recognition as sr
print(sr.__version__)


r = sr.Recognizer()
#r.adjust_for_ambient_noise(source, duration=0.5)

# print('loading audio')
# harvard = sr.AudioFile('test.wav')
# with harvard as source:
#     audio = r.record(source)
#
# print('loaded')
# print(r.recognize_sphinx(audio))
# print('done')

mic = sr.Microphone()
print(sr.Microphone.list_microphone_names())
#mic = sr.Microphone(device_index=3)

with mic as source:
    r.adjust_for_ambient_noise(source)
    audio = r.listen(source)

print(r.recognize_sphinx(audio))