import sys
import cv2
import threading
import socket
import struct
import pickle
import numpy as np
import json
import time
import face_recognition
from PyQt5 import QtWidgets, QtGui, QtCore
from pubsub import pub
import requests
import os

class RemoteVideoStream:
    def __init__(self, robot_ip, port=8089):
        self.robot_ip = robot_ip
        self.port = port
        self.socket = None
        self.running = False
        self.frame = None
        self.lock = threading.Lock()
        
    def start(self):
        self.running = True
        threading.Thread(target=self._stream_receiver).start()
        return self
        
    def _stream_receiver(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.robot_ip, self.port))
            
            data = b""
            payload_size = struct.calcsize("L")
            
            while self.running:
                # Receive message size
                while len(data) < payload_size:
                    packet = self.socket.recv(4096)
                    if not packet:
                        break
                    data += packet
                    
                if not self.running:
                    break
                    
                # Extract message size
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("L", packed_msg_size)[0]
                
                # Receive message data
                while len(data) < msg_size:
                    packet = self.socket.recv(4096)
                    if not packet:
                        break
                    data += packet
                    
                # Extract frame
                frame_data = data[:msg_size]
                data = data[msg_size:]
                
                # Decode frame
                frame = pickle.loads(frame_data)
                jpeg_frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                # Store frame safely
                with self.lock:
                    self.frame = jpeg_frame
                    
        except Exception as e:
            print(f"Stream error: {e}")
            
        finally:
            self.stop()
                
    def read(self):
        with self.lock:
            return self.frame
            
    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None


class CommandSender:
    def __init__(self, robot_ip, port=8090):
        self.robot_ip = robot_ip
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self):
        if self.connected:
            return True
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.robot_ip, self.port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False
            
    def send_command(self, command_type, params=None):
        if params is None:
            params = {}
            
        if not self.connected and not self.connect():
            return False
            
        try:
            command = {
                'command': command_type,
                'params': params
            }
            
            self.socket.sendall(json.dumps(command).encode('utf-8'))
            
            # Get acknowledgment
            response = self.socket.recv(1024).decode('utf-8')
            return json.loads(response)
        except Exception as e:
            print(f"Command sending error: {e}")
            self.connected = False
            return False
            
    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False


