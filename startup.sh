PATH="/home/pi/really-useful-robot/main.py" # Set path as appropriate
sudo pkill -f $PATH
sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO @todo may not be used
sudo python3 $PATH
