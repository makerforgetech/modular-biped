import logging, json
import os
from modules.base_module import BaseModule

class LogWrapper(BaseModule):
    levels = ['notset', 'debug', 'info', 'warning', 'error', 'critical']

    def __init__(self, **kwargs):
        """
        LogWrapper class
        :param kwargs: path, filename, translator
        
        Install: pip install pubsub
        
        Subscribes to 'log' to log messages
        - Argument: type (string) - log level
        - Argument: message (string) - message to log
        
        Example:
        self.publish('log', 'My message to log')
        self.publish('log', type='info', message='This is an info message')
        self.publish('log/debug', 'This is a debug message')
        self.publish('log/info', 'This is an info message')
        self.publish('log/error', 'This is an error message')
        self.publish('log/critical', 'This is a critical message')
        self.publish('log/warning', 'This is a warning message')
        
        """
        self.path = kwargs.get('path',  os.path.dirname(os.path.dirname(__file__)))
        self.filename = kwargs.get('filename', kwargs.get('filename','app.log'))
        self.file = self.path + '/' + self.filename
        print(f"Creating log at {self.file}")
        self.print = kwargs.get('print', False)
        
        logging.basicConfig(filename=self.file, 
                    level=logging.INFO, format='%(levelname)s: %(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p') 
        
        self.translator = kwargs.get('translator', None)

    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('log', self.log)
        self.subscribe('log/debug', self.log, type='debug')
        self.subscribe('log/info', self.log, type='info')
        self.subscribe('log/error', self.log, type='error')
        self.subscribe('log/critical', self.log, type='critical')
        self.subscribe('log/warning', self.log, type='warning')

    def __del__(self):
        if os.path.isfile(self.file):
            os.rename(self.file, self.file + '.previous')

    def log(self, message):
        self.log('info', message)

    def log(self,  message, type='info'):
        # if message is a json object as a string
        if isinstance(message, str) and message.startswith('{'):
            message = json.loads(message)['message']
                
        if self.translator is not None:
            message = self.translator.request(message)

        # Translate type string to log level (0 - 50)
        logging.log(LogWrapper.levels.index(type)*10, message, exc_info=True)       
         
        if self.print:
            print('LogWrapper: ' + type + ' - ' + str(message))
        