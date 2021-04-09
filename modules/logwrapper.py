from pubsub import pub
import logging
import os

class LogWrapper:

    def __init__(self, **kwargs):
        self.path = kwargs.get('path', '/')
        self.filename = kwargs.get('filename', 'app.log')
        self.file = self.path + '/' + self.file

        logging.basicConfig(filename= self.file, level=logging.DEBUG, format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

        pub.subscribe(self.log, 'log', type='info')
        pub.subscribe(self.log, 'log:debug', type='debug')
        pub.subscribe(self.log, 'log:info', type='info')
        pub.subscribe(self.log, 'log:error', type='error')
        pub.subscribe(self.log, 'log:warning', type='warning')

    def __del__(self):
        os.rename(self.file, self.file + '.previous')

    def log(self, type, msg):
        logging.log(type, msg)
        if type == 'error' or type == 'warning':
            print('LogWrapper: ' + type + ' - ' + msg)

