from pubsub import pub
from time import sleep
from colour import Color
import board
from modules.network.arduinoserial import set_led_pin
    
import threading

class NeoPx:
    COLOR_OFF = (0, 0, 0)
    COLOR_RED = (100, 0, 0)
    COLOR_GREEN = (0, 100, 0)
    COLOR_BLUE = (0, 0, 100)
    COLOR_PURPLE = (100, 0, 100)
    COLOR_WHITE = (100, 100, 100)
    COLOR_WHITE_FULL = (255, 255, 255)
    COLOR_WHITE_DIM = (50, 50, 50)
    COLOR_RED_TO_GREEN_100 = list(Color("red").range_to(Color("green"),100))
    COLOR_BLUE_TO_RED_100 = list(Color("blue").range_to(Color("red"),100)) # also passes through green
    COLOR_BLUE_TO_GREEN_100 = list(Color("blue").range_to(Color("green"),100))

    COLOR_MAP = {
        'red': COLOR_RED,
        'green': COLOR_GREEN,
        'blue': COLOR_BLUE,
        'purple': COLOR_PURPLE,
        'white': COLOR_WHITE,
        'white_full': COLOR_WHITE_FULL,
        'off': COLOR_OFF,
        'white_dim': COLOR_WHITE_DIM
    }

    # Add named colors from Arduino for ESP32 compatibility
    ARDUINO_COLOR_MAP = {
        'RED': (255, 0, 0),
        'GREEN': (0, 255, 0),
        'BLUE': (0, 0, 255),
        'YELLOW': (255, 255, 0),
        'PURPLE': (255, 0, 255),
        'CYAN': (0, 255, 255),
        'WHITE': (255, 255, 255),
        'ORANGE': (255, 165, 0),
        'PINK': (255, 105, 180),
        'GOLD': (255, 215, 0),
        'TEAL': (0, 128, 128),
        'MAGENTA': (255, 0, 127),
        'LIME': (50, 205, 50),
        'SKY_BLUE': (135, 206, 235),
        'NAVY': (0, 0, 128),
        'MAROON': (128, 0, 0),
        'AQUA': (127, 255, 212),
        'VIOLET': (138, 43, 226),
        'CORAL': (255, 127, 80),
        'TURQUOISE': (64, 224, 208)
    }

    def __init__(self, **kwargs):
        """
        NeoPx class
        :param kwargs: count, positions, brightness, i2c
        :param count: number of neopixels
        :param positions: dictionary of positions
        :param brightness: list of brightness values for each neopixel
        :param i2c: boolean to use i2c
        
        Install: pip install adafruit-circuitpython-seesaw
        
        Subscribes to 'led' to set color of pixel
        - Argument: identifiers (int or list) - pixel number (starting from 0)
        - Argument: color (string or tuple) - string map of COLOR_MAP or tuple (R, G, B)
        
        Subscribes to 'led:full' to set all pixels to one color
        - Argument: color (string or tuple) - string map of COLOR_MAP or tuple (R, G, B)
        
        Subscribes to 'led:eye' to set eye color
        - Argument: color (string or tuple) - string map of COLOR_MAP or tuple (R, G, B)
        
        Subscribes to 'led:ring' to set ring color
        - Argument: color (string or tuple) - string map of COLOR_MAP or tuple (R, G, B)
        
        Subscribes to 'led:off' to turn off all pixels
        
        Subscribes to 'led:flashlight' to turn on/off all pixels
        - Argument: on (bool) - turn on or off
        
        Subscribes to 'led:party' to start party mode
        
        Subscribes to 'exit' to clean up
        
        Subscribes to 'speech' to handle speech commands
        - Argument: msg (string) - speech command

        Subscribes to 'led:animate' to trigger animations (when ESP32 protocol is used)
        - Argument: animation (string) - animation name
        - Argument: color (string or tuple) - optional color
        - Argument: color2 (string or tuple) - optional second color for animations that need it
        - Argument: repeat (int) - optional repeat count
        
        Example:
        pub.sendMessage('led', identifiers=1, color='red')
        pub.sendMessage('led:full', color='red')
        pub.sendMessage('led:eye', color='red')
        pub.sendMessage('led:ring', color='red')
        pub.sendMessage('led:off')
        pub.sendMessage('led:flashlight', on=True)
        pub.sendMessage('led:party')
        pub.sendMessage('exit')
        pub.sendMessage('speech', msg='light on')
        pub.sendMessage('led:animate', animation='RAINBOW', repeat=3)
        pub.sendMessage('led:animate', animation='COLOR_WIPE', color='RED', repeat=2)
        pub.sendMessage('led:animate', animation='ALTERNATING', color='RED', color2='BLUE', repeat=5)
        """
        # Initialise
        self.count = kwargs.get('count')
        self.positions = kwargs.get('positions')
        # Manually adjust brightness of individual neopixels
        self.brightness = kwargs.get('brightness')
        self.all = range(self.count)
        self.all_eye = ['right', 'top_right', 'top_left', 'left', 'bottom_left', 'bottom_right', 'middle']
        self.ring_eye = ['right', 'top_right', 'top_left', 'left', 'bottom_left', 'bottom_right']
        self.animation = False
        self.thread = None
        self.overridden = False  # prevent any further changes until released (for flashlight)
        
        # Ensure only one valid protocol is active
        accepted_protocols = ['I2C', 'SPI', 'ESP32', 'GPIO']
        self.protocol = kwargs.get('protocol')
        if self.protocol not in accepted_protocols:
            raise ValueError("Invalid protocol specified. Choose one of: " + ", ".join(accepted_protocols))
        
        if self.protocol == 'I2C':
            import busio
            from rainbowio import colorwheel
            from adafruit_seesaw import seesaw, neopixel
            self.i2c = busio.I2C(board.SCL, board.SDA)
            try:
                ss = seesaw.Seesaw(self.i2c, addr=0x60)
            except:
                # If i2c fails, try again
                self.i2c.deinit()
                self.i2c = busio.I2C(board.SCL, board.SDA)
                ss = seesaw.Seesaw(self.i2c, addr=0x60)
            neo_pin = 15 # Unclear how this is used
            self.pixels = neopixel.NeoPixel(ss, neo_pin, self.count, brightness = 0.1)
        elif self.protocol == 'SPI':
            import neopixel_spi as neopixel
            spi = board.SPI()
            self.pixels = neopixel.NeoPixel_SPI(spi, self.count, brightness=0.1, auto_write=False, pixel_order=neopixel.GRB)    
            
            DELAY = 3
            print("All neopixels OFF")
            self.pixels.fill((0,0,0))
            self.pixels.show()
            sleep(DELAY)

            print("First neopixel red, last neopixel blue")
            self.pixels[0] = (10,0,0)
            self.pixels[self.count - 1] = (0,0,10)
            self.pixels.show()
            sleep(DELAY)

            print("All " + str(self.count) + " neopixels green")
            self.pixels.fill((0,10,0))
            self.pixels.show()
            sleep(DELAY)

            print("All neopixels OFF")
            self.pixels.fill((0,0,0))
            self.pixels.show()
            sleep(DELAY)

            print("End of test")
        elif self.protocol == 'ESP32':
            import serial
            # Open USB serial port (configured via kwargs)
            self.serial = serial.Serial(
                kwargs.get('serial_port', '/dev/ttyUSB0'),
                kwargs.get('baudrate', 115200),
                timeout=1
            )
        else: # GPIO
            import neopixel
            self.pixels = neopixel.NeoPixel(kwargs.get('pin'), self.count)
        # Default states
        self.set(self.all, NeoPx.COLOR_OFF)
        sleep(0.1)
        self.set(self.positions['middle'], NeoPx.COLOR_BLUE)

        # Set subscribers
        pub.subscribe(self.set, 'led')
        pub.subscribe(self.full, 'led:full')
        pub.subscribe(self.eye, 'led:eye')
        pub.subscribe(self.ring, 'led:ring')
        pub.subscribe(self.off, 'led:off')
        pub.subscribe(self.eye, 'led:flashlight')
        pub.subscribe(self.party, 'led:party')
        pub.subscribe(self.exit, 'exit')
        pub.subscribe(self.speech, 'speech')
        pub.subscribe(self.handle_animate, 'led:animate')

    def exit(self):
        """
        On close of application carry out clean up
        """
        if self.animation:
            self.animation = False
            self.thread.join()
        self.set(self.all, NeoPx.COLOR_OFF)
        if self.protocol == 'I2C':
            self.i2c.deinit()
        elif self.protocol == 'ESP32':
            self.serial.close()
        sleep(1)

    def speech(self, text):
        if 'light on' in text:
            self.flashlight(True)
        if 'light off' in text:
            self.flashlight(False)

    def color_to_arduino_format(self, color):
        """Convert color to a format understood by Arduino code"""
        # If color is a string, check if it's in our Arduino color map
        if isinstance(color, str):
            # First try Arduino color map (upper case names)
            if color.upper() in self.ARDUINO_COLOR_MAP:
                return color.upper()
            # Then try our standard color map
            elif color in self.COLOR_MAP:
                # Return the RGB values directly
                rgb = self.COLOR_MAP[color]
                return f"{rgb[0]},{rgb[1]},{rgb[2]}"
        # If it's already an RGB tuple
        elif isinstance(color, tuple) and len(color) == 3:
            return f"{color[0]},{color[1]},{color[2]}"
        # Default to empty string if no valid color format found
        return ""

    def set(self, identifiers, color, gradient=False):
        """
        Set color of pixel
        (255, 0, 0) # set to red, full brightness
        (0, 128, 0) # set to green, half brightness
        (0, 0, 64)  # set to blue, quarter brightness
        :param identifiers: pixel number (starting from 0) - can be list
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        """
        if self.overridden:
            return
        # convert single identifier to list
        if type(identifiers) is int:
            identifiers = [identifiers]
        elif type(identifiers) is str:
            identifiers = [self.positions[identifiers]]
        # lookup color if string
        if type(color) is float:
            color = int(color)
        if type(color) is int:
            # Make color gradiant use possible @todo refactor
            if color >= 100:
                color = 99 # max in range
            if gradient == 'br':
                color = NeoPx.COLOR_BLUE_TO_RED_100[color].rgb
            elif gradient == 'bg':
                color = NeoPx.COLOR_BLUE_TO_GREEN_100[color].rgb
            else:
                color = NeoPx.COLOR_RED_TO_GREEN_100[color].rgb
            color = (round(color[0]*100), round(color[1]*100), round(color[2]*100)) # increase values to be used as LED RGB
        elif type(color) is str:
            color = NeoPx.COLOR_MAP[color]
        # If protocol is ESP32, send commands via serial and exit early
        if self.protocol == 'ESP32':
            for i in identifiers:
                if type(i) is str:
                    i = self.positions[i]
                cmd = "SET {} {} {} {}\n".format(i, color[0], color[1], color[2])
                self.serial.write(cmd.encode())
                # minimal delay for serial transmission
                sleep(0.01)
            return
        for i in identifiers:
            if type(i) is str:
                i = self.positions[i]
            # print(str(i) + str(color))
            try:
                if i >= self.count:
                    pub.sendMessage('log', msg='[LED] Error in set pixels: index out of range')
                    print('Error in set pixels: index out of range')
                    i = self.count-1                
                self.pixels[i] = self.apply_brightness_modifier(i, color)
            except Exception as e:
                print(e)
                pub.sendMessage('log', msg='[LED] Error in set pixels: ' + str(e))
                pass
        
        self.pixels.show()
        sleep(.1)

    def apply_brightness_modifier(self, identifier, color):
        # Some neopixels do not need to be full brightness. Reduce intensity with the BRIGHTNESS_MODIFIER for each neopixel
        return (round(color[0]*self.brightness[identifier]), round(color[1]*self.brightness[identifier]), round(color[2]*self.brightness[identifier]))

    def ring(self, color):
        self.set(self.ring_eye, color)

    def flashlight(self, on):
        if on:
            self.set(self.all_eye, NeoPx.COLOR_WHITE_FULL)
            set_led_pin(True)
            self.overridden = True
        else:
            self.overridden = False
            self.set(self.all_eye, NeoPx.COLOR_OFF)
            set_led_pin(False)

    def off(self):
        if self.thread:
            pub.sendMessage('log', msg='[LED] Animation stopping')
            self.animation = False
            self.thread.animation = False
            self.thread.join()
        self.set(self.all, NeoPx.COLOR_OFF)
        sleep(.5)

    def full(self, color):
        if color in NeoPx.COLOR_MAP.keys():
            self.set(self.all, NeoPx.COLOR_MAP[color])

    def eye(self, color):
        if 'middle' not in self.positions:
            raise ValueError('Middle position not found')
        if color not in NeoPx.COLOR_MAP.keys():
            raise ValueError('Color not found')
        index = self.positions['middle']
        if (self.count < index):
            index = self.count - 1
            pub.sendMessage('log', msg='[LED] Error in set pixels: index out of range, changing to last pixel')
        if self.pixels[index] != color:
            pub.sendMessage('log', msg='[LED] Setting eye colour: ' + color)
            self.set(index, NeoPx.COLOR_MAP[color])

    def party(self):
        if self.protocol == 'ESP32':
            # For ESP32, use the RAINBOW_CYCLE animation
            self.send_animation_command('RAINBOW_CYCLE')
            return
            
        # Original party implementation for other protocols
        # self.animate(self.all, 'off', 'rainbow_cycle')
        
        for j in range(256 * 1):
            for i in range(self.count):
                self.set(i, NeoPx._wheel((int(i * 256 / self.count) + j) & 255))
            return
        print('done')

        # threading.Thread(target=self.rainbow_cycle(self.all, 'off'))
        # self.thread.start()

    def animate(self, identifiers, color, animation):
        """
        Trigger one of the LED animations
        :param identifiers: single index or array or indexes
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        :param animation: string name of animation listed in map below
        :return:
        """
        if self.animation:
            pub.sendMessage('log', msg='[LED] Animation already started. Command ignored')
            return

        pub.sendMessage('log', msg='[LED] Animation starting: ' + animation)

        # For ESP32, use the send_animation_command method
        if self.protocol == 'ESP32':
            self.send_animation_command(animation, color)
            return

        animations = {
            'spinner': self.spinner,
            'breathe': self.breathe,
            'rainbow': self.rainbow,
            'rainbow_cycle': self.rainbow_cycle
        }

        self.animation = True
        if animation in animations:
            self.thread = threading.Thread(target=animations[animation], args=(identifiers, color,))
            self.thread.start()

    def handle_animate(self, animation, color=None, color2=None, repeat=1):
        """
        Handle animation requests from pubsub
        :param animation: animation name
        :param color: optional first color
        :param color2: optional second color
        :param repeat: optional repeat count (1-10)
        """
        if self.protocol == 'ESP32':
            self.send_animation_command(animation, color, color2, repeat)
        else:
            # Fall back to standard animation system
            color_val = color if color else NeoPx.COLOR_RED
            self.animate(self.all, color_val, animation.lower())

    def send_animation_command(self, animation, color=None, color2=None, repeat=1):
        """
        Send animation command to ESP32
        :param animation: animation name
        :param color: optional first color (string or RGB tuple)
        :param color2: optional second color (string or RGB tuple)
        :param repeat: optional repeat count (1-10)
        """
        if self.protocol != 'ESP32':
            return
        
        # Ensure repeat is within bounds
        repeat = max(1, min(10, int(repeat)))
        
        # Convert colors to Arduino format
        color_str = self.color_to_arduino_format(color) if color else ""
        color2_str = self.color_to_arduino_format(color2) if color2 else ""
        
        # Build command
        cmd = f"ANIMATE {animation} {color_str} {color2_str} {repeat}\n"
        
        # Log and send command
        pub.sendMessage('log', msg=f'[LED] Sending animation command: {cmd.strip()}')
        self.serial.write(cmd.encode())
        sleep(0.1)  # Brief pause to ensure command is processed

    # Animation methods for ESP32 protocol
    def rainbow_esp32(self, repeat=1):
        """Trigger rainbow animation on ESP32"""
        self.send_animation_command('RAINBOW', repeat=repeat)
    
    def rainbow_cycle_esp32(self, repeat=1):
        """Trigger rainbow cycle animation on ESP32"""
        self.send_animation_command('RAINBOW_CYCLE', repeat=repeat)
    
    def spinner_esp32(self, color='RED', repeat=1):
        """Trigger spinner animation on ESP32"""
        self.send_animation_command('SPINNER', color, repeat=repeat)
    
    def breathe_esp32(self, color='RED', repeat=1):
        """Trigger breathing animation on ESP32"""
        self.send_animation_command('BREATHE', color, repeat=repeat)
    
    def meteor_esp32(self, color='WHITE', repeat=1):
        """Trigger meteor rain animation on ESP32"""
        self.send_animation_command('METEOR', color, repeat=repeat)
    
    def fire_esp32(self, repeat=1):
        """Trigger fire animation on ESP32"""
        self.send_animation_command('FIRE', repeat=repeat)
    
    def comet_esp32(self, color='CYAN', repeat=1):
        """Trigger comet animation on ESP32"""
        self.send_animation_command('COMET', color, repeat=repeat)
    
    def wave_esp32(self, repeat=1):
        """Trigger wave animation on ESP32"""
        self.send_animation_command('WAVE', repeat=repeat)
    
    def pulse_esp32(self, color='MAGENTA', repeat=1):
        """Trigger pulse animation on ESP32"""
        self.send_animation_command('PULSE', color, repeat=repeat)
    
    def twinkle_esp32(self, color='WHITE', repeat=1):
        """Trigger twinkle animation on ESP32"""
        self.send_animation_command('TWINKLE', color, repeat=repeat)
    
    def color_wipe_esp32(self, color='RED', repeat=1):
        """Trigger color wipe animation on ESP32"""
        self.send_animation_command('COLOR_WIPE', color, repeat=repeat)
    
    def random_blink_esp32(self, repeat=1):
        """Trigger random blink animation on ESP32"""
        self.send_animation_command('RANDOM_BLINK', repeat=repeat)
    
    def theater_chase_esp32(self, color='WHITE', repeat=1):
        """Trigger theater chase animation on ESP32"""
        self.send_animation_command('THEATER_CHASE', color, repeat=repeat)
    
    def snow_esp32(self, color='WHITE', repeat=1):
        """Trigger snow animation on ESP32"""
        self.send_animation_command('SNOW', color, repeat=repeat)
    
    def alternating_esp32(self, color='RED', color2='BLUE', repeat=1):
        """Trigger alternating colors animation on ESP32"""
        self.send_animation_command('ALTERNATING', color, color2, repeat)
    
    def gradient_esp32(self, repeat=1):
        """Trigger gradient animation on ESP32"""
        self.send_animation_command('GRADIENT', repeat=repeat)
    
    def bouncing_ball_esp32(self, color='RED', repeat=1):
        """Trigger bouncing ball animation on ESP32"""
        self.send_animation_command('BOUNCING_BALL', color, repeat=repeat)
    
    def running_lights_esp32(self, color='RED', repeat=1):
        """Trigger running lights animation on ESP32"""
        self.send_animation_command('RUNNING_LIGHTS', color, repeat=repeat)
    
    def stacked_bars_esp32(self, repeat=1):
        """Trigger stacked bars animation on ESP32"""
        self.send_animation_command('STACKED_BARS', repeat=repeat)

    def spinner(self, identifiers, color, index=1):
        """
        Create a spinner effect around outer LEDs of 7 LED ring.
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        :param index: current LED to change
        :return:
        """
        sleep(.3)

        self.set(range(1, 7), NeoPx.COLOR_OFF)
        self.set(index, color)

        index = (index + 1) % self.count
        # don't set the center led
        if index == 0:
            index = 1

        t = threading.currentThread()
        if getattr(t, "animation", True):
            self.spinner(identifiers, color, index)

    def breathe(self, identifiers, color):
        """
        Begin a breathing animation for whatever color has been passed in.

        Assume the max is the brightest value from the tuple.
        All values > 0 will become aligned to that max value.
        E.g. (0, 100, 255) will brighten to (0, 255, 255) and then darken to (0, 0, 0) repeatedly

        :param identifiers: pins to apply animation
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        """
        if type(color) is str:
            color = NeoPx.COLOR_MAP[color]
        t = threading.currentThread()
        if getattr(t, "animation", True):
            for dc in range(0, max(color), 1):  # Increase brightness to max of color
                self.set(identifiers, (dc if color[0] > 0 else 0, dc if color[0] > 0 else 0, dc if color[0] > 0 else 0))
                sleep(0.10)
            sleep(2)
            for dc in range(max(color), 0, -1):  # Decrease brightness to 0
                self.set(identifiers, (dc if color[0] > 0 else 0, dc if color[0] > 0 else 0, dc if color[0] > 0 else 0))
                sleep(0.10)
            sleep(2)

    @staticmethod
    def _wheel(p):
        """Generate rainbow colors across 0-255 positions."""
        # https://github.com/jgarff/rpi_ws281x/blob/master/python/examples/strandtest.py
        if p < 85:
            return (p * 3, 255 - p * 3, 0)
        elif p < 170:
            p -= 85
            return (255 - p * 3, 0, p * 3)
        else:
            p -= 170
            return (0, p * 3, 255 - p * 3)

    def rainbow(self, identifiers, color, wait_ms=20, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.count):
                self.set(i, NeoPx._wheel((i + j) & 255))
            t = threading.currentThread()
            if not getattr(t, "animation", True):
                return
            sleep(wait_ms / 1000)

    def rainbow_cycle(self, identifiers, color, wait_ms=20, iterations=5):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256 * iterations):
            for i in range(self.count):
                self.set(i, NeoPx._wheel((int(i * 256 / self.count) + j) & 255))
            t = threading.currentThread()
            if not getattr(t, "animation", True):
                return
            sleep(wait_ms / 1000)


if __name__ == '__main__':
    inst = NeoPx(12)
    inst.set(inst.all, 1)
    sleep(2)
    inst.set(inst.all, 50)
    sleep(2)
    inst.set(inst.all, 100)
    sleep(2)
    inst.set(inst.all, NeoPx.COLOR_RED)
    sleep(2)
    inst.set(inst.all, NeoPx.COLOR_GREEN)
    sleep(2)
    inst.set(inst.all, NeoPx.COLOR_BLUE)
    sleep(2)
    inst.set(inst.all, NeoPx.COLOR_OFF)
    sleep(2)
    inst.flashlight(True)
    sleep(2)
    inst.flashlight(False)