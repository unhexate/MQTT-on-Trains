from client import Client
import socket
import threading

TOP_CITIES = {
    "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Chennai": [13.0827, 80.2707],
    "Kolkata": [22.5726, 88.3639],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

class ControlCenter:
    def __init__(self, address: str, port: int = 8080):
        # the mqtt client which interfaces with the trains
        self.mqttclient: Client = Client("control-center")
        # train ids with their positions
        self.trains: dict[str, list[int]] = dict() 

        # ip address of the control center
        self.address: str = address 
        self.port: int = port
        # start the server for http
        self.httpserver: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.httpserver.bind((address, 8080))
        self.httpserver.listen(5)


    def __listen_for_http(self):
        while True:
            # accept the connection
            client_socket, _ = self.httpserver.accept()
            # print(self.trains)
            # print("accepted")

            # http request headers are finished by the sequence \r\n\r\n            
            buffer = bytearray(1)
            http_req_encoded = b''
            while(http_req_encoded[-4:] != b'\r\n\r\n'):
                client_socket.recv_into(buffer, 1)
                http_req_encoded+=buffer

            # decode it into a list of lines
            http_req = http_req_encoded.decode('utf-8').split('\r\n')
            # add headers to a dictionary for easy lookup
            http_req_headers = dict(map(lambda x: x.split(': '), http_req[1:-2]))
            # print(http_req)

            #check for right address and right protocol
            if(http_req_headers["Host"] == f"{self.address}:{self.port}" and
                http_req[0].split()[2] == 'HTTP/1.1'):

                # GET /locations
                # returns train ids and their locations in json format
                if(http_req[0].split()[0] == 'GET' and 
                http_req[0].split()[1] == '/locations'):
                    location_data = str(self.trains).replace(' ','').replace('\'','"')
                    http_response = "HTTP/1.1 200 OK\r\n"
                    http_response += "Content-Type: application/json\r\n"
                    http_response += f"Content-Length: {len(location_data)}\r\n"
                    http_response += "\r\n"
                    http_response += location_data
                    client_socket.sendall(http_response.encode('utf-8'))

                else:
                    html_data="<h1>this page does not exist</h1>"
                    http_response = "HTTP/1.1 404 Not Found\r\n"
                    http_response += "Content-Type: text/html\r\n"
                    http_response += f"Content-Length: {len(html_data)}\r\n"
                    http_response += "\r\n"
                    http_response += html_data
                    client_socket.sendall(http_response.encode('utf-8'))

    def __on_mqtt_msg(self,msg):
        try:
            command = msg.split(',')
            if(command[0] == "hello"):
                self.trains[command[1]] = [command[2], command[3]]
            elif(command[0] == "location"):
                if(command[1] in self.trains):
                    self.trains[command[1]] = [command[2], command[3]]
                else:
                    print(f'invalid train: {command[1]}')
        except Exception as e:
            print("Error:", msg)
            

    def connect(self, broker: str, port: int, keep_alive: int = 10):
        self.mqttclient.connect(broker, port, keep_alive)
        self.mqttclient.loop()
        self.mqttclient.subscribe(f"trains/#")


    def start(self):
        self.mqttclient.on_message = self.__on_mqtt_msg
        http_listen_thread = threading.Thread(target = self.__listen_for_http)
        http_listen_thread.start()