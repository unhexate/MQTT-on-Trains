import socket
import random, string
from MQTTPacket import FixedHeader, MQTTPacket
from variableheaders import *
from utils import *

def recv_fixed_header(conn: socket.socket):
    encoded = conn.recv(2)
    if(encoded == b'\x00'): return 0
    decoded = 0; i=1
    while encoded[i]&128:
        decoded = (encoded[i]-128)<<7*i|decoded
        encoded += conn.recv(1)
        i+=1
    decoded = (encoded[i])<<7*i|decoded
    return encoded, decoded

class Client:

    def __init__(self, client_id: str = ""):
        if(client_id == ""):
            self.client_id = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(128)])
        else:
            self.client_id = client_id
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, broker: str, port: int, keep_alive: int):
        connect_fixed_header = FixedHeader(CONNECT)
        connect_var_header = ConnectVariableHeader(self.client_id, keep_alive=keep_alive)
        connect_packet = MQTTPacket(connect_fixed_header, connect_var_header)
        connect_packet_encoded = connect_packet.encode()
        self.conn.connect((broker, port))
        self.conn.sendall(connect_packet_encoded)

        connack_packet_encoded, connack_packet_len = recv_fixed_header(self.conn)
        connack_packet_encoded += self.conn.recv(connack_packet_len)
        connack_packet = MQTTPacket.decode(connack_packet_encoded)


mqttc = Client("a")
mqttc.connect("hello", 1883, 60)