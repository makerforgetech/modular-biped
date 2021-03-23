
class Config:
    # Application settings
    LOOP_FREQUENCY = 2

    MODE_TRACK_MOTION = 0
    MODE_TRACK_FACES = 1
    MODE_SLEEP = 2
    MODE_ANIMATE = 3
    MODE_OFF = 4
    MODE_KEYBOARD = 5
    MODE_RANDOM_BEHAVIOUR = 6

    MODE = MODE_KEYBOARD

    # GPIO
    # gpio = pigpio.pi()

    # Power Management
    POWER_ENABLE_PIN = 11
    SLEEP_TIMEOUT = 1  # Minutes

    # Audio
    BUZZER_PIN = 27

    # Microwave sensor pin
    MOTION_PIN = 13

    servos = dict()
    servos['neck'] = {'pin': 2, 'range': [36, 170], 'start': 95}
    servos['tilt'] = {'pin': 3, 'range': [36, 125], 'start': 55}
    #servos['pan'] = {'pin': 4, 'range': [0, 180], 'start': 55}
    servos['leg_l_hip'] = {'pin': 8, 'range': [0, 180], 'start': 80}
    servos['leg_l_knee'] = {'pin': 9, 'range': [0, 180], 'start': 5}
    servos['leg_l_ankle'] = {'pin': 10, 'range': [0, 180], 'start': 35}
    servos['leg_r_hip'] = {'pin': 5, 'range': [0, 180], 'start': 20}
    servos['leg_r_knee'] = {'pin': 6, 'range': [0, 180], 'start': 100}
    servos['leg_r_ankle'] = {'pin': 7, 'range': [0, 180], 'start': 65}

    # Head and neck
    # NECK_PIN = 3
    # TILT_PIN = 4
    # PAN_PIN = 5
    #
    # TILT_RANGE = [81, 117]
    # PAN_RANGE = [0, 180]
    # NECK_RANGE = [45, 117]
    #
    # TILT_START_POS = 50
    # PAN_START_POS = 50
    # NECK_START_POS = 75
    #
    # # Right Leg
    # LEG_R_HIP_PIN = 6
    # LEG_R_KNEE_PIN = 7
    # LEG_R_ANKLE_PIN = 8
    #
    # # Left Leg
    # LEG_L_HIP_PIN = 9
    # LEG_L_KNEE_PIN = 10
    # LEG_L_ANKLE_PIN = 11
    #
    # LEG_HIP_RANGE = [0, 180]
    # LEG_KNEE_RANGE = [0, 180]
    # LEG_ANKLE_RANGE = [0, 180]
    #
    # LEG_L_HIP_START_POS = 50
    # LEG_L_KNEE_START_POS = 45
    # LEG_L_ANKLE_START_POS = 50
    #
    # LEG_R_HIP_START_POS = 55
    # LEG_R_KNEE_START_POS = 55
    # LEG_R_ANKLE_START_POS = 50

    # RGB NeoPixels
    LED_COUNT = 7

    # HotWord (uses Snowboy.ai)
    HOTWORD_MODEL = 'modules/snowboy/resources/models/robot.pmdl'
    HOTWORD_SLEEP_TIME = 0.03

