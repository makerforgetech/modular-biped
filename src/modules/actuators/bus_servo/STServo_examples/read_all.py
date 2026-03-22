#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
#
# Available STServo model on this example : All models using Protocol STS
# This example is tested with a STServo and an URT
#

import os
import sys

# Add parent directory to sys.path to import STservo_sdk from sibling folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
        
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from STservo_sdk import *

# Default setting
STS_ID                      = 1                 # STServo ID : 1
BAUDRATE                    = 1000000           # STServo default baudrate : 1000000
DEVICENAME                  = '/dev/ttyACM0'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
SERVO_CNT                   = 20                 # Number of servos to read      

# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = sts(portHandler)
    
# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()

# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

# Instead of a single ID, define a range to scan
STS_ID_RANGE = range(1, SERVO_CNT)  # Typical servo ID range (1-SERVO_CNT)

while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):
        break
    print("Scanning for %d servos..." % SERVO_CNT)
    for STS_ID in STS_ID_RANGE:
        sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(STS_ID)
        if sts_comm_result == COMM_SUCCESS:
            print(f"[ID:{STS_ID:03d}] PresPos:{sts_present_position} PresSpd:{sts_present_speed}")
            if sts_error != 0:
                print(packetHandler.getRxPacketError(sts_error))
    print("Scan complete.")

# Close port
portHandler.closePort()
