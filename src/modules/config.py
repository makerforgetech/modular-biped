#! /usr/bin/python
from time import localtime
import yaml
import glob
import json

class Config:
    # Load all yaml files in config folder
    config = dict()
    for file in glob.glob("config/*.yml"):
        config.update(yaml.safe_load(open(file)))
        
    @staticmethod
    def get(key):
        return Config.get(key, None)
    
    @staticmethod
    def get(key, key2):
        if key2 == None:
            return Config.config[key]
        return Config.config[key][key2]
    
    @staticmethod
    def get_all_pins():
        '''Returns list of tuple for all pins used in any config file'''
        pins = []
        for key in Config.config:
            if 'pin' in Config.config[key] and Config.config[key]['pin'] != 'None':
                pins.append([key, Config.config[key]['pin']])
        return pins
    
    # Application settings
    LOOP_FREQUENCY = 2

    MODE_TRACK_MOTION = 0
    MODE_TRACK_FACES = 1
    MODE_SLEEP = 2
    MODE_ANIMATE = 3
    MODE_OFF = 4
    MODE_KEYBOARD = 5
    MODE_LIVE = 6


    # VISION_TECH = 'coral' # or 'opencv'
    # VISION_MODE = 'object' # 'face' or 'object'
    # DEBUG_VISION = False # Creates loop to focus on tracking without personality etc.

    # GPIO
    # gpio = pigpio.pi()

    # Power Management
    # POWER_ENABLE_PIN = 11
    # SLEEP_TIMEOUT = 1  # Minutes

    # # Audio
    # BUZZER_PIN = 27

    # # Microwave sensor pin
    # MOTION_PIN = 13

    # servos = dict()
    # # Everything is percentages except the range values.
    # servos['leg_l_hip'] = {'id': 0, 'pin': 9, 'range': [20, 160], 'start': 19}
    # servos['leg_l_knee'] = {'id': 1, 'pin': 10, 'range': [5, 175], 'start': 12}
    # servos['leg_l_ankle'] = {'id': 2, 'pin': 11, 'range': [40, 180], 'start': 52}
    # servos['leg_r_hip'] = {'id': 3, 'pin': 6, 'range': [20, 160], 'start': 93}
    # servos['leg_r_knee'] = {'id': 4, 'pin': 7, 'range': [5, 175], 'start': 90}
    # servos['leg_r_ankle'] = {'id': 5, 'pin': 8, 'range': [40, 180], 'start': 88}
    # servos['tilt'] = {'id': 6, 'pin': 2, 'range': [60, 120], 'start': 75}
    # servos['pan'] = {'id': 7, 'pin': 3, 'range': [20, 160], 'start': 50}

    # # RGB NeoPixels
    # LED_COUNT = 7

    # # HotWord (uses Snowboy.ai)
    # HOTWORD_MODEL = None #'modules/snowboy/resources/models/robot.pmdl'
    # HOTWORD_SLEEP_TIME = 0.03

    STATE_SLEEPING = 0
    STATE_RESTING = 1
    STATE_IDLE = 2
    STATE_ALERT = 3

    NIGHT_HOURS = [22, 8]  # night start and end. Will not wake during this time

    @staticmethod
    def exit(signum, frame):
        raise Exception('Exit command received!')

    @staticmethod
    def is_night():
        t = localtime()
        if Config.NIGHT_HOURS[1] < t.tm_hour < Config.NIGHT_HOURS[0]:
            return False
        return True

# if main
if __name__ == "__main__":
    c = Config()
    print(json.dumps(Config.config, indent=2))
    print('Pins: ' + str(Config.get_all_pins()))
