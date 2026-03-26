#!/usr/bin/env python
#
# *********     Sync Read and Sync Write Example      *********
#
#
# Available STServo model on this example : All models using Protocol STS
# This example is tested with a STServo and an URT
#

import sys
import os
import time

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

# Control table address

# Default setting
BAUDRATE                    = 1000000           # STServo default baudrate : 1000000
DEVICENAME                  = 'COM11'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

STS_MINIMUM_POSITION_VALUE  = 0             # SCServo will rotate between this value
STS_MAXIMUM_POSITION_VALUE  = 4095
STS_MOVING_SPEED            = 2400          # SCServo moving speed
STS_MOVING_ACC              = 50            # SCServo moving acc

index = 0
sts_goal_position = [STS_MINIMUM_POSITION_VALUE, STS_MAXIMUM_POSITION_VALUE]         # Goal position

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

groupSyncRead = GroupSyncRead(packetHandler, STS_PRESENT_POSITION_L, 11)

while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):
        break

    for sts_id in range(1, 11):
        # Add SCServo#1~10 goal position\moving speed\moving accc value to the Syncwrite parameter storage
        sts_addparam_result = packetHandler.SyncWritePosEx(sts_id, sts_goal_position[index], STS_MOVING_SPEED, STS_MOVING_ACC)
        if sts_addparam_result != True:
            print("[ID:%03d] groupSyncWrite addparam failed" % sts_id)

    # Syncwrite goal position
    sts_comm_result = packetHandler.groupSyncWrite.txPacket()
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))

    # Clear syncwrite parameter storage
    packetHandler.groupSyncWrite.clearParam()
    time.sleep(0.002) #wait for servo status moving=1
    while 1:
        # Add parameter storage for STServo#1~10 present position value
        for sts_id in range(1, 11):
            sts_addparam_result = groupSyncRead.addParam(scs_id)
            if sts_addparam_result != True:
                print("[ID:%03d] groupSyncRead addparam failed" % sts_id)

        sts_comm_result = groupSyncRead.txRxPacket()
        if sts_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(sts_comm_result))

        sts_last_moving = 0;
        for sts_id in range(1, 11):
            # Check if groupsyncread data of STServo#1~10 is available
            sts_data_result, sts_error = groupSyncRead.isAvailable(sts_id, STS_PRESENT_POSITION_L, 11)
            if sts_data_result == True:
                # Get STServo#scs_id present position moving value
                sts_present_position = groupSyncRead.getData(sts_id, STS_PRESENT_POSITION_L, 2)
                sts_present_speed = groupSyncRead.getData(sts_id, STS_PRESENT_SPEED_L, 2)
                sts_present_moving = groupSyncRead.getData(sts_id, STS_MOVING, 1)
                # print(scs_present_moving)
                print("[ID:%03d] PresPos:%d PresSpd:%d" % (sts_id, sts_present_position, packetHandler.sts_tohost(sts_present_speed, 15)))
                if sts_present_moving==1:
                    sts_last_moving = 1;
            else:
                print("[ID:%03d] groupSyncRead getdata failed" % sts_id)
                continue
            if sts_error:
                print(packetHandler.getRxPacketError(sts_error))
        print("---")

        # Clear syncread parameter storage
        groupSyncRead.clearParam()
        if sts_last_moving==0:
            break
    # Change goal position
    if index == 0:
        index = 1
    else:
        index = 0

# Close port
portHandler.closePort()
