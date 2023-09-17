sudo pkill -f /home/SentryRoot/SentryBOT/main.py
sudo modprobe bcm2835-v4l2 #kamera aktifleştirme
sudo pigpiod  #GPIO @todo kullanılamaz
python3 /home/SentryRoot/SentryBOT/main.py preview
