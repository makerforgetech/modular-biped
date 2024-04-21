import os
from pubsub import pub
import logging
logging.basicConfig(filename=os.path.dirname(__file__) + '/app.log', level=logging.DEBUG, format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p') # this doesn't work unless it's here
from modules.logwrapper import LogWrapper

# try:
#     import pigpio
# except ModuleNotFoundError as e:
#     from modules.mocks.mock_pigpio import MockPiGPIO
#     import pigpio
#     from modules.mocks.mock_cv2 import MockCV2

from time import sleep, time
import signal
import schedule

# Import modules
from modules.config import Config
from modules.actuators.servo import Servo
from modules.actuators.piservo import PiServo
from modules.animate import Animate
# from modules.power import Power
# from modules.keyboard import Keyboard
# from modules.gamepad import Gamepad
from modules.sensor import Sensor
# try:
#     from modules.hotword import HotWord
# except ModuleNotFoundError as e:
#     pass

import sys

# from modules.speechinput import SpeechInput
from modules.arduinoserial import ArduinoSerial
from modules.neopx import NeoPx
# from modules.tts import TTS
from modules.personality import Personality
# from modules.battery import Battery
from modules.braillespeak import Braillespeak
from modules.buzzer import Buzzer
from modules.pitemperature import PiTemperature

from modules.translator import Translator

# if Config.get('vision', 'tech') == 'opencv':
#     from modules.opencv.vision import Vision
#     from modules.opencv.tracking import Tracking
#     from modules.opencv.train_model import TrainModel
#     from modules.opencv.video_stream import VideoStream
#     from modules.opencv.timelapse import Timelapse
# elif Config.get('vision', 'tech') == 'coral':
#     from modules.coral.vision import Vision
#     from modules.coral.tracking import Tracking



def mode():
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        return Config.MODE_KEYBOARD
    return Config.MODE_LIVE

def main():
    print('Starting...')
    
    path = os.path.dirname(__file__)
    translator = Translator(src=Config.get('translator', 'default')['src'], dest=Config.get('translator', 'default')['dest'])
    log = LogWrapper(path=os.path.dirname(__file__), translator=translator)
    

    # Throw exception to safely exit script when terminated
    signal.signal(signal.SIGTERM, Config.exit)

    # GPIO
    # gpio = pigpio.pi()

    # Arduino connection
    serial = ArduinoSerial()

    servos = dict()
    servo_conf = Config.get('servos','conf')
    for key in servo_conf:
        s = servo_conf[key]
        servos[key] = Servo(s['pin'], key, s['range'], s['id'], start_pos=s['start'])
        
    piservos = dict()
    piservo_conf = Config.get('piservo','conf')
    for key in piservo_conf:
        s = piservo_conf[key]
        piservos[key] = PiServo(s['pin'], s['range'], start_pos=s['start'])

    # pub.sendMessage('log', msg="[Main] Starting pan test")
    # pub.sendMessage('servo:pan:mvabs', percentage=0)
    # sleep(2)
    # pub.sendMessage('log', msg="[Main] Finished looking left")
    # pub.sendMessage('servo:pan:mvabs', percentage=100)
    # sleep(2)
    # pub.sendMessage('log', msg="[Main] Finished looking right")
    # pub.sendMessage('servo:pan:mvabs', percentage=50)
    # sleep(2)
    # pub.sendMessage('servo:tilt:mvabs', percentage=100)
    # sleep(2)
    # pub.sendMessage('log', msg="[Main] Finished looking up")
    # pub.sendMessage('servo:tilt:mvabs', percentage=0)
    # sleep(2)
    # pub.sendMessage('log', msg="[Main] Finished looking down")
    # sleep(10)
    # pub.sendMessage('log', msg="[Main] Finished testing")
    #return
    # power = Power(Config.POWER_ENABLE_PIN)

    neopx = NeoPx(Config.get('neopixel','count'))
    # tts = TTS(translator=translator)

    if Config.get('motion','pin') != '':
        motion = Sensor(Config.get('motion','pin'))

    pub.sendMessage('tts', msg='I am awake.')
    pub.sendMessage('speak', msg='hi')

    if mode() == Config.MODE_LIVE:
        # Vision / Tracking
        preview = False
        if len(sys.argv) > 1 and sys.argv[1] == 'preview':
            preview = True
            
        # if Config.get('vision','tech') == 'opencv':
        #     camera_resolution = (640, 480) #(1024, 768) #- this halves the speed of image recognition
        #     video_stream = VideoStream(resolution=camera_resolution).start()
        #     vision = Vision(video_stream, mode=Vision.MODE_FACES, path=path, preview=preview, resolution=camera_resolution)
        #     tracking = Tracking(vision)
        #     training = TrainModel(dataset=path + '/matches/trained', output='encodings.pickle')
        #     # timelapse = Timelapse(video_stream, path=path, original_resolution=camera_resolution)
        # elif Config.get('vision','tech') == 'coral':
        #     if Config.get('vision', 'debug'):
        #         # Testing - for fine-tuning tracking without the other stuff
        #         pub.sendMessage('wake')
        #         # pub.sendMessage('power:use')
        #         pub.sendMessage("servo:tilt:mvabs", percentage=50)
        #         pub.sendMessage("servo:pan:mvabs", percentage=50)
        #         sleep(1)

        #     vision = Vision(preview=preview, mode=Config.get('vision','initial_mode'))
        #     tracking = Tracking()

        #     if Config.get('vision', 'debug'):
        #         while True:
        #             pass

        personality = Personality()
    # elif mode() == Config.MODE_KEYBOARD:
        # keyboard = Keyboard()

    # gamepad = Gamepad()
    temp = PiTemperature()

    # Voice
    # if Config.get('hotword', 'model') != '':
    #     hotword = HotWord(Config.get('hotword', 'model'))
    #     hotword.start()  # @todo this starts the thread. can it be moved into hotword?
    #     hotword.start_recog(sleep_time=Config.get('hotword', 'sleep_time'))
    #     sleep(1)  # @todo is this needed?
        # @todo this is throwing errors: ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'defaults.bluealsa.device'

    #speech = SpeechInput()
    # Output
    # if Config.get('buzzer', 'pin') != '':
        # speak = Braillespeak(Config.get('buzzer', 'pin'), duration=80/1000)
        # buzzer = Buzzer(Config.get('buzzer', 'pin'))
    
    animate = Animate()

    # @todo 2k resistor needs switching to > 3k for 20v+ support.
    #battery = Battery(0, serial, path=path) # note: needs ref for pubsub to work

    # Nightly loop (for facial recognition model training)
    schedule.every().day.at("10:30").do(pub.sendMessage, 'loop:nightly')
    # Other more frequent loops
    second_loop = time()
    ten_second_loop = time()
    minute_loop = time()
    loop = True
    # pub.sendMessage('speak', message='hi')
    # pub.sendMessage('animate', action='celebrate')

    try:
        pub.sendMessage('log', msg="[Main] Loop started")
        while loop:
            pub.sendMessage('loop')
            if time() - second_loop > 1:
                second_loop = time()
                pub.sendMessage('loop:1')
            if time() - ten_second_loop > 10:
                ten_second_loop = time()
                pub.sendMessage('loop:10')
            if time() - minute_loop > 60:
                minute_loop = time()
                pub.sendMessage('loop:60')
                schedule.run_pending()

    except (Exception) as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        # output stack trace
        print(ex.with_traceback())
        print(message)
        pub.sendMessage('log:error', msg=ex)
        loop = False
        sleep(5)
        quit()

    finally:
        pub.sendMessage("exit")
        pub.sendMessage("animate", action="sit")
        pub.sendMessage("animate", action="sleep")
        pub.sendMessage("power:exit")
        pub.sendMessage("log", msg="[Main] loop ended")

if __name__ == '__main__':
    main()
