import snowboydecoder
import signal


class HotWord:
    """
    Use snowboy (https://snowboy.kitt.ai) to listen for a given keyword, specified in the trained model
    """
    def __init__(self, **kwargs):
        self.interrupted = False
        signal.signal(signal.SIGINT, self.signal_handler)

        detector = snowboydecoder.HotwordDetector(kwargs.get('model', 'robot.pmdl'), sensitivity=0.5)

        detector.start(detected_callback=snowboydecoder.ding_callback,
                       interrupt_check=kwargs.get('callback', self.interrupt_callback),
                       sleep_time=0.03)

    def __del__(self):
        self.detector.terminate()

    def signal_handler(self, signal, frame):
        print('handler')
        self.interrupted = True

    def interrupt_callback(self):
        print('callback')
        return self.interrupted
