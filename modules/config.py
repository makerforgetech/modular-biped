class Config:
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

    TILT_RANGE = [0, 180]
    PAN_RANGE = [0, 180]
    NECK_RANGE = [0, 180]

    TILT_START_POS = 50
    PAN_START_POS = 50
    NECK_START_POS = 50

    # RGB NeoPixels
    LED_COUNT = 7
    LED_MIDDLE = 0
    LED_ALL = range(LED_COUNT)

    # HotWord (uses Snowboy.ai)
    HOTWORD_MODEL = 'modules/snowboy/resources/models/robot.pmdl'
    HOTWORD_SLEEP_TIME = 0.03

