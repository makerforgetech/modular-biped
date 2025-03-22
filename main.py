import os, sys
from time import sleep, time
import signal
from modules.config import Config
from module_loader import ModuleLoader

def main():
    print('Starting...')
    # Throw exception to safely exit script when terminated
    signal.signal(signal.SIGTERM, Config.exit)

    # Dynamically load and initialize modules
    loader = ModuleLoader(config_folder="config")
    module_instances = loader.load_modules()
    
    # Set messaging service for all modules
    messaging_service = module_instances['MessagingService'].messaging_service
    loader.set_messaging_service(module_instances, messaging_service)

    # Add your business logic here using module_instances as needed
    # Example: module_instances[0].some_method()
    # vision = module_instances['vision']
    
    ## output all module instance keys for reference
    # print(module_instances.keys())
    # dict_keys(['ArduinoSerial', 'NeoPx', 'BrailleSpeak', 'Animate', 'Vision', 'PiTemperature', 'Servo_leg_l_hip', 'Servo_leg_l_knee', 'Servo_leg_l_ankle', 'Servo_leg_r_hip', 'Servo_leg_r_knee', 'Servo_leg_r_ankle', 'Servo_tilt', 'Servo_pan', 'Translator', 'Tracking_tracking', 'Sensor', 'Buzzer_buzzer'])

    # Use animate to nod head
    # messaging_service.publish('animate', action='head_nod')
    # sleep(1)
    # messaging_service.publish('animate', action='head_shake')
    
    # Enable translator in log wrapper
    # log.translator = module_instances['Translator'] # Set the translator for the log wrapper

    # Use braillespeak to say hi
    # messaging_service.publish('speak', msg="Hi")
    
    # Play happy birthday with buzzer
    # messaging_service.publish('play', song="happy birthday") # Also available: 'merry christmas'
    
    # Check temperature of Raspberry Pi
    # messaging_service.subscribe('temperature', callback) # callback should accept 'value' as a parameter
    
    # Move pi servo
    # messaging_service.publish('piservo:move', angle=30)
    # messaging_service.publish('piservo:move', angle=-30)
    
    # Move servo
    # messaging_service.publish('servo:<identifier>:mv', percentage=50) # e.g. servo:pan:mv
    # messaging_service.publish('servo:<identifier>:mvabs', percentage=50) # Absolute position. e.g. servo:pan:mvabs

    # Test emotion analysis
    # messaging_service.publish('speech', text='I am so happy today!')
    
    # Test speech input
    # messaging_service.publish('speech:listen')
    
    # Start loops or other tasks
    messaging_service.publish('log', message=f"[Main] Loop started using {messaging_service.protocol} protocol")

    second_loop = time()
    ten_second_loop = time()
    minute_loop = time()
    loop = True
    
    try:
        while loop:
            messaging_service.publish('system/loop')
            if time() - second_loop > 1:
                second_loop = time()
                messaging_service.publish('system/loop/1')
            if time() - ten_second_loop > 10:
                ten_second_loop = time()
                messaging_service.publish('system/loop/10')
            if time() - minute_loop > 60:
                minute_loop = time()
                messaging_service.publish('system/loop/60')
            
            if messaging_service.protocol == 'mqtt':
                sleep(0.01) # Needed to prevent MQTT broker from jamming when system/loop is included

    except Exception as ex:
        # output exception details
        print(ex)
        messaging_service.publish('log', message="[Main] Exception occurred: " + str(ex))
        #output full details
        import traceback
        traceback.print_exc()
        loop = False

    finally:
        messaging_service.publish('system/exit')
        messaging_service.publish('log', message="[Main] Loop ended")

if __name__ == '__main__':
    main()
