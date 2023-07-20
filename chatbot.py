from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import speech_recognition as sr
from gtts import gTTS
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

class MyChatBot:
    
    def __init__(self, **kwargs):
        self.chatbot = ChatBot('Robot')
        #chatbot için yeni bir eğitim oluşturun
        self.trainer = ChatterBotCorpusTrainer(self.chatbot)

        self.trainer.train("chatterbot.corpus.turkish")
        # Chatbot'u Türkçe bütüncesine"(corpusuna)"göre eğitin
        self.trainer.train("chatterbot.corpus.turkish.greetings")
        # Chatbot'u Türkçe Selamlama bütüncesine"(corpusuna)"göre eğitin
        self.trainer.train("chatterbot.corpus.turkish.conversations")
        # Chatbot'u Türkçe Konuşma bütüncesine"(corpusuna)"göre eğitin

        self.recognizer = sr.Recognizer()

    def get_audio_input(self):
        with sr.Microphone() as source:
            print("Dinliyorum...")
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio, language='tr-TR')
            print("Ses Algılandı:", text)
            return text
        except sr.UnknownValueError:
            print("Ses anlaşılamadı")
            return ""
        except sr.RequestError:
            print("Google Speech Recognition servisine şu anda ulaşılamıyor lütfen daha sonra tekrar deneyiniz")
            return ""

    def speak(self, text):
        tts = gTTS(text=text, lang='tr')
        tts.save("output.mp3")
        os.system("mpg321 output.mp3")
        print("ChatBot:", text)

    def chat(self):
        while True:
            user_input = self.get_audio_input()

            if user_input.lower() == "Konuşma motorunu kapat":
                self.speak("Konuşma motoru kapatılıyor!")
                break

            response = self.chatbot.get_response(user_input)
            self.speak(response.text)

if __name__ == "__main__":
    chatbot = MyChatBot()
    chatbot.chat()
