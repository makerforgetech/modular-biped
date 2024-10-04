import json
import random
from transformers import pipeline
from itertools import combinations
from pubsub import pub

class EmotionAnalysisModule:
    def __init__(self):
        # Load color sets from JSON file
        with open('emotions.json') as f:
            self.color_sets = json.load(f)

        # Emotion analyzer
        self.emotion_analyzer = pipeline('text-classification', model='joeddav/distilbert-base-uncased-go-emotions-student')

        # Emotion to keyword mapping
        self.emotion_to_keyword = {
            'admiration': 'admiration',
            'neutral': 'neutral',
            'surprise': 'surprise',
            'sadness': 'sadness',
            'remorse': 'remorse',
            'relief': 'relief',
            'realization': 'realization',
            'pride': 'pride',
            'optimism': 'optimism',
            'nervousness': 'nervousness',
            'love': 'love',
            'joy': 'joy',
            'grief': 'grief',
            'gratitude': 'gratitude',
            'fear': 'fear',
            'excitement': 'excitement',
            'embarrassment': 'embarrassment',
            'disgust': 'disgust',
            'disapproval': 'disapproval',
            'disappointment': 'disappointment',
            'desire': 'desire',
            'curiosity': 'curiosity',
            'confusion': 'confusion',
            'caring': 'caring',
            'approval': 'approval',
            'annoyance': 'annoyance',
            'anger': 'anger',
            'amusement': 'amusement',
        }

        pub.subscribe(self.analyze_text, 'speech')

    def get_different_colors(self, color_dict, num_colors):
        colors = list(color_dict.values())
        if len(colors) <= num_colors:
            return colors
        selected = []
        for _ in range(num_colors):
            color = random.choice(colors)
            selected.append(color)
            colors = [c for c in colors if abs(int(color.split(',')[0][1:]) - int(c.split(',')[0][1:])) > 50]
        return selected

    def analyze_text(self, text):
        emotion_keywords = [self.emotion_to_keyword.get(e['label'].lower(), '') for e in self.emotion_analyzer(text)]
        color_dicts = {e: self.color_sets.get(e, {}) for e in emotion_keywords if e}
        colors_by_emotion = {e: self.get_different_colors(color_dicts[e], 7) for e in color_dicts}

        if len(emotion_keywords) == 1:
            selected_colors = colors_by_emotion[emotion_keywords[0]]
        elif len(emotion_keywords) == 2:
            dominant, less_dominant = emotion_keywords
            selected_colors = (
                self.get_different_colors(color_dicts[dominant], 4) +
                self.get_different_colors(color_dicts[less_dominant], 3)
            )
        elif len(emotion_keywords) == 3:
            dominant, medium, least_dominant = emotion_keywords
            selected_colors = (
                self.get_different_colors(color_dicts[dominant], 4) +
                self.get_different_colors(color_dicts[medium], 2) +
                self.get_different_colors(color_dicts[least_dominant], 1)
            )
        elif len(emotion_keywords) == 4:
            dominant, second_dominant, third_dominant, least_dominant = emotion_keywords
            selected_colors = (
                self.get_different_colors(color_dicts[dominant], 3) +
                self.get_different_colors(color_dicts[second_dominant], 3) +
                self.get_different_colors(color_dicts[third_dominant], 1)
            )
        else:
            sorted_emotions = sorted(emotion_keywords, key=lambda e: len(color_dicts[e]), reverse=True)
            selected_colors = []
            color_counts = [3, 3, 2, 1] + [1] * (len(sorted_emotions) - 4)
            for e, count in zip(sorted_emotions, color_counts):
                selected_colors.extend(self.get_different_colors(color_dicts[e], count))

        # Convert color strings to RGB tuples
        rgb_colors = [tuple(map(int, c[1:-1].split(','))) for c in selected_colors]
        
        # Send colors to NeoPixel LEDs
        for i, color in enumerate(rgb_colors):
            pub.sendMessage('led', identifiers=i, color=color)
