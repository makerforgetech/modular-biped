import board

class Config:
    # Power Management
    POWER_ENABLE_PIN = 2

    # Pan Servo
    PAN_PIN = 27
    PAN_RANGE = (560, 2450)
    PAN_START_POS = 55

    # Tilt Servo
    TILT_PIN = 17
    TILT_RANGE = (1560, 1880)
    TILT_START_POS = 40

    # Linear Actuators
    LEG_PINS = (6, 13, 19, 26)
    LEG_RANGE = (0, 100)
    LEG_START_POS = 0

    # RGB NeoPixels
    PIXEL_PIN = board.D18
    PIXEL_COUNT = 5

