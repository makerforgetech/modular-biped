import serial
import time

arduino = serial.Serial('/dev/ttyACM0', 9600)
time.sleep(1)

while(True):
    
    
    arduino.write("20,20".encode())

    time.sleep(2)

    arduino.write("90,90".encode())

    time.sleep(2)
    
    arduino.write("180,180".encode())

    time.sleep(2)