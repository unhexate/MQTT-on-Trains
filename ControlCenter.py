# Import the MQTT client from a separate client.py file (assumed to be a custom wrapper)
from client import Client
# Import socket module to create HTTP server
import socket
# Import threading to run HTTP server concurrently with MQTT
import threading
# Import sys to handle command-line arguments
import sys
# Import time to timestamp the train location updates
import time

# Dictionary of top non-coastal cities with their latitude and longitude
TOP_CITIES = {
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

# Authorization token for HTTP requests
auth_key = "8194d5119dbdfaa09a45db0e3d2b53fd68a62696e1cac3579ec9991c834820f2"

# Class representing the control center system
class ControlCenter:
    def __init__(self, address: str, port: int = 8080):
        # Initialize MQTT client for train communications
        self.mqttclient: Client = Client("control-center")
        
        # Dictionary to store train ID with their current locations
        self.current_train_locations: dict[str, list[int]] = dict() 
        
        # Dictionary to store train ID with their routes (source to destination)
        self.current_train_routes: dict[str, list[str]] = dict()
        
        # List to track history of train location updates with timestamp
        self.locations: list[list[any]] = [["train_id", "pos_x", "pos_y", "time"]]

        # IP address to bind HTTP server
        self.address: str = address 
        # Port number for HTTP server
        self.port: int = port
        
        # Initialize the HTTP server socket
        self.httpserver: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow address reuse
        self.httpserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the HTTP server to the given address and port
        self.httpserver.bind((address, 8080))
        # Start listening for incoming connections (max queue = 5)
        self.httpserver.listen(5)

    # Internal method to handle incoming HTTP requests
    def __listen_for_http(self):
        while True:
            # Accept an incoming client connection
            client_socket, _ = self.httpserver.accept()

            # Initialize a buffer to receive the HTTP request
            buffer = bytearray(1)
            http_req_encoded = b''
            # Read the request byte-by-byte until the header ends with \r\n\r\n
            while(http_req_encoded[-4:] != b'\r\n\r\n'):
                client_socket.recv_into(buffer, 1)
                http_req_encoded += buffer

            # Decode the request to string and split by lines
            http_req = http_req_encoded.decode('utf-8').split('\r\n')
            # Convert HTTP headers to a dictionary
            http_req_headers = dict(map(lambda x: x.split(': '), http_req[1:-2]))

            # Validate Host and HTTP version
            if(http_req_headers["Host"] == f"{self.address}:{self.port}" and
                http_req[0].split()[2] == 'HTTP/1.1'):

                # Check if Authorization header is valid
                if(http_req_headers["Authorization"] == f"Bearer {auth_key}"):

                    # If GET /locations is requested
                    if(http_req[0].split()[0] == 'GET' and 
                    http_req[0].split()[1] == '/locations'):
                        # Prepare train location data in CSV format
                        location_data = "\n".join([",".join(map(str, row)) for row in self.locations])
                        # Compose HTTP 200 OK response
                        http_response = "HTTP/1.1 200 OK\r\n"
                        http_response += "Content-Type: text/csv\r\n"
                        http_response += f"Content-Length: {len(location_data)}\r\n"
                        http_response += "\r\n"
                        http_response += location_data
                        # Send the response
                        client_socket.sendall(http_response.encode('utf-8'))

                    # If GET /routes is requested
                    elif(http_req[0].split()[0] == 'GET' and
                    http_req[0].split()[1] == '/routes'):
                        # Prepare route data in JSON-like format
                        route_data = str(self.current_train_routes).replace('\'','"')
                        http_response = "HTTP/1.1 200 OK\r\n"
                        http_response += "Content-Type: application/json\r\n"
                        http_response += f"Content-Length: {len(route_data)}\r\n"
                        http_response += "\r\n"
                        http_response += route_data
                        client_socket.sendall(http_response.encode('utf-8'))

                    # If GET /login is requested (perhaps to validate auth)
                    elif(http_req[0].split()[0] == 'GET' and
                    http_req[0].split()[1] == '/login'):
                        http_response = "HTTP/1.1 200 OK\r\n"
                        http_response += "\r\n"
                        client_socket.sendall(http_response.encode('utf-8'))

                    # For any other endpoint, return 404 Not Found
                    else:
                        html_data="<h1>this page does not exist</h1>"
                        http_response = "HTTP/1.1 404 Not Found\r\n"
                        http_response += "Content-Type: text/html\r\n"
                        http_response += f"Content-Length: {len(html_data)}\r\n"
                        http_response += "\r\n"
                        http_response += html_data
                        client_socket.sendall(http_response.encode('utf-8'))
                else:
                    # Unauthorized request due to invalid token
                    http_response = "HTTP/1.1 401 Unauthorized\r\n"
                    http_response += "\r\n"
                    client_socket.sendall(http_response.encode('utf-8'))

    # Callback for handling incoming MQTT messages
    def __on_mqtt_msg(self, msg):
        try:
            command = msg.split(',')
            # Handle "hello" command for new train
            if(command[0] == "hello"):
                self.current_train_locations[command[1]] = [command[2], command[3]]
                self.current_train_routes[command[1]] = [command[4], command[5]]
                self.locations.append([command[1], command[2], command[3], round(time.time(), 2)])
                print(self.locations)
            # Handle location update command
            elif(command[0] == "location"):
                if(command[1] in self.current_train_locations):
                    self.current_train_locations[command[1]] = [command[2], command[3]]
                    self.locations.append([command[1], command[2], command[3], round(time.time(), 2)])
                else:
                    print(f'invalid train: {command[1]}')
            # Handle route update command
            elif(command[0] == "route"):
                self.current_train_routes[command[1]] = [command[2], command[3]]
        except Exception as e:
            print("Error:", msg)

    # Connect to MQTT broker and subscribe to train updates
    def connect(self, broker: str, port: int, keep_alive: int = 10):
        self.mqttclient.connect(broker, port, keep_alive)
        self.mqttclient.loop()
        self.mqttclient.subscribe(f"trains/#")

    # Start listening to MQTT and HTTP simultaneously
    def start(self):
        self.mqttclient.on_message = self.__on_mqtt_msg
        # Start HTTP listener on a separate thread
        http_listen_thread = threading.Thread(target=self.__listen_for_http)
        http_listen_thread.start()

# Main entry point
if __name__ == "__main__":

    # Check for required number of command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python ControlCenter.py <BrokerIP> <HTTP_IP>")
        sys.exit(1)

    # Extract MQTT broker IP and HTTP server IP
    broker_ip = sys.argv[1]
    http_ip = sys.argv[2]

    # Create and configure control center object
    control_center = ControlCenter(http_ip, 83)
    # Connect to the MQTT broker
    control_center.connect(broker_ip, 1883)
    # Start both MQTT client and HTTP server
    control_center.start()
