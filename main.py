import os, sys
import logging
from time import sleep, time
import signal
import schedule
from pubsub import pub
from modules.config import Config
from module_loader import ModuleLoader

# Set up logging
logging.basicConfig(filename=os.path.dirname(__file__) + '/app.log', level=logging.DEBUG, format='%(levelname)s: %(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p') # this doesn't work unless it's here
from modules.logwrapper import LogWrapper

def mode():
    return Config.MODE_KEYBOARD if len(sys.argv) > 1 and sys.argv[1] == 'manual' else Config.MODE_LIVE

def main():
    print('Starting...')
    
    path = os.path.dirname(__file__)
    log = LogWrapper(path=os.path.dirname(__file__))

    # Throw exception to safely exit script when terminated
    signal.signal(signal.SIGTERM, Config.exit)
    
    # Dynamically load and initialize modules
    loader = ModuleLoader(config_folder="config")
    module_instances = loader.load_modules()

    # Add your business logic here using module_instances as needed
    # Example: module_instances[0].some_method()
    # vision = module_instances['vision']
    
    ## output all module instance keys for reference
    # print(module_instances.keys())
    # dict_keys(['ArduinoSerial', 'NeoPx', 'BrailleSpeak', 'Animate', 'Vision', 'PiTemperature', 'Servo_leg_l_hip', 'Servo_leg_l_knee', 'Servo_leg_l_ankle', 'Servo_leg_r_hip', 'Servo_leg_r_knee', 'Servo_leg_r_ankle', 'Servo_tilt', 'Servo_pan', 'Translator', 'Tracking_tracking', 'Sensor', 'Buzzer_buzzer'])

    
    # Enable translator in log wrapper
    # log.translator = module_instances['Translator'] # Set the translator for the log wrapper

    # Use braillespeak to say hi
    # pub.sendMessage('speak', msg="Hi")
    
    # Play happy birthday with buzzer
    # pub.sendMessage('play', song="happy birthday") # Also available: 'merry christmas'

    # Use animate to nod head
    # pub.sendMessage('animate', action='head_nod')
    
    # Check temperature of Raspberry Pi
    # pub.subscribe(self.handleTemp, 'temperature') # handleTemp should accept 'value' as a parameter
    
    # Move pi servo
    # pub.sendMessage('piservo:move', percentage=50)
    
    # Move servo
    # pub.sendMessage('servo:<identifier>:mv', percentage=50) # e.g. servo:pan:mv
    # pub.sendMessage('servo:<identifier>:mvabs', percentage=50) # Absolute position. e.g. servo:pan:mvabs



    # Start loops or other tasks
    pub.sendMessage('log', msg="[Main] Loop started")

    second_loop = time()
    ten_second_loop = time()
    minute_loop = time()
    loop = True
    
    try:
        while loop:
            pub.sendMessage('loop')
            if time() - second_loop > 1:
                second_loop = time()
                pub.sendMessage('loop:1')
            if time() - ten_second_loop > 10:
                ten_second_loop = time()
                pub.sendMessage('loop:10')
            if time() - minute_loop > 60:
                minute_loop = time()
                pub.sendMessage('loop:60')
                schedule.run_pending()

    except Exception as ex:
        logging.error(f"Exception: {ex}", exc_info=True)
        loop = False

    finally:
        pub.sendMessage("exit")
        pub.sendMessage("log", msg="[Main] loop ended")

if __name__ == '__main__':
    main()
