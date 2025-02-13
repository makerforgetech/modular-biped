# modules/controller/audio_llm.py

import requests
from pubsub import pub

class AudioLLM:
    def __init__(self, **kwargs):
        """
        AudioLLM module processes voice input, sends it to the LLM service,
        and publishes the response for TTS.
        
        Configuration kwargs:
          - ollama_url: URL of the LLM (Ollama) API (e.g., "http://laptop_ip:port/api")
          - translator: Optional translation object/function with a translate(text, source, target) method.
          - source_lang: Source language for translation (default: 'auto')
          - target_lang: Target language for translation (default: 'en')
        """
        self.ollama_url = kwargs.get('ollama_url', 'http://localhost:5000/api')
        self.translator = kwargs.get('translator', None)
        self.source_lang = kwargs.get('source_lang', 'auto')
        self.target_lang = kwargs.get('target_lang', 'en')
        
        # Subscribe to voice input messages.
        pub.subscribe(self.handle_voice_input, 'speech_input')
        pub.subscribe(self.handle_llm_response, 'llm_response')
        
        print(f"[AudioLLM] Initialized with Ollama URL: {self.ollama_url}")

    def handle_voice_input(self, text):
        """Processes voice input and sends it to the LLM service."""
        print(f"[AudioLLM] Received voice input: {text}")
        
        # Optionally translate the input text.
        if self.translator is not None:
            try:
                text = self.translator.translate(text, self.source_lang, self.target_lang)
                print(f"[AudioLLM] Translated text: {text}")
            except Exception as e:
                print(f"[AudioLLM] Translation error: {e}")
        
        response_text = self.send_to_llm(text)
        if response_text:
            # Publish the response for TTS.
            pub.sendMessage('tts', text=response_text)
        else:
            print("[AudioLLM] No response from LLM API.")

    def send_to_llm(self, text):
        """Sends the text to the LLM API and returns the response."""
        payload = {'input': text}
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                output = data.get('output', '')
                print(f"[AudioLLM] LLM API response: {output}")
                return output
            else:
                print(f"[AudioLLM] LLM API status: {response.status_code}")
                return None
        except Exception as e:
            print(f"[AudioLLM] Error contacting LLM API: {e}")
            return None

    def handle_llm_response(self, response_text):
        """
        In case the LLM response is published from elsewhere,
        republish it for the TTS module.
        """
        print(f"[AudioLLM] Received LLM response via pubsub: {response_text}")
        pub.sendMessage('tts', text=response_text)
