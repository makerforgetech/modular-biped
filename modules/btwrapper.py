import bluetooth


class BTWrapper:
    def __init__(self, **kwargs):
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = kwargs.get('port', 1)
        self.server_socket.bind(("", port))
        self.server_socket.listen(port)
        self.client_socket, address = self.server_socket.accept()
        print("Accepted connection from ", address)

    def read(self):
        data = ""
        data = self.client_socket.recv(1024)
        print("Received: %s" % data)
        return data

    def __delete__(self, instance):
        self.client_socket.close()
        self.server_socket.close()