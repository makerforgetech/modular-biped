from googletrans import Translator as GoogleTranslator
'''
    This module is used to translate text from one language to another.
    Install with `pip install googletrans==3.1.0a0` to avoid `AttributeError: 'NoneType' object has no attribute 'group'`
    Set default languages in config/transalator.yml and reference in init call

'''


class Translator:
    def __init__(self, **kwargs):
        # init the Google API translator
        self.translator = GoogleTranslator()
        self.src = kwargs.get('src', 'en')
        self.dest = kwargs.get('dest', 'en')
        
    def request(self, text, src = None, dest = None):
        if src is None:
            src = self.src
        if dest is None:
            dest = self.dest
        if src == dest:
            return text
        translation = self.translator.translate(text, src=src, dest=dest)
        print(f"{translation.origin} ({translation.src}) --> {translation.text} ({translation.dest})")    
        return translation
        

if __name__ == '__main__':
    translator = Translator()
    print(translator.request("This is a test of the translation from English to Spanish"))