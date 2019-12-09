import board

class Config:
    # Power Management
    POWER_ENABLE_PIN = 2
    SLEEP_TIMEOUT = 1  # Minutes

    # Microwave sensor pin
    MOTION_PIN = 4

    # Pan Servo
    PAN_PIN = 27
    PAN_RANGE = (560, 2450)
    PAN_START_POS = 55

    # Tilt Servo
    TILT_PIN = 17
    TILT_RANGE = (1560, 1880)
    TILT_START_POS = 35

    # Linear Actuators
    LEG_PINS = (6, 13, 19, 26)
    LEG_RANGE = (0, 280)  # 14 * 20
    LEG_START_POS = 0

    # RGB NeoPixels
    PIXEL_PIN = board.D18
    PIXEL_COUNT = 5

    PIXEL_EYES = [1, 2]
    PIXEL_MOUTH = [3, 4]
    PIXEL_FRONT = PIXEL_EYES + PIXEL_MOUTH
    PIXEL_TOP = [5, 6, 7, 8]
    PIXEL_LEFT = [9, 10]
    PIXEL_RIGHT = [11, 12, 13, 14]
    PIXEL_BACK = [15, 16, 17, 18]
    PIXEL_HEAD = PIXEL_TOP + PIXEL_LEFT + PIXEL_RIGHT + PIXEL_BACK
    PIXEL_ALL = PIXEL_FRONT + PIXEL_HEAD


