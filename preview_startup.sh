sudo pkill -f /home/archie/companion-robot/main.py
sudo pkill -f /home/archie/companion-robot/RFID.py
sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO @todo may not be used
sudo python3 /home/archie/companion-robot/main.py preview
sudo python2 /home/archie/companion-robot/RFID.py
