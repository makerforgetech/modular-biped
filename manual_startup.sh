sudo pkill -f /home/pi/really-useful-robot/main.py
sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO @todo may not be used
sudo python3 /home/pi/really-useful-robot/main.py manual
