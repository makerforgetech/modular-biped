import logging, json
import os, datetime
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
        
        Examples (require module to extend BaseModule):
        self.log('My message to log') 
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
        self.log_level = kwargs.get('log_level', 'debug') # level of logs to output to file
        self.cli_level = kwargs.get('cli_level', 'debug') # level of logs to output to console
        print(f"[Creating log at {self.file}]")
        self.print = kwargs.get('print', False)
        
        logging.basicConfig(filename=self.file, 
                    level=LogWrapper.levels.index(self.log_level)*10, format='%(levelname)s: %(asctime)s %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S %p') 
        
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
        print(f"[Log file stored at {self.file}.previous]")

    def log(self, message):
        self.log('info', message)

    def log(self,  message, type='info'):
        # if message is a json object as a string
        if isinstance(message, str) and message.startswith('{'):
            message = json.loads(message)['message']
                
        if self.translator is not None:
            message = self.translator.request(message)

        logging.log(LogWrapper.levels.index(type)*10, message) # Filter on log level is handled by logging module
         
        if LogWrapper.levels.index(self.cli_level) <= LogWrapper.levels.index(type):
            print('log/' + type + ': ' + str(message))
    