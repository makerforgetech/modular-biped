import logging
from pubsub import pub
import os
# from viam.logging import getLogger
# LOGGER = getLogger(__name__)
# LOGGER.debug('INIT MAKERFORGE LOGGER')

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
        self.path = kwargs.get('path', '/')
        self.filename = kwargs.get('filename', 'app.log')
        self.file = self.path + '/' + self.filename
        
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
        #msg = '[LOGGING] ' + msg
        # Translate type string to log level (0 - 50)
        logging.log(LogWrapper.levels.index(type)*10, msg)
        # if type == 'error' or type == 'warning':
        if self.translator is not None:
            msg = self.translator.request(msg)
        #print('LogWrapper: ' + type + ' - ' + str(msg))
        # self.log_viam(type, msg)
        
    # def log_viam(self, type, msg):
    #     if type == 'debug':
    #         LOGGER.debug(msg)
    #     elif type == 'info':
    #         LOGGER.info(msg)
    #     elif type == 'warning':
    #         LOGGER.warn(msg)
    #     elif type == 'error':
    #         LOGGER.error(msg)
    #     elif type == 'critical':
    #         LOGGER.critical(msg)