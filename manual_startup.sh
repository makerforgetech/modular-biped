sudo pkill -f /home/archie/companion-robot/main.py
sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO @todo may not be used
sudo python3 /home/archie/companion-robot/main.py manual
