import sys
import cv2
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from pubsub import pub
import requests

class DeskGUI(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super(DeskGUI, self).__init__()
        self.setWindowTitle("Robot Desk GUI")
        self.resize(1200, 800)
        self.ollama_url = kwargs.get('ollama_url', 'http://localhost:5000/api')

        # Create the main layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QGridLayout(self.central_widget)

        # Create camera labels
        self.camera_labels = []
        for i in range(3):
            label = QtWidgets.QLabel()
            label.setFixedSize(320, 240)
            label.setStyleSheet("background-color: black;")
            self.camera_labels.append(label)
            self.layout.addWidget(label, 0, i)

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

        # Image processing mode
        self.image_processing_mode = False
        self.selected_camera_index = 0

        # Add image processing controls
        self.process_button = QtWidgets.QPushButton("Toggle Image Processing")
        self.camera_selector = QtWidgets.QComboBox()
        self.camera_selector.addItems([f"Camera {i}" for i in range(3)])
        self.layout.addWidget(self.process_button, 3, 0)
        self.layout.addWidget(self.camera_selector, 3, 1)

        self.process_button.clicked.connect(self.toggle_image_processing)
        self.camera_selector.currentIndexChanged.connect(self.select_camera)

        # Initialize cameras
        self.captures = []
        self.camera_errors = [False] * 3  # Prevent duplicate error logs
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if not cap.isOpened():
                self.log_once(i, f"Camera {i} could not be opened.")
                cap = None
            self.captures.append(cap)

        # Use QTimer to update camera frames
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # ~33 FPS

        # Subscribe to log and LLM response events
        pub.subscribe(self.update_log, 'log')
        pub.subscribe(self.display_llm_response, 'llm_response')

    def toggle_image_processing(self):
        """Toggle the image processing mode."""
        self.image_processing_mode = not self.image_processing_mode
        self.log(f"Image processing mode {'enabled' if self.image_processing_mode else 'disabled'}.")

    def select_camera(self, index):
        """Select the camera for image processing."""
        self.selected_camera_index = index
        self.log(f"Selected Camera {index} for image processing.")

    def update_frames(self):
        """Capture frames from cameras and display them."""
        for idx, cap in enumerate(self.captures):
            if cap and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    if self.image_processing_mode and idx == self.selected_camera_index:
                        frame = self.process_frame(frame)
                    processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    height, width, channel = processed_frame.shape
                    bytes_per_line = 3 * width
                    qimg = QtGui.QImage(
                        processed_frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888
                    )
                    pixmap = QtGui.QPixmap.fromImage(qimg)
                    self.camera_labels[idx].setPixmap(
                        pixmap.scaled(self.camera_labels[idx].size(), QtCore.Qt.KeepAspectRatio)
                    )
            else:
                self.log_once(idx, f"Camera {idx} is not opened.")

    def process_frame(self, frame):
        """Apply image processing to the frame."""
        # Example: Convert to grayscale
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

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

    def log_once(self, camera_index, message):
        """Log an error message only once per camera."""
        if not self.camera_errors[camera_index]:
            self.log(message)
            self.camera_errors[camera_index] = True  # Mark the error as logged

    def closeEvent(self, event):
        """Release camera resources on application close."""
        for cap in self.captures:
            if cap:
                cap.release()
        event.accept()


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
        'ollama_url': 'http://localhost:5000/api'
    }
    launch_gui(**config)
