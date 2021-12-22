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

with sr.AudioFile('file_stereo_i2s.wav') as source:
    audio = r.record(source)
print(r.recognize_google(audio))

mic = sr.Microphone()
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
# mic = sr.Microphone(device_index=0, sample_rate=48000)
# mic.format=sr.Microphone.get_pyaudio().paInt32


with mic as source:
    print('adjusting')
    r.adjust_for_ambient_noise(source)
    print('adjusted. listening...')
    audio = r.listen(source)
    print('audio found')

print(r.recognize_google(audio))
