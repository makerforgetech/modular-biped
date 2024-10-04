from pubsub import pub
from time import sleep
import os

from openai import OpenAI

class OpenAiChat:
    def __init__(self, **kwargs):
        self.persona = kwargs.get('persona', 'You are a helpful assistant. You respond with short phrases where possible.')
        self.model = kwargs.get('model', 'gpt-4o-mini')
        self.client = OpenAI()
        
        pub.subscribe(self.completion, 'speech')
        
    def completion(self, input):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You respond with short phrases where possible."},
                {
                    "role": "user",
                    "content": input
                }
            ]
        )

        print(completion.choices[0].message)
        pub.sendMessage('tts', completion.choices[0].message.content)
        return completion.choices[0].message.content

                
if __name__ == '__main__':
    mychat = Openaichat()
    mychat.completion('This is a test')
