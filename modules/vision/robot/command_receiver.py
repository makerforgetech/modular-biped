import socket
import json
import threading
import time
from pubsub import pub

class CommandReceiver:
    def __init__(self, **kwargs):
        """
        Receives commands from a remote computer to control the robot
        
        Configuration kwargs:
          - port: Port number for command server (default: 8090)
        """
        self.port = kwargs.get('port', 8090)
        self.running = False
        self.server_socket = None
        
        pub.subscribe(self.stop_receiver, 'exit')
        
        # Auto-start if specified
        if kwargs.get('autostart', True):
            threading.Thread(target=self.start_receiver).start()
    
    def start_receiver(self):
        """Start the command receiver server."""
        if self.running:
            pub.sendMessage('log', msg=f"[CommandReceiver] Already running on port {self.port}")
            return
            
        self.running = True
        pub.sendMessage('log', msg=f"[CommandReceiver] Starting command receiver on port {self.port}")
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            pub.sendMessage('log', msg=f"[CommandReceiver] Waiting for connection on port {self.port}")
            
            # Accept connections in a separate thread
            threading.Thread(target=self._handle_connections).start()
            
        except Exception as e:
            pub.sendMessage('log', msg=f"[CommandReceiver] Socket error: {str(e)}")
            self.running = False
    
    def _handle_connections(self):
        """Handle incoming connections and process commands."""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                pub.sendMessage('log', msg=f"[CommandReceiver] Connection from {addr}")
                
                # Handle client in a separate thread
                threading.Thread(target=self._handle_client, args=(client_socket, addr)).start()
                
            except Exception as e:
                if self.running:  # Only log if not intentionally stopped
                    pub.sendMessage('log', msg=f"[CommandReceiver] Connection error: {str(e)}")
                break
    
    def _handle_client(self, client_socket, addr):
        """Handle commands from a connected client."""
        buffer_size = 1024
        
        try:
            while self.running:
                # Receive data
                data = client_socket.recv(buffer_size)
                if not data:
                    pub.sendMessage('log', msg=f"[CommandReceiver] Client {addr} disconnected")
                    break
                
                # Process the command
                self._process_command(data, client_socket)
                
        except Exception as e:
            pub.sendMessage('log', msg=f"[CommandReceiver] Client handling error: {str(e)}")
        
        finally:
            client_socket.close()
    
    def _process_command(self, data, client_socket):
        """Process a received command and publish appropriate pubsub events."""
        try:
            # Parse JSON command
            command_data = json.loads(data.decode('utf-8'))
            command_type = command_data.get('command')
            params = command_data.get('params', {})
            
            pub.sendMessage('log', msg=f"[CommandReceiver] Received command: {command_type}")
            
            # Handle different command types
            if command_type == 'servo_move':
                identifier = params.get('identifier')
                percentage = params.get('percentage')
                is_absolute = params.get('absolute', False)
                
                if identifier and percentage is not None:
                    event = f'servo:{identifier}:{"mvabs" if is_absolute else "mv"}'
                    pub.sendMessage(event, percentage=percentage)
                    
            elif command_type == 'animate':
                action = params.get('action')
                if action:
                    pub.sendMessage('animate', action=action)
            
            elif command_type == 'speak':
                message = params.get('message')
                if message:
                    pub.sendMessage('speak', msg=message)
            
            elif command_type == 'buzzer':
                song = params.get('song')
                if song:
                    pub.sendMessage('play', song=song)
                    
            # Send acknowledgment
            response = {'status': 'ok', 'command': command_type}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            pub.sendMessage('log', msg=f"[CommandReceiver] Invalid JSON format")
            response = {'status': 'error', 'message': 'Invalid JSON format'}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            pub.sendMessage('log', msg=f"[CommandReceiver] Command processing error: {str(e)}")
            response = {'status': 'error', 'message': str(e)}
            try:
                client_socket.sendall(json.dumps(response).encode('utf-8'))
            except:
                pass
    
    def stop_receiver(self):
        """Stop the command receiver."""
        if not self.running:
            return
            
        self.running = False
        pub.sendMessage('log', msg="[CommandReceiver] Stopping command receiver")
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
