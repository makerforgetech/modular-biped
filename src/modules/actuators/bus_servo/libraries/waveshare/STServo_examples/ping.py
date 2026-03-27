#!/usr/bin/env python
#
# *********     Ping Example      *********
#
#
# Available STServo model on this example : All models using Protocol STS
# This example is tested with a STServo and an URT
#

import sys
import os

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

sys.path.append("..")
from STservo_sdk import *                   # Uses STServo SDK library

# Default setting
STS_ID                  = 1                 # STServo ID : 1
BAUDRATE                = 1000000           # STServo default baudrate : 1000000
DEVICENAME              = '/dev/ttyACM0'    # Check which port is being used on your controller
                                            # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

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

# Try to ping the STServo
# Get STServo model number
sts_model_number, sts_comm_result, sts_error = packetHandler.ping(STS_ID)
if sts_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(sts_comm_result))
else:
    print("[ID:%03d] ping Succeeded. STServo model number : %d" % (STS_ID, sts_model_number))
if sts_error != 0:
    print("%s" % packetHandler.getRxPacketError(sts_error))

# Close port
portHandler.closePort()
