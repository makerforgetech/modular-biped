from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class MyChatBot:
    
    def __init__(self, tts, speech_input, **kwargs):
        self.chatbot = ChatBot('Robot')
        self.trainer = ChatterBotCorpusTrainer(self.chatbot)

        self.trainer.train("chatterbot.corpus.english")
        self.trainer.train("chatterbot.corpus.english.greetings")
        self.trainer.train("chatterbot.corpus.english.conversations")

        self.tts = tts
        self.speech_input = speech_input

    def speak(self, text):
        self.tts.speak(text)

    def get_audio_input(self):
        return self.speech_input.get_audio_input()

    def chat(self):
        while True:
            user_input = self.get_audio_input()

            if user_input.lower() == "turn off speech engine":
                self.speak("turning off speech engine!")
                break

            response = self.chatbot.get_response(user_input)
            self.speak(response.text)
