# INSTALL DEPENDENCIES FOR SPEECH RECOGNITION
sudo apt-get install libpulse-dev
apt-get install swig
python3 -m pip install --upgrade pip setuptools wheel
pip3 install --upgrade pocketsphinx
pip3 install SpeechRecognition
sudo apt-get install python-pyaudio python3-pyaudio
sudo apt install bluealsa

# google speech
apt-get install flac

# CHIRP
sudo apt-get install python3-dev python3-setuptools portaudio19-dev libffi-dev libsndfile1

# NeoPixels
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
sudo python3 -m pip install --force-reinstall adafruit-blinka

# OpenCV
sudo apt-get install libatlas-base-dev

# INSTALL ALL PYTHON DEPENDENCIES
sudo python3 -m pip install -r requirements.txt
sudo pip3 install -r requirements.txt

# Activate other scripts
chmod 777 startup.sh
chmod 777 manual_startup.sh
chmod 777 stop.sh

# Snowboy hotword
npm install --save snowboy