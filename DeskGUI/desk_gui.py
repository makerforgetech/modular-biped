import sys
import cv2
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from pubsub import pub
import requests

class DeskGUI(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        """
        DeskGUI displays three camera feeds, a log area, and an I/O panel for LLM interaction.
        
        Configuration kwargs:
          - ollama_url: URL of the LLM (Ollama) API (e.g., "http://localhost:5000/api")
        """
        super(DeskGUI, self).__init__()
        self.setWindowTitle("Robot Desk GUI")
        self.resize(1200, 800)
        
        self.ollama_url = kwargs.get('ollama_url', 'http://localhost:5000/api')

        # Set up the main layout.
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QGridLayout(self.central_widget)

        # Create labels for three camera feeds.
        self.camera_labels = []
        for i in range(3):
            label = QtWidgets.QLabel()
            label.setFixedSize(320, 240)
            label.setStyleSheet("background-color: black;")
            self.camera_labels.append(label)
            self.layout.addWidget(label, 0, i)

        # Log display area.
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text, 1, 0, 1, 3)

        # I/O panel for LLM interaction.
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

        # Start video capture for three cameras.
        self.captures = []
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if not cap.isOpened():
                self.log(f"Camera {i} could not be opened.")
            self.captures.append(cap)

        # Use QTimer to update camera frames.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # ~33 FPS

        # Subscribe to log and LLM response messages.
        pub.subscribe(self.update_log, 'log')
        pub.subscribe(self.display_llm_response, 'llm_response')

    def update_frames(self):
        """Grab frames from each camera and display them."""
        for idx, cap in enumerate(self.captures):
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Convert color for display.
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
                self.log(f"Camera {idx} is not opened.")

    def send_to_llm(self):
        """Send input text to the LLM API."""
        input_text = self.io_input.text().strip()
        if input_text:
            self.log(f"Sending to LLM: {input_text}")
            threading.Thread(target=self.llm_request, args=(input_text,)).start()

    def llm_request(self, input_text):
        """Make an HTTP POST request to the LLM API."""
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
        """Display LLM response in the log and output panels."""
        self.log(f"Received LLM response: {response_text}")
        self.io_output.append(response_text)

    def update_log(self, msg):
        self.log(msg)

    def log(self, message):
        self.log_text.append(message)

    def closeEvent(self, event):
        # Release camera resources.
        for cap in self.captures:
            cap.release()
        event.accept()

def launch_gui(**kwargs):
    """
    Launches the DeskGUI. This function can be called via the dynamic module loader,
    or directly when running the code on the laptop.
    """
    app = QtWidgets.QApplication(sys.argv)
    gui = DeskGUI(**kwargs)
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    # Example configuration for standalone launch.
    config = {
        'ollama_url': 'http://localhost:5000/api'
    }
    launch_gui(**config)
