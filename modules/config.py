class Config:
    # Application settings
    LOOP_FREQUENCY = 2


    # Power Management
    POWER_ENABLE_PIN = 2
    SLEEP_TIMEOUT = 1  # Minutes

    # Audio
    AUDIO_ENABLE_PIN = 12  # Arduino pin handling audio power

    # Microwave sensor pin
    MOTION_PIN = 4

    # Head and neck
    NECK_PIN = 3
    TILT_PIN = 4
    PAN_PIN = 5

    TILT_RANGE = [81, 117]
    PAN_RANGE = [0, 180]
    NECK_RANGE = [45, 117]

    TILT_START_POS = 50
    PAN_START_POS = 50
    NECK_START_POS = 50

    # Right Leg
    LEG_R_HIP_PIN = 6
    LEG_R_KNEE_PIN = 7
    LEG_R_ANKLE_PIN = 8

    # Left Leg
    LEG_L_HIP_PIN = 9
    LEG_L_KNEE_PIN = 10
    LEG_L_ANKLE_PIN = 11

    LEG_HIP_RANGE = [0, 180]
    LEG_KNEE_RANGE = [0, 180]
    LEG_ANKLE_RANGE = [0, 180]

    LEG_HIP_START_POS = 50
    LEG_KNEE_START_POS = 50
    LEG_ANKLE_START_POS = 50

    # RGB NeoPixels
    LED_COUNT = 7

    # HotWord (uses Snowboy.ai)
    HOTWORD_MODEL = 'modules/snowboy/resources/models/robot.pmdl'
    HOTWORD_SLEEP_TIME = 0.03

