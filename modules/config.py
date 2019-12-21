class Config:
    # Power Management
    POWER_ENABLE_PIN = 2
    SLEEP_TIMEOUT = 1  # Minutes

    # Audio
    AUDIO_ENABLE_PIN = 12  # Arduino pin handling audio power

    # Microwave sensor pin
    MOTION_PIN = 4

    # Head and neck
    LOWER_NECK_PIN = 3
    UPPER_NECK_PIN = 4
    HEAD_ROTATE_PIN = 5

    # RGB NeoPixels
    LED_COUNT = 7
    LED_MIDDLE = 0
    LED_ALL = range(LED_COUNT)

    # HotWord (uses Snowboy.ai)
    HOTWORD_MODEL = 'modules/snowboy/Robot.pmdl'
    HOTWORD_SLEEP_TIME = 0.03

