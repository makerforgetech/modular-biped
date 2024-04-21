# source modular-biped-venv/bin/activate
sudo pkill -f /home/archie/modular-biped/main.py
# sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO - is used
python3 /home/archie/modular-biped/main.py

