from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import logging

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

class MyChatBot:
    
    def __init__(self, **kwargs):
        self.chatbot = ChatBot('Robot')
        # Create a new trainer for the chatbot
        self.trainer = ChatterBotCorpusTrainer(self.chatbot)

        # Train the chatbot based on the english corpus
        self.trainer.train("chatterbot.corpus.english")

        # Train based on english greetings corpus
        self.trainer.train("chatterbot.corpus.english.greetings")

        # Train based on the english conversations corpus
        self.trainer.train("chatterbot.corpus.english.conversations")

    def get_response(self, text):
        return self.chatbot.get_response(text)
