from elevenlabs import ElevenLabs, VoiceSettings, play
import os

# This uses ElevenLabs, create an API key and export in your .bashrc file using `export ELEVENLABS_KEY=<KEY>` before use

client = ElevenLabs(
    api_key=os.getenv('ELEVENLABS_KEY') or ''
)

output = client.text_to_speech.convert(
    voice_id="pMsXgVXv3BLzUgSXRplE",
    optimize_streaming_latency="0",
    output_format="mp3_22050_32",
    text="It sure does, Jackie… My mama always said: “In Carolina, the air's so thick you can wear it!”",
    voice_settings=VoiceSettings(
        stability=0.1,
        similarity_boost=0.3,
        style=0.2,
    ),
)

play(output)