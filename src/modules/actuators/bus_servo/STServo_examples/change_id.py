#!/usr/bin/env python
#
# *********     Change Servo ID Example      *********
#
# Works for both STS (ST3215) and SCSCL (SC09) servos.
# Requires each servo to be connected individually.
# RUN THIS BEFORE USING THE SERVOS IN ANY OTHER EXAMPLE!
#

import sys
import os

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import tty, termios
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
from STservo_sdk import *

# User config
SERVO_TYPE = input("Enter servo type (STS for ST3215, SCSCL for SC09): ").strip().upper()
SERVO_ID = int(input("Enter current servo ID (1-253): "))
BAUDRATE = 1000000
DEVICENAME = '/dev/ttyACM0'  # Change as needed

# Initialize PortHandler
portHandler = PortHandler(DEVICENAME)

# Select correct packet handler
if SERVO_TYPE == "STS":
    packetHandler = sts(portHandler)
    ID_ADDR = 5
elif SERVO_TYPE == "SCSCL":
    packetHandler = scscl(portHandler)
    ID_ADDR = 5
else:
    print("Unknown servo type.")
    sys.exit(1)

# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    sys.exit(1)

# Set baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    portHandler.closePort()
    sys.exit(1)

while True:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):
        break

    # Read present position/speed (optional, for feedback)
    try:
        if SERVO_TYPE == "STS":
            pos, spd, comm_result, err = packetHandler.ReadPosSpeed(SERVO_ID)
        else:
            pos, spd, comm_result, err = packetHandler.ReadPosSpeed(SERVO_ID)
        if comm_result == COMM_SUCCESS:
            print(f"[ID:{SERVO_ID:03d}] PresPos:{pos} PresSpd:{spd}")
        else:
            print(packetHandler.getTxRxResult(comm_result))
        if err != 0:
            print(packetHandler.getRxPacketError(err))
    except Exception as e:
        print(f"Could not read servo: {e}")

    # Get new ID
    try:
        new_id = int(input("Enter new ID (1-253): "))
    except Exception:
        print("Invalid input.")
        continue
    if new_id < 1 or new_id > 253:
        print("Invalid ID. Please enter a value between 1 and 253.")
        continue

    # Unlock EEPROM
    unlock_result, unlock_error = packetHandler.unLockEprom(SERVO_ID)
    if unlock_result != COMM_SUCCESS or unlock_error != 0:
        print("Failed to unlock EEPROM: %s %s" % (
            packetHandler.getTxRxResult(unlock_result),
            packetHandler.getRxPacketError(unlock_error)
        ))
        continue

    # Write new ID
    write_result, write_error = packetHandler.write1ByteTxRx(SERVO_ID, ID_ADDR, new_id)
    if write_result != COMM_SUCCESS or write_error != 0:
        print("Failed to change ID: %s %s" % (
            packetHandler.getTxRxResult(write_result),
            packetHandler.getRxPacketError(write_error)
        ))
        continue

    # Lock EEPROM
    lock_result, lock_error = packetHandler.LockEprom(new_id)
    if lock_result != COMM_SUCCESS or lock_error != 0:
        print("Failed to lock EEPROM: %s %s" % (
            packetHandler.getTxRxResult(lock_result),
            packetHandler.getRxPacketError(lock_error)
        ))
        continue

    print(f"{SERVO_TYPE} servo ID changed successfully to {new_id}")
    SERVO_ID = new_id

portHandler.closePort()
