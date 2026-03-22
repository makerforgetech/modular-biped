import logging, json
import os, datetime
import shutil
from glob import glob
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
        self.subscribe('log/file', self.log, type='file')

    def __del__(self):
        try:
            if os.path.isfile(self.file):
                logs_dir = os.path.join(os.path.dirname(self.file), 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                prev_dir = os.path.join(logs_dir, 'previous')
                os.makedirs(prev_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                base = os.path.basename(self.file)
                prev_file = os.path.join(prev_dir, f"{base}.{timestamp}")
                shutil.move(self.file, prev_file)
                print(f"[Log file stored at {prev_file}]")
                # Remove all but the 10 most recent logs
                prev_logs = sorted(glob(os.path.join(prev_dir, f"{base}.*")), reverse=True)
                for old_log in prev_logs[10:]:
                    try:
                        os.remove(old_log)
                    except Exception as e:
                        print(f"[Error removing old log {old_log}: {e}]")
        except Exception as e:
            # Avoid raising exceptions during GC/interpreter shutdown
            print(f"[LogWrapper __del__ suppressed exception: {e}]")

    def log(self, message):
        self.log('info', message)

    def log(self,  message, type='info'):
        if type=='file':
            self.create_file(message)
            return
            
        # if message is a json object as a string
        if isinstance(message, str) and message.startswith('{'):
            message = json.loads(message)['message']
                
        if self.translator is not None:
            message = self.translator.request(message)

        logging.log(LogWrapper.levels.index(type)*10, message) # Filter on log level is handled by logging module
         
        if LogWrapper.levels.index(self.cli_level) <= LogWrapper.levels.index(type):
            print('log/' + type + ': ' + str(message))
    
    def create_file(self, message):
        # Extract caller information (format: [{class_name}.{method_name}:{frame.lineno}] {str(message)})
        caller = message.split(']')[0][1:]  # Get text between [ and ]
        # Extract class name
        class_name = caller.split('.')[0]
        # Create filename from caller and timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{caller}_{timestamp}.log".replace(':', '_')  # Replace : with _ for filename safety
        # file path should include logs directory, create if doesn't exist
        logs_dir = os.path.join(self.path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        # add class name to file path as directory, create if not present
        class_dir = os.path.join(logs_dir, class_name)
        os.makedirs(class_dir, exist_ok=True)
        filepath = os.path.join(class_dir, filename)
        with open(filepath, 'w') as f:
            f.write(message)
        print(f"[Created log file at {filepath}]")