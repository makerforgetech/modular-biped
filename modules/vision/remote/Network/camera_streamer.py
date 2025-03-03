import cv2
import socket
import pickle
import struct
import time
import threading
from pubsub import pub

class CameraStreamer:
    def __init__(self, **kwargs):
        """
        Streams camera feed over network to a remote computer
        
        Configuration kwargs:
          - port: Port number for streaming (default: 8089)
          - camera_id: Camera device ID (default: 0)
          - quality: JPEG compression quality 0-100 (default: 90)
          - max_fps: Maximum frames per second (default: 24)
          - resolution: Tuple of (width, height) (default: (640, 480))
        """
        self.port = kwargs.get('port', 8089)
        self.camera_id = kwargs.get('camera_id', 0)
        self.quality = kwargs.get('quality', 90)
        self.max_fps = kwargs.get('max_fps', 24)
        self.resolution = kwargs.get('resolution', (640, 480))
        
        self.running = False
        self.server_socket = None
        self.client_socket = None
        self.cap = None
        
        pub.subscribe(self.stop_streaming, 'exit')
        pub.subscribe(self.start_streaming, 'camera:start_streaming')
        pub.subscribe(self.stop_streaming, 'camera:stop_streaming')
        
        # Auto-start if specified
        if kwargs.get('autostart', True):
            threading.Thread(target=self.start_streaming).start()
    
    def start_streaming(self):
        """Start the camera streaming server."""
        if self.running:
            pub.sendMessage('log', msg=f"[CameraStreamer] Already running on port {self.port}")
            return
            
        self.running = True
        pub.sendMessage('log', msg=f"[CameraStreamer] Starting camera stream on port {self.port}")
        
        # Initialize camera
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            pub.sendMessage('log', msg=f"[CameraStreamer] Error: Could not open camera {self.camera_id}")
            self.running = False
            return
            
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            pub.sendMessage('log', msg=f"[CameraStreamer] Waiting for connection on port {self.port}")
            
            # Accept connections in a separate thread
            threading.Thread(target=self._handle_connections).start()
            
        except Exception as e:
            pub.sendMessage('log', msg=f"[CameraStreamer] Socket error: {str(e)}")
            self.running = False
            self.cap.release()
    
    def _handle_connections(self):
        """Handle incoming connections and stream camera data."""
        while self.running:
            try:
                self.client_socket, addr = self.server_socket.accept()
                pub.sendMessage('log', msg=f"[CameraStreamer] Connection from {addr}")
                
                # Stream in a separate thread
                threading.Thread(target=self._stream_to_client, args=(addr,)).start()
                
            except Exception as e:
                if self.running:  # Only log if not intentionally stopped
                    pub.sendMessage('log', msg=f"[CameraStreamer] Connection error: {str(e)}")
                break
    
    def _stream_to_client(self, addr):
        """Stream video to a connected client."""
        last_frame_time = time.time()
        frame_interval = 1.0 / self.max_fps
        
        try:
            while self.running and self.client_socket:
                # Control frame rate
                current_time = time.time()
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)  # Small sleep to prevent CPU hogging
                    continue
                
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    pub.sendMessage('log', msg="[CameraStreamer] Failed to read frame")
                    break
                
                # Compress frame to JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                _, jpeg = cv2.imencode('.jpg', frame, encode_param)
                
                # Serialize frame
                data = pickle.dumps(jpeg)
                
                # Send frame size followed by frame data
                message_size = struct.pack("L", len(data))
                try:
                    self.client_socket.sendall(message_size + data)
                except:
                    pub.sendMessage('log', msg=f"[CameraStreamer] Client {addr} disconnected")
                    break
                
                last_frame_time = time.time()
                
        except Exception as e:
            pub.sendMessage('log', msg=f"[CameraStreamer] Streaming error: {str(e)}")
        
        finally:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
                pub.sendMessage('log', msg=f"[CameraStreamer] Client {addr} connection closed")
    
    def stop_streaming(self):
        """Stop the camera streaming server."""
        if not self.running:
            return
            
        self.running = False
        pub.sendMessage('log', msg="[CameraStreamer] Stopping camera stream")
        
        # Close client socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Release camera
        if self.cap and self.cap.isOpened():
            self.cap.release()
