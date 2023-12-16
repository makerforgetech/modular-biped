from pubsub import pub
from time import sleep, localtime
from modules.config import Config
from random import randrange

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class Sentiment:

    def __init__(self, state):
        
        self.state = state  # the personality instance
        pub.subscribe(self.speech, 'speech')
        # Do this the first time
        nltk.download('vader_lexicon')
        # initialize NLTK sentiment analyzer
        self.analyzer = SentimentIntensityAnalyzer()

    def speech(self, msg):
        if self.state.is_resting():
            return
        score = self.get_sentiment(msg)
        pub.sendMessage('sentiment', score=score)
        
    def get_sentiment(self, text):
        scores = self.analyzer.polarity_scores(text)
        pub.sendMessage('log', msg='[Sentiment] ' + str(scores))
        return scores['compound']
