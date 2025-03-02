#!/usr/bin/env python3
"""
Launch script for the robot's camera streaming service.
This script runs on the robot to stream camera data and receive commands from DeskGUI.
"""

import os
import time
import signal
import sys
from pubsub import pub
from module_loader import ModuleLoader

def log(msg):
    """Simple log function."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def setup_exit_handler():
    """Set up signal handlers for graceful exit."""
    def exit_handler(signum, frame):
        log("Exiting on signal...")
        pub.sendMessage('exit')
        sys.exit(0)
        
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

def main():
    """Main function to run the camera streaming service."""
    log("Starting robot camera streaming service...")
    
    # Set up exit handler
    setup_exit_handler()
    
    # Subscribe to log events
    pub.subscribe(log, 'log')
    
    # Load modules from configuration
    loader = ModuleLoader(config_folder="config")
    modules = loader.load_modules()
    
    # Keep the script running until Ctrl+C
    log("Camera streaming service is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Keyboard interrupt received.")
    finally:
        pub.sendMessage('exit')
        log("Camera streaming service stopped.")

if __name__ == '__main__':
    main()
