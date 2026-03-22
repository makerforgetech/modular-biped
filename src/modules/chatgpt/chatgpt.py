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
        
        Subscribes to 'speech' to chat
        - Argument: text (string) - message to chat
        
        Example:
        self.publish('speech', text='Can you hear me?')
        """
        self.persona = kwargs.get('persona', 'You are a helpful assistant. You respond with short phrases where possible.')
        self.model = kwargs.get('model', 'gpt-4o-mini')
        # Check for OPENAI_API_KEY and raise error if not found
        if 'OPENAI_API_KEY' not in os.environ:
            raise RuntimeError("ChatGPT: OPENAI_API_KEY environment variable not found. Please set it to your OpenAI API key.")
        self.client = OpenAI()
        
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('speech', self.completion)
        self.subscribe('ai/input', self.text_completion)
        
    def text_completion(self, text, persona=None):
        """
        Get a text completion from the model and publish it to 'ai/response'.
        :param text: message to chat
        
        Publishes 'ai/response' with response
        """
        try:
            if persona is None:
                persona = self.persona
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": persona
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            )
            output = completion.choices[0].message.content
            self.publish('ai/response', response=output)
            return output
        except Exception as e:
            error_msg = f"[ChatGPT] Error: {e}"
            self.log(error_msg, type='error')
            self.publish('ai/response', response=error_msg)
            return None
        
    def completion(self, text):
        """
        Chat with GPT
        :param text: message to chat
        
        Publishes:
        - 'tts' with response (default)
        - 'animate' with action if output includes 'animate/'
        - 'gpio/<target>' with state if output includes 'gpio/'
        Also logs the response.
        """
        try:
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
            if 'animate/' in output:
                action = output.split('/')[1]
                self.publish('animate', action=action)
            if 'gpio/' in output:
                # If output includes 'gpio/', split on colon and sendMessage 'gpio' with action
                t = output.split('/')[1]
                state = output.split('/')[2] == 'on'
                self.publish('gpio/' + t , state=state)
            else:
                self.publish('tts', msg=output)
            return output
        except Exception as e:
            error_msg = f"[ChatGPT] Error: {e}"
            self.log(error_msg, type='error')
            self.publish('tts', msg=error_msg)
            self.publish('ai/response', response=error_msg)
            return None

                
if __name__ == '__main__':
    mychat = ChatGPT()
    mychat.completion('Can you hear me?')
