from time import sleep
import os
import re

from openai import OpenAI
from modules.base_module import BaseModule

class ChatGPT(BaseModule):
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
        self.publish('speech', text='Can you hear me?')
        """
        self.persona = kwargs.get('persona', 'You are a helpful assistant. You respond with short phrases where possible.')
        self.model = kwargs.get('model', 'gpt-4o-mini')
        self.client = OpenAI()
        
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('speech', self.completion)
        
    def completion(self, text):
        """
        Chat with GPT
        :param text: message to chat
        
        Publishes 'log' with response
        Publishes 'animate' with available animations listed in config yaml
        Publishes 'tts' with response
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": self.persona
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        output = completion.choices[0].message.content
        self.log(output)
        # if output includes 'animate:', split on colon and sendMessage 'animate' with action
        if 'animate:' in output:
            action = output.split(':')[1]
            self.publish('animate', action=action)
        else:
            self.publish('tts', msg=output)
        return output

                
if __name__ == '__main__':
    mychat = ChatGPT()
    mychat.completion('Can you hear me?')
