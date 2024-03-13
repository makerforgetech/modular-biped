import asyncio
import os

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.services.vision import VisionClient
from viam.components.camera import Camera
import setenv # I added this
from datetime import datetime

from pubsub import pub

from viam.logging import getLogger
LOGGER = getLogger(__name__)
LOGGER.info('INIT MAKERFORGE MAIN_VIAM')
# LOGGER.warning('LOOP MAKERFORGE MAIN_VIAM')
# LOGGER.error('LOOP MAKERFORGE MAIN_VIAM')

#### MAIN ####

import logging
logging.basicConfig(filename=os.path.dirname(__file__) + '/app.log', level=logging.DEBUG, format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p') # this doesn't work unless it's here
from modules.logwrapper import LogWrapper

from time import sleep, time
import signal
import schedule

# Import modules
from modules.config import Config
from modules.actuators.servo import Servo
from modules.actuators.piservo import PiServo
from modules.animate import Animate
from modules.sensor import Sensor
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

### MAIN END ###

# from modules.viam.viamobjects import ViamObjects

# These must be set. You can get them from your robot's 'Code sample' tab
robot_api_key = os.getenv('ROBOT_API_KEY') or ''
robot_api_key_id = os.getenv('ROBOT_API_KEY_ID') or ''
robot_address = os.getenv('ROBOT_ADDRESS') or ''

async def connect():
    opts = RobotClient.Options.with_api_key(
      api_key=robot_api_key,
      api_key_id=robot_api_key_id
    )
    return await RobotClient.at_address(robot_address, opts)


async def main():
    robot = await connect()
    
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
        
        
    try:
        neopx = NeoPx(Config.get('neopixel','count'))
    except ValueError as e:
        print('Error initializing NeoPixel: ' + str(e))
    # tts = TTS(translator=translator)

    if Config.get('motion','pin') != '':
        motion = Sensor(Config.get('motion','pin'))
    
    # personality = Personality()
    temp = PiTemperature()
    animate = Animate()

    # Nightly loop (for facial recognition model training)
    schedule.every().day.at("10:30").do(pub.sendMessage, 'loop:nightly')
    # Other more frequent loops
    second_loop = time()
    ten_second_loop = time()
    minute_loop = time()
    loop = True
    
    # # viamobjects = ViamObjects(robot)
    
    # pub.sendMessage('vision:start')
        
    try:
        while loop:
            # await viamobjects.detect()
            pub.sendMessage('loop')
            if time() - second_loop > 1:
                #LOGGER.info('LOOP MAKERFORGE MAIN_VIAM')
                second_loop = time()
                pub.sendMessage('loop:1')
            if time() - ten_second_loop > 10:
                ten_second_loop = time()
                pub.sendMessage('loop:10')
                # loop = False # remove after testing
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
    
    # await asyncio.sleep(5)
    await robot.close()

if __name__ == '__main__':
    asyncio.run(main())
