from modules.snowboy import snowboydecoder
import signal

from pubsub import pub

interrupted = False

class HotWord:
    """
    Use snowboydecoder.py (https://snowboydecoder.py.kitt.ai) to listen for a given keyword, specified in the trained model
    """
    def __init__(self, **kwargs):
        self.interrupted = False
        signal.signal(signal.SIGINT, self.signal_handler)

        self.detector = snowboydecoder.HotwordDetector(kwargs.get('model', 'modules/robot.pmdl'), sensitivity=0.5)

        print('listening for hotword')

        self.detector.start(detected_callback=kwargs.get('callback', self.detected_callback),
                            interrupt_check=self.interrupt_callback,
                            sleep_time=0.03)

    def __del__(self):
        global interrupted
        interrupted = True
        self.detector.terminate()

    def signal_handler(self, signal, frame):
        global interrupted
        print('interrupt')
        interrupted = True

    def detected_callback(self):
        global interrupted
        print('detected')
        pub.sendMessage('hotword')
        interrupted = True

    def interrupt_callback(self):
        global interrupted
        return interrupted
