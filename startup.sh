sudo pkill -f /home/archie/companion-robot/main.py
sudo pkill -f webserver.py
sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO @todo may not be used
sudo python3 /home/archie/companion-robot/main.py && python3 /home/archie/companion-robot/modules/webserver.py

