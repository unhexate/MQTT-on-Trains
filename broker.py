# Importing necessary modules
import socket, threading, time
from MQTTPacket import FixedHeader, MQTTPacket       # Custom classes for MQTT packets
from variableheaders import *                        # Importing various MQTT variable header classes
from utils import *                                  # Importing utility functions
import sys                                           # For accessing command-line arguments

# Function to receive fixed header and remaining length from socket
def recv_fixed_header(conn: socket.socket):
    encoded = conn.recv(2)                           # Receive first 2 bytes (may include remaining length partially)
    if(encoded):
        if(encoded == b'\x00'): return 0             # Check for invalid/empty packet
        decoded_len = 0; i=1                         # Initialize decoded length and shift count
        while encoded[-1]&128:                       # While the most significant bit (MSB) is 1 (more bytes to read)
            decoded_len = (encoded[-1]-128)<<7*i|decoded_len
            encoded += conn.recv(1)                  # Keep receiving until remaining length is fully read
            i+=1
        decoded_len = (encoded[-1])<<7*i|decoded_len
        return encoded, decoded_len                  # Return fixed header and decoded length


# MQTT Broker class
class Broker:

    def __init__(self, broker_ip: str):
        # Create and configure server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((broker_ip, 1883))  # Bind broker to port 1883 (MQTT standard)
        self.server_socket.listen(5)                # Start listening for incoming connections

        # Client data tracking
        self.client_sockets = dict()                # Maps client_id -> socket
        self.client_subs = dict()                   # Maps client_id -> set of subscribed topics
        self.topics = dict()                        # Maps topic -> set of client_ids subscribed
        self.client_locks = dict()                  # Locks for thread-safe communication with clients
        self.verbosity = 0                          # Verbosity flag for debugging

        self.waiting_clients: dict[int, set[str]] = dict()  # Maps packet_id -> set of clients awaiting PUBACK


    # Function to accept and listen for incoming client connections
    def __listen_for_clients(self):
        while True:
            client_socket, _ = self.server_socket.accept()         # Accept connection
            encoded_packet, packet_len = recv_fixed_header(client_socket)
            encoded_packet += client_socket.recv(packet_len)       # Receive full packet
            recv_packet = MQTTPacket.decode(encoded_packet)        # Decode the received MQTT packet

            # Validate it's a CONNECT packet
            assert recv_packet.encode() == encoded_packet
            if(recv_packet.fixed_header.packet_type == CONNECT):
                thread = threading.Thread(target = self.__handle_connect, args=(recv_packet, client_socket))
                thread.start()                                     # Handle each client in a new thread


    # Start broker's main loop
    def loop(self, verbosity = 0):
        self.verbosity = verbosity
        wait_for_client_thread = threading.Thread(target=self.__listen_for_clients)
        wait_for_client_thread.start()


    # Handle a client's CONNECT request
    def __handle_connect(self, conn_packet: MQTTPacket, client_socket: socket.socket):
        client_id = conn_packet.variable_data.client_id

        # If client is new
        if(client_id not in self.client_sockets):
            self.client_sockets[client_id] = client_socket
            self.client_subs[client_id] = set()
            self.client_locks[client_id] = threading.Lock()
        else:
            # Duplicate connect: send error CONNACK and disconnect
            print(f'Repeat connect for {client_id}')
            connack_fixed_header = FixedHeader(CONNACK)
            connack_var_header = ConnackVariableHeader(0, 0x82)     # 0x82: Identifier Rejected
            connack_packet = MQTTPacket(connack_fixed_header, connack_var
