from modules.snowboy import snowboydecoder
import threading
import queue
from pubsub import pub


class HotWord(threading.Thread):
    """
    Wrapper class around detectors to run them in a separate thread
    and provide methods to pause, resume, and modify detection
    """

    def __init__(self, models, **kwargs):
        """
        Initialize Detectors object. **kwargs is for any __init__ keyword
        arguments to be passed into HotWordDetector __init__() method.
        """
        threading.Thread.__init__(self)
        self.models = models
        self.init_kwargs = kwargs
        self.interrupted = True
        self.commands = queue.Queue()
        self.vars_are_changed = True
        self.detectors = None  # Initialize when thread is run in self.run()
        self.run_kwargs = None  # Initialize when detectors start in self.start_recog()
        pub.subscribe(self.exit, 'exit')

    def exit(self):
        self.terminate()

    def initialize_detectors(self):
        """
        Returns initialized Snowboy HotwordDetector objects
        """
        self.detectors = snowboydecoder.HotwordDetector(self.models, **self.init_kwargs)

    def run(self):
        """
        Runs in separate thread - waits on command to either run detectors
        or terminate thread from commands queue
        """
        try:
            while True:
                command = self.commands.get(True)
                if command == "Start":
                    self.interrupted = False
                    if self.vars_are_changed:
                        # If there is an existing detector object, terminate it
                        if self.detectors is not None:
                            self.detectors.terminate()
                        self.initialize_detectors()
                        self.vars_are_changed = False
                    # Start detectors - blocks until interrupted by self.interrupted variable
                    pub.sendMessage('log', msg='[Hotword] Running')
                    self.detectors.start(detected_callback=self.detected_callback, interrupt_check=lambda: self.interrupted, **self.run_kwargs)
                elif command == "Terminate":
                    # Program ending - terminate thread
                    break
        finally:
            if self.detectors is not None:
                self.detectors.terminate()

    def detected_callback(self):
        pub.sendMessage('log', msg='[Hotword] Detected')
        pub.sendMessage('hotword')

    def start_recog(self, **kwargs):
        """
        Starts recognition in thread. Accepts kwargs to pass into the
        HotWordDetector.start() method, but does not accept interrupt_callback,
        as that is already set up.
        """
        assert "interrupt_check" not in kwargs, \
            "Cannot set interrupt_check argument. To interrupt detectors, use Detectors.pause_recog() instead"
        self.run_kwargs = kwargs
        self.commands.put("Start")

    def pause_recog(self):
        """
        Halts recognition in thread.
        """
        self.interrupted = True

    def terminate(self):
        """
        Terminates recognition thread - called when program terminates
        """
        self.pause_recog()
        self.commands.put("Terminate")

    def is_running(self):
        return not self.interrupted

    def change_models(self, models):
        if self.is_running():
            print("Models will be changed after restarting detectors.")
        if self.models != models:
            self.models = models
            self.vars_are_changed = True

    def change_sensitivity(self, sensitivity):
        if self.is_running():
            print("Sensitivity will be changed after restarting detectors.")
        if self.init_kwargs['sensitivity'] != sensitivity:
            self.init_kwargs['sensitivity'] = sensitivity
            self.vars_are_changed = True