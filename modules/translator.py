from googletrans import Translator as GoogleTranslator
'''
    This module is used to translate text from one language to another.
    Install with `pip install googletrans==3.1.0a0` to avoid `AttributeError: 'NoneType' object has no attribute 'group'`
    Set default languages in config/transalator.yml and reference in init call

'''


class Translator:
    def __init__(self, **kwargs):
        self.src = kwargs.get('src', 'en')
        self.dest = kwargs.get('dest', 'en')
        self.translator = None

    def request(self, text, src = None, dest = None):
        if src is None:
            src = self.src
        if dest is None:
            dest = self.dest
        if src == dest:
            return text
        try:
            if self.translator is None:
                self.translator = GoogleTranslator()
            translation = self.translator.translate(text, src=src, dest=dest)
        except Exception as e:
            print(e)
            return 'FAILED TRANSLATION: ' + text
        # print(f"{translation.origin} ({translation.src}) --> {translation.text} ({translation.dest})")    
        return translation.text
        

if __name__ == '__main__':
    translator = Translator()
    print(translator.request("This is a test of the translation from English to Spanish"))