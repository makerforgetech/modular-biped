from pubsub import pub
from time import sleep
import os
import re

from openai import OpenAI

class OpenAiChat:
    def __init__(self, **kwargs):
        self.persona = kwargs.get('persona', 'You are a helpful assistant. You respond with short phrases where possible.')
        self.model = kwargs.get('model', 'gpt-4o-mini')
        self.client = OpenAI()
        self.tts_threshold = kwargs.get('tts_threshold', 15)
        
        pub.subscribe(self.completion, 'speech')
        
    def completion(self, input):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. You respond with short phrases or yes / no as a strong preference."
                },
                {
                    "role": "user",
                    "content": input
                }
            ]
        )

        pub.sendMessage('log', msg='[OpenAIChat] ' + completion.choices[0].message.content)
        print(completion.choices[0].message.content)
        output = re.sub(r'[^\w\s]','',completion.choices[0].message.content).lower()
        print(output)
        if output == 'yes':
            # Nod head if answer is just 'yes'
            pub.sendMessage('animate', action='head_nod')
        elif output == 'no':
            # Shake head if answer is just 'no'
            pub.sendMessage('animate', action='head_shake')
        elif len(output) > self.tts_threshold:
            # Send to TTS engine if output is longer than threshold
            pub.sendMessage('tts', msg=completion.choices[0].message.content)
        else: 
            # Send to brailespeak module (if output is shorter than threshold)
            pub.sendMessage('speak', msg=completion.choices[0].message.content)
        return completion.choices[0].message.content

                
if __name__ == '__main__':
    mychat = OpenAiChat()
    mychat.completion('Can you hear me?')
