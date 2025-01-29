import logging
from pubsub import pub
import os

class LogWrapper:
    levels = ['notset', 'debug', 'info', 'warning', 'error', 'critical']

    def __init__(self, **kwargs):
        """
        LogWrapper class
        :param kwargs: path, filename, translator
        
        Install: pip install pubsub
        
        Subscribes to 'log' to log messages
        - Argument: type (string) - log level
        - Argument: msg (string) - message to log
        
        Example:
        pub.sendMessage('log', type='info', msg='This is an info message')
        pub.sendMessage('log:debug', msg='This is a debug message')
        pub.sendMessage('log:info', msg='This is an info message')
        pub.sendMessage('log:error', msg='This is an error message')
        pub.sendMessage('log:critical', msg='This is a critical message')
        pub.sendMessage('log:warning', msg='This is a warning message')
        
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

        pub.subscribe(self.log, 'log', type='info')
        pub.subscribe(self.log, 'log:debug', type='debug')
        pub.subscribe(self.log, 'log:info', type='info')
        pub.subscribe(self.log, 'log:error', type='error')
        pub.subscribe(self.log, 'log:critical', type='critical')
        pub.subscribe(self.log, 'log:warning', type='warning')

    def __del__(self):
        if os.path.isfile(self.file):
            os.rename(self.file, self.file + '.previous')

    def log(self, type, msg):
        if self.translator is not None:
            msg = self.translator.request(msg)

        # Translate type string to log level (0 - 50)
        logging.log(LogWrapper.levels.index(type)*10, msg)
        
        if self.print:
            print('LogWrapper: ' + type + ' - ' + str(msg))
        