import asyncio
import os

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.services.vision import VisionClient
from viam.services.generic import Generic
from viam.components.camera import Camera
import setenv # I added this
from datetime import datetime

from pubsub import pub

'''
    Viam main script - currently replacing this with viam modules.
    Viam Logger is viam disabled in logwrapper.py. Uncomment to re-enable.
'''

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
# from modules.opencv.timelapse import Timelapse

### MAIN END ###

# from modules.viam.viamobjects import ViamObjects
from modules.viam.viamclassifier import ViamClassifier

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
    
    # viamobjects = ViamObjects(robot)
    # viamobjects.enable()
    #viamGestures = ViamClassifier(robot)
    #pub.sendMessage('vision:start')
    # 
    
    print('Resources:')
    print(robot.resource_names)
    
    animation = Generic.from_robot(robot, "animation-service")

    # Uncomment to show failure    
    # response = await animation.do_command({"animate": ["not_an_animation"]})
    
    response = await animation.do_command({"animate": ["scan"]})
    
    # Until we have a working MQTT broker
    # Parse response and use pubsub to send message to animate
    # Example response: {'animate': [['servo:pan:mv', [20.0]], ['servo:pan:mv', [-40.0]], ['servo:pan:mv', [40.0]], ['servo:pan:mv', [-40.0]], ['servo:pan:mv', [20.0]]]}
    for command in response['animate']:
        pub.sendMessage(command[0], percentage=command[1][0])
    
    # # print(f"The response is {response}")
    # print(response)
    
    # GESTURE TEST
    # camera_name = "camera"
    # my_webcam = Camera.from_robot(robot, camera_name)
    # my_webcam_return_value = await my_webcam.get_image()
    # print(f"my-webcam get_image return value: {my_webcam_return_value}")
    # roboflow_test = VisionClient.from_robot(robot, "roboflow-test")
    
                
        
    try:
        while loop:
            
            pub.sendMessage('loop')
            if time() - second_loop > 1:
                LOGGER.info('LOOP MAKERFORGE MAIN_VIAM')
                # await viamobjects.detect()
                #await viamGestures.detect()
                second_loop = time()
                pub.sendMessage('loop:1')
                # roboflow_test_return_value = await roboflow_test.get_detections_from_camera(camera_name)
                # print(f"roboflow-test get_detections_from_camera return value: {roboflow_test_return_value}")
            if time() - ten_second_loop > 10:
                ten_second_loop = time()
                pub.sendMessage('loop:10')
                pub.sendMessage('vision:start')
                # pub.sendMessage('animate', action='head_shake')
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
