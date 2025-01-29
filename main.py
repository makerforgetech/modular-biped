import os, sys
from time import sleep, time
import signal
from pubsub import pub
from modules.config import Config
from module_loader import ModuleLoader

def main():
    print('Starting...')
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

    # Use animate to nod head
    # pub.sendMessage('animate', action='head_nod')
    # sleep(1)
    # pub.sendMessage('animate', action='head_shake')
    
    # Enable translator in log wrapper
    # log.translator = module_instances['Translator'] # Set the translator for the log wrapper

    # Use braillespeak to say hi
    # pub.sendMessage('speak', msg="Hi")
    
    # Play happy birthday with buzzer
    # pub.sendMessage('play', song="happy birthday") # Also available: 'merry christmas'

    
    # Check temperature of Raspberry Pi
    # pub.subscribe(self.handleTemp, 'temperature') # handleTemp should accept 'value' as a parameter
    
    # Move pi servo
    # pub.sendMessage('piservo:move', angle=30)
    # pub.sendMessage('piservo:move', angle=-30)
    
    # Move servo
    # pub.sendMessage('servo:<identifier>:mv', percentage=50) # e.g. servo:pan:mv
    # pub.sendMessage('servo:<identifier>:mvabs', percentage=50) # Absolute position. e.g. servo:pan:mvabs

    # Test emotion analysis
    # pub.sendMessage('speech', text='I am so happy today!')
    
    # Test speech input
    # pub.sendMessage('speech:listen')
    
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
                # schedule.run_pending()

    except Exception as ex:
        print(f"Exception: {ex}")
        loop = False

    finally:
        pub.sendMessage("exit")
        pub.sendMessage("log", msg="[Main] loop ended")

if __name__ == '__main__':
    main()
