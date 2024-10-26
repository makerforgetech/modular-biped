from pubsub import pub
from time import sleep
import os
import re

from openai import OpenAI

class ChatGPT:
    def __init__(self, **kwargs):
        """
        ChatGPT class
        :param kwargs: persona, model
        :kwarg persona: persona to use for the chat
        :kwarg model: model to use for the chat
        
        Requires API key environment variable OPENAI_API_KEY
        Read here for config steps : https://platform.openai.com/docs/quickstart
        
        Install: pip install openai
        
        Subscribes to 'speech' to chat
        - Argument: text (string) - message to chat
        
        Example:
        pub.sendMessage('speech', text='Can you hear me?')
        """
        self.persona = kwargs.get('persona', 'You are a helpful assistant. You respond with short phrases where possible.')
        self.model = kwargs.get('model', 'gpt-4o-mini')
        self.client = OpenAI()
        pub.subscribe(self.completion, 'speech')
        
    def completion(self, text):
        """
        Chat with GPT
        :param text: message to chat
        
        Publishes 'log' with response
        Publishes 'animate' with head nod or shake
        Publishes 'tts' with response
        """
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. You respond with short phrases or yes / no as a strong preference."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        pub.sendMessage('log', msg='[ChatGPT] ' + completion.choices[0].message.content)
        # print(completion.choices[0].message.content)
        output = re.sub(r'[^\w\s]','',completion.choices[0].message.content).lower()
        # print(output)
        if output == 'yes':
            # Nod head if answer is just 'yes'
            pub.sendMessage('animate', action='head_nod')
        elif output == 'no':
            # Shake head if answer is just 'no'
            pub.sendMessage('animate', action='head_shake')
        pub.sendMessage('tts', msg=completion.choices[0].message.content)
        return completion.choices[0].message.content

                
if __name__ == '__main__':
    mychat = ChatGPT()
    mychat.completion('Can you hear me?')
