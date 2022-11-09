# Python 3 server http://<IP>:8080
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

ERROR_LOG = 'app.log'

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><meta http-equiv='refresh' content='5' /><head><title>Archie Log</title></head>", "utf-8"))
        # self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<h1>Log</h1>", "utf-8"))
        try:
            for line in reversed(list(open(ERROR_LOG))):
                self.wfile.write(bytes("<p>" +  line + "</p>", "utf-8"))
                # print(line.rstrip())
        except FileNotFoundError:
            self.wfile.write(bytes("<p>No log found</p>", "utf-8"))
            pass

        # with open('install-errors.txt', 'r') as file:
            # self.wfile.write(bytes("<p>" +  file.read().replace('\n', '') + "</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer(('', 8080), MyServer)
    print("Server started...")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")