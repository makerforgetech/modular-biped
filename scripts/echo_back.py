import speech_recognition as sr
print(sr.__version__)


r = sr.Recognizer()

from elevenlabs import ElevenLabs, VoiceSettings, play
import os

# This uses ElevenLabs, create an API key and export in your .bashrc file using `export ELEVENLABS_KEY=<KEY>` before use

client = ElevenLabs(
    api_key=os.getenv('ELEVENLABS_KEY') or ''
)

# mic = sr.Microphone()
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))


mic = sr.Microphone(device_index=2, sample_rate=16000)
# mic.format=sr.Microphone.get_pyaudio().paInt8
# mic.format = mic.pyaudio_module.paInt32
# mic.SAMPLE_WIDTH = mic.pyaudio_module.get_sample_size(mic.format)  # size of each sample

print(mic.format)


with mic as source:
    print('adjusting')
    r.adjust_for_ambient_noise(source)
    print('adjusted. listening...')
    while True:
        audio = r.listen(source)
        try:
            # print('audio found')
            input = r.recognize_google(audio)
            print(input)
            output = client.text_to_speech.convert(
                voice_id="flq6f7yk4E4fJM5XTYuZ",
                optimize_streaming_latency="0",
                output_format="mp3_22050_32",
                text=input,
                voice_settings=VoiceSettings(
                    stability=0.1,
                    similarity_boost=0.3,
                    style=0.2,
                ),
            )

            play(output)
            quit()
        except sr.UnknownValueError as e:
            print('.', end = '', flush=True)