class FaceDetector:
    def __init__(self, encodings_file=None):
        # Load cascade classifier
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Face recognition data
        self.data = None
        if encodings_file and os.path.exists(encodings_file):
            with open(encodings_file, 'rb') as f:
                self.data = pickle.loads(f.read())
    
    def detect_faces(self, frame):
        if frame is None:
            return [], []
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Recognize faces if we have encodings data
        names = []
        if self.data is not None and len(faces) > 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            for (x, y, w, h) in faces:
                # Extract face ROI
                face_encoding = face_recognition.face_encodings(rgb, [(y, x+w, y+h, x)])[0]
                
                # Compare with known encodings
                matches = face_recognition.compare_faces(self.data["encodings"], face_encoding)
                name = "Unknown"
                
                if True in matches:
                    matched_idxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}
                    
                    for i in matched_idxs:
                        name = self.data["names"][i]
                        counts[name] = counts.get(name, 0) + 1
                        
                    name = max(counts, key=counts.get)
                
                names.append(name)
        
        return faces, names
        
    def process_frame(self, frame):
        if frame is None:
            return frame
            
        # Detect faces
        faces, names = self.detect_faces(frame)
        
        # Draw rectangles and labels
        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            if i < len(names):
                name = names[i]
                y_pos = y - 10 if y - 10 > 10 else y + h + 10
                cv2.putText(frame, name, (x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
        return frame, faces, names


class MotionDetector:
    def __init__(self):
        self.static_back = None
        self.motion_threshold = 30
        self.min_area = 10000
        
    def detect_motion(self, frame):
        if frame is None:
            return frame, []
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize static background on first run
        if self.static_back is None:
            self.static_back = gray
            return frame, []
            
        # Calculate difference between current frame and background
        diff_frame = cv2.absdiff(self.static_back, gray)
        thresh_frame = cv2.threshold(diff_frame, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter by area and draw rectangles
        motion_areas = []
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue
                
            (x, y, w, h) = cv2.boundingRect(contour)
            motion_areas.append((x, y, w, h))
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            
        # Slowly update background model for changes
        if len(motion_areas) == 0 and self.static_back is not None:
            alpha = 0.05  # Learning rate
            self.static_back = cv2.addWeighted(gray, alpha, self.static_back, 1-alpha, 0)
            
        return frame, motion_areas


class Tracking:
    TRACKING_THRESHOLD = 30
    TRACKING_MOVE_PERCENT = 10
    
    def __init__(self, command_sender=None):
        self.command_sender = command_sender
        self.active = False
        self.screen_dimensions = (640, 480)
        
    def set_active(self, active):
        self.active = active
        
    def set_dimensions(self, dimensions):
        self.screen_dimensions = dimensions
        
    def track_object(self, object_rect):
        if not self.active or not self.command_sender or not object_rect:
            return False
            
        # Extract object coordinates
        x, y, w, h = object_rect
        
        # Calculate center points
        screen_w, screen_h = self.screen_dimensions
        screen_cx = screen_w / 2
        screen_cy = screen_h / 2
        
        obj_cx = x + (w / 2)
        obj_cy = y + (h / 2)
        
        # Calculate movement needed for pan (horizontal)
        if abs(screen_cx - obj_cx) > self.TRACKING_THRESHOLD:
            x_move = round((screen_cx - obj_cx) / self.TRACKING_MOVE_PERCENT)
            self.command_sender.send_command('servo_move', {
                'identifier': 'pan',
                'percentage': x_move
            })
            
        # Calculate movement needed for tilt (vertical)
        if abs(screen_cy - obj_cy) > self.TRACKING_THRESHOLD:
            y_move = round((obj_cy - screen_cy) / self.TRACKING_MOVE_PERCENT)
            self.command_sender.send_command('servo_move', {
                'identifier': 'tilt',
                'percentage': -y_move
            })
            
        return True


class DeskGUI(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super(DeskGUI, self).__init__()
        self.setWindowTitle("Robot Control GUI")
        self.resize(1200, 800)
        
        # Configuration
        self.robot_ip = kwargs.get('robot_ip', '192.168.1.10')
        self.video_port = kwargs.get('video_port', 8089)
        self.command_port = kwargs.get('command_port', 8090)
        self.ollama_url = kwargs.get('ollama_url', 'http://localhost:5000/api')
        self.encodings_file = kwargs.get('encodings_file', 'encodings.pickle')
        
        # Initialize components
        self.video_stream = None
        self.command_sender = CommandSender(self.robot_ip, self.command_port)
        self.face_detector = FaceDetector(self.encodings_file)
        self.motion_detector = MotionDetector()
        self.tracking = Tracking(self.command_sender)
        
        # State variables
        self.processing_mode = 'none'  # 'none', 'face', 'motion'
        self.tracking_enabled = False
        self.stream_connected = False
        self.largest_face = None
        
        # Create the main layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QGridLayout(self.central_widget)
        
        # Create video display
        self.video_label = QtWidgets.QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.video_label, 0, 0, 1, 2)
        
        # Control panel
        self.create_control_panel()
        self.layout.addWidget(self.control_panel, 0, 2, 1, 1)
        
        # Log display
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text, 1, 0, 1, 3)
        
        # I/O panel
        self.io_input = QtWidgets.QLineEdit()
        self.io_output = QtWidgets.QTextEdit()
        self.io_output.setReadOnly(True)
        self.send_button = QtWidgets.QPushButton("Send to LLM")
        io_layout = QtWidgets.QVBoxLayout()
        io_layout.addWidget(QtWidgets.QLabel("Input:"))
        io_layout.addWidget(self.io_input)
        io_layout.addWidget(self.send_button)
        io_layout.addWidget(QtWidgets.QLabel("Output:"))
        io_layout.addWidget(self.io_output)
        self.layout.addLayout(io_layout, 2, 0, 1, 3)
        
        self.send_button.clicked.connect(self.send_to_llm)
        
        # Use QTimer to update video frame
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33 FPS
        
        # Subscribe to log and LLM response events
        pub.subscribe(self.update_log, 'log')
        pub.subscribe(self.display_llm_response, 'llm_response')
        
    def create_control_panel(self):
        """Create the control panel with all robot control buttons."""
        self.control_panel = QtWidgets.QGroupBox("Robot Controls")
        layout = QtWidgets.QVBoxLayout()
        
        # Connection controls
        connection_group = QtWidgets.QGroupBox("Connection")
        connection_layout = QtWidgets.QHBoxLayout()
        
        self.ip_input = QtWidgets.QLineEdit(self.robot_ip)
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        connection_layout.addWidget(QtWidgets.QLabel("Robot IP:"))
        connection_layout.addWidget(self.ip_input)
        connection_layout.addWidget(self.connect_button)
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Vision processing controls
        vision_group = QtWidgets.QGroupBox("Vision Processing")
        vision_layout = QtWidgets.QVBoxLayout()
        
        self.face_detection_radio = QtWidgets.QRadioButton("Face Detection")
        self.motion_detection_radio = QtWidgets.QRadioButton("Motion Detection")
        self.no_processing_radio = QtWidgets.QRadioButton("No Processing")
        self.no_processing_radio.setChecked(True)
        
        self.tracking_checkbox = QtWidgets.QCheckBox("Enable Tracking")
        
        vision_layout.addWidget(self.face_detection_radio)
        vision_layout.addWidget(self.motion_detection_radio)
        vision_layout.addWidget(self.no_processing_radio)
        vision_layout.addWidget(self.tracking_checkbox)
        
        vision_group.setLayout(vision_layout)
        layout.addWidget(vision_group)
        
        # Robot movement controls
        movement_group = QtWidgets.QGroupBox("Robot Movement")
        movement_layout = QtWidgets.QGridLayout()
        
        self.btn_up = QtWidgets.QPushButton("▲")
        self.btn_down = QtWidgets.QPushButton("▼")
        self.btn_left = QtWidgets.QPushButton("◄")
        self.btn_right = QtWidgets.QPushButton("►")
        self.btn_center = QtWidgets.QPushButton("■")
        
        # Connect movement buttons to actions
        self.btn_up.clicked.connect(lambda: self.send_servo_command('tilt', 10))
        self.btn_down.clicked.connect(lambda: self.send_servo_command('tilt', -10))
        self.btn_left.clicked.connect(lambda: self.send_servo_command('pan', 10))
        self.btn_right.clicked.connect(lambda: self.send_servo_command('pan', -10))
        self.btn_center.clicked.connect(self.center_servos)
        
        # Add buttons to grid
        movement_layout.addWidget(self.btn_up, 0, 1)
        movement_layout.addWidget(self.btn_left, 1, 0)
        movement_layout.addWidget(self.btn_center, 1, 1)
        movement_layout.addWidget(self.btn_right, 1, 2)
        movement_layout.addWidget(self.btn_down, 2, 1)
        
        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)
        
        # Animation controls
        animation_group = QtWidgets.QGroupBox("Animations")
        animation_layout = QtWidgets.QVBoxLayout()
        
        self.animation_combo = QtWidgets.QComboBox()
        self.animation_combo.addItems(["head_nod", "head_shake", "look_around", "wake_up", "sleep"])
        self.btn_animate = QtWidgets.QPushButton("Run Animation")
        self.btn_animate.clicked.connect(self.run_animation)
        
        animation_layout.addWidget(self.animation_combo)
        animation_layout.addWidget(self.btn_animate)
        
        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)
        
        # Speech controls
        speech_group = QtWidgets.QGroupBox("Speech")
        speech_layout = QtWidgets.QVBoxLayout()
        
        self.speech_input = QtWidgets.QLineEdit()
        self.btn_speak = QtWidgets.QPushButton("Speak")
        self.btn_speak.clicked.connect(self.send_speech)
        
        speech_layout.addWidget(self.speech_input)
        speech_layout.addWidget(self.btn_speak)
        
        speech_group.setLayout(speech_layout)
        layout.addWidget(speech_group)
        
        # Buzzer controls
        buzzer_group = QtWidgets.QGroupBox("Buzzer")
        buzzer_layout = QtWidgets.QVBoxLayout()
        
        self.buzzer_combo = QtWidgets.QComboBox()
        self.buzzer_combo.addItems(["happy birthday", "merry christmas", "beep"])
        self.btn_buzzer = QtWidgets.QPushButton("Play Sound")
        self.btn_buzzer.clicked.connect(self.play_buzzer)
        
        buzzer_layout.addWidget(self.buzzer_combo)
        buzzer_layout.addWidget(self.btn_buzzer)
        
        buzzer_group.setLayout(buzzer_layout)
        layout.addWidget(buzzer_group)
        
        # Model training button
        self.train_button = QtWidgets.QPushButton("Train Face Recognition Model")
        self.train_button.clicked.connect(self.train_model)
        layout.addWidget(self.train_button)
        
        self.control_panel.setLayout(layout)
        
        # Connect signals
        self.face_detection_radio.toggled.connect(self.update_processing_mode)
        self.motion_detection_radio.toggled.connect(self.update_processing_mode)
        self.no_processing_radio.toggled.connect(self.update_processing_mode)
        self.tracking_checkbox.toggled.connect(self.update_tracking)
        
    def toggle_connection(self):
        """Toggle the connection to the robot."""
        if self.stream_connected:
            self.disconnect_from_robot()
        else:
            self.connect_to_robot()
            
    def connect_to_robot(self):
        """Connect to the robot's video stream and command server."""
        self.robot_ip = self.ip_input.text().strip()
        self.video_stream = RemoteVideoStream(self.robot_ip, self.video_port).start()
        self.stream_connected = True
        self.log("Connected to robot.")
        
    def disconnect_from_robot(self):
        """Disconnect from the robot's video stream and command server."""
        if self.video_stream:
            self.video_stream.stop()
            self.video_stream = None
        self.stream_connected = False
        self.log("Disconnected from robot.")
        
    def update_processing_mode(self):
        """Update the image processing mode based on the selected radio button."""
        if self.face_detection_radio.isChecked():
            self.processing_mode = 'face'
        elif self.motion_detection_radio.isChecked():
            self.processing_mode = 'motion'
        else:
            self.processing_mode = 'none'
        self.log(f"Processing mode set to {self.processing_mode}.")
        
    def update_tracking(self):
        """Update the tracking state based on the checkbox."""
        self.tracking_enabled = self.tracking_checkbox.isChecked()
        self.tracking.set_active(self.tracking_enabled)
        self.log(f"Tracking {'enabled' if self.tracking_enabled else 'disabled'}.")
        
    def update_frame(self):
        """Update the video frame display."""
        if not self.video_stream:
            return
            
        frame = self.video_stream.read()
        if frame is None:
            return
            
        if self.processing_mode == 'face':
            frame, faces, names = self.face_detector.process_frame(frame)
            if self.tracking_enabled and faces:
                self.largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                self.tracking.track_object(self.largest_face)
        elif self.processing_mode == 'motion':
            frame, motion_areas = self.motion_detector.detect_motion(frame)
            if self.tracking_enabled and motion_areas:
                self.tracking.track_object(motion_areas[0])
                
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        qimg = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), QtCore.Qt.KeepAspectRatio))
        
    def send_to_llm(self):
        """Send text input to the LLM API."""
        input_text = self.io_input.text().strip()
        if input_text:
            self.log(f"Sending to LLM: {input_text}")
            threading.Thread(target=self.llm_request, args=(input_text,)).start()
            
    def llm_request(self, input_text):
        """Send an HTTP request to the LLM API."""
        payload = {'input': input_text}
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                output = data.get('output', '')
                pub.sendMessage('llm_response', response_text=output)
            else:
                self.log(f"LLM API error: {response.status_code}")
        except Exception as e:
            self.log(f"Error contacting LLM API: {e}")
            
    def display_llm_response(self, response_text):
        """Display the response received from the LLM."""
        self.log(f"Received LLM response: {response_text}")
        self.io_output.append(response_text)
        
    def update_log(self, msg):
        """Update the log display."""
        self.log(msg)
        
    def log(self, message):
        """Append a message to the log display."""
        self.log_text.append(message)
        
    def closeEvent(self, event):
        """Release resources on application close."""
        self.disconnect_from_robot()
        event.accept()
        
    def send_servo_command(self, servo_id, percentage):
        """Send a servo movement command to the robot."""
        if not self.stream_connected:
            self.log("Not connected to robot.")
            return
            
        self.log(f"Moving {servo_id} servo by {percentage}%")
        self.command_sender.send_command('servo_move', {
            'identifier': servo_id,
            'percentage': percentage,
            'absolute': False
        })
        
    def center_servos(self):
        """Center both pan and tilt servos."""
        if not self.stream_connected:
            self.log("Not connected to robot.")
            return
            
        self.log("Centering servos.")
        self.command_sender.send_command('servo_move', {
            'identifier': 'pan',
            'percentage': 0,
            'absolute': True
        })
        self.command_sender.send_command('servo_move', {
            'identifier': 'tilt',
            'percentage': 0,
            'absolute': True
        })
        
    def run_animation(self):
        """Run the selected animation on the robot."""
        if not self.stream_connected:
            self.log("Not connected to robot.")
            return
            
        animation = self.animation_combo.currentText()
        self.log(f"Running animation: {animation}")
        self.command_sender.send_command('animate', {
            'action': animation
        })
        
    def send_speech(self):
        """Send speech text to be spoken by the robot."""
        if not self.stream_connected:
            self.log("Not connected to robot.")
            return
            
        message = self.speech_input.text().strip()
        if not message:
            return
            
        self.log(f"Sending speech: {message}")
        self.command_sender.send_command('speak', {
            'message': message
        })
        
    def play_buzzer(self):
        """Play the selected sound on the robot's buzzer."""
        if not self.stream_connected:
            self.log("Not connected to robot.")
            return
            
        song = self.buzzer_combo.currentText()
        self.log(f"Playing sound: {song}")
        self.command_sender.send_command('buzzer', {
            'song': song
        })
        
    def train_model(self):
        """Start training the face recognition model."""
        self.log("Training face recognition model. This may take some time...")
        
        # Run in a thread to avoid blocking the UI
        threading.Thread(target=self._train_model_thread).start()
        
    def _train_model_thread(self):
        """Background thread for model training."""
        try:
            # Import the TrainModel class
            from modules.vision.remote.train_model import TrainModel
            
            # Create and run the trainer
            trainer = TrainModel(dataset='dataset', output=self.encodings_file)
            trainer.train()
            
            # Reload the face detector with new model
            self.face_detector = FaceDetector(self.encodings_file)
            
            self.log("Model training completed successfully.")
        except Exception as e:
            self.log(f"Error training model: {e}")


def launch_gui(**kwargs):
    """Launch the GUI application. Handles errors gracefully."""
    try:
        app = QtWidgets.QApplication(sys.argv)
        gui = DeskGUI(**kwargs)
        gui.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error launching GUI: {e}")


if __name__ == '__main__':
    config = {
        'robot_ip': '192.168.1.10',
        'video_port': 8089,
        'command_port': 8090,
        'ollama_url': 'http://localhost:5000/api',
        'encodings_file': 'encodings.pickle'
    }
    launch_gui(**config)
