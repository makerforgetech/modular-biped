from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from pubsub import pub

class MyChatBot:
    
    def __init__(self, **kwargs):
        self.chatbot = ChatBot('Robot')
        self.trainer = ChatterBotCorpusTrainer(self.chatbot)

        self.trainer.train("chatterbot.corpus.english")
        self.trainer.train("chatterbot.corpus.english.greetings")
        self.trainer.train("chatterbot.corpus.english.conversations")
        
        pub.subscribe(self.chat, 'speech')

    def chat(self, msg):
        response = self.chatbot.get_response(msg)
        pub.sendMessage('tts', msg=response.text)
