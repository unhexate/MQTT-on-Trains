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
            connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
            client_socket.sendall(connack_packet.encode())
            client_socket.close()

            # Clean up any existing state for this client
            self.client_sockets.pop(client_id)
            self.client_locks.pop(client_id)
            for topic in self.client_subs[client_id]:
                self.topics[topic].discard(client_id)
            self.client_subs[client_id].discard(client_id)
            return
        
        # Send successful CONNACK
        connack_fixed_header = FixedHeader(CONNACK)
        connack_var_header = ConnackVariableHeader(0, 0x00)         # 0x00: Connection Accepted
        connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
        client_socket.send(connack_packet.encode())
        print(f'Connected to {client_id}')

        # Start listening for incoming packets from this client
        self.__recv_packets(client_socket, conn_packet.variable_data.keep_alive, client_id)


    # Loop to receive packets from client
    def __recv_packets(self, client_socket, keep_alive: int, client_id: str):

        last_packet_time = time.time()

        while True:
            data = recv_fixed_header(client_socket)
            
            # Check for keep_alive timeout
            if(time.time()-last_packet_time > keep_alive*1.5):
                client_socket.close()
                self.client_sockets.pop(client_id)
                self.client_locks.pop(client_id)
                for topic in self.client_subs[client_id]:
                    self.topics[topic].discard(client_id)
                self.client_subs[client_id].discard(client_id)
                print(f"Timeout {client_id}")
                return
            
            if(data):
                last_packet_time = time.time()
                encoded_recv_packet,packet_len = data
                encoded_recv_packet += client_socket.recv(packet_len)
                recv_packet = MQTTPacket.decode(encoded_recv_packet)

                # Handle packet types
                if(recv_packet.fixed_header.packet_type == CONNECT):
                    # Invalid repeat connect
                    print(f"Repeat connect from {client_id}")
                    connack_fixed_header = FixedHeader(CONNACK)
                    connack_var_header = ConnackVariableHeader(0, 0x82)
                    connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
                    client_socket.sendall(connack_packet.encode())
                    client_socket.close()
                    self.client_sockets.pop(client_id)
                    self.client_locks.pop(client_id)
                    for topic in self.client_subs[client_id]:
                        self.topics[topic].discard(client_id)
                    self.client_subs[client_id].discard(client_id)
                    return

                elif(recv_packet.fixed_header.packet_type == PUBLISH):
                    publishthread = threading.Thread(target = self.__handle_publish, args=(recv_packet, client_socket, client_id))
                    publishthread.start()

                elif(recv_packet.fixed_header.packet_type == PUBACK):
                    self.__handle_ack(recv_packet, client_id)

                elif(recv_packet.fixed_header.packet_type == SUBSCRIBE):
                    self.__handle_subscribe(recv_packet, client_socket, client_id)

                elif(recv_packet.fixed_header.packet_type == DISCONNECT):
                    client_socket.close()
                    self.client_sockets.pop(client_id)
                    self.client_locks.pop(client_id)
                    for topic in self.client_subs[client_id]:
                        self.topics[topic].discard(client_id)
                    self.client_subs[client_id].discard(client_id)
                    return
    

    # Handles incoming PUBLISH messages and forwards to subscribers
    def __handle_publish(self, recv_packet: MQTTPacket, client_socket: socket.socket, src_client_id: str):

        encoded_recv_packet = recv_packet.encode()

        if self.verbosity > 0: print("Received publish packet from", src_client_id)
        if self.verbosity > 0: print(encoded_recv_packet.hex(' '))
        if self.verbosity > 0: print(recv_packet.variable_data.payload)

        QoS = (recv_packet.fixed_header.flags & 0b0110) >> 1         # Extract QoS

        # If QoS 1, send PUBACK to publisher
        if(QoS == 1):
            print(recv_packet.variable_data.packet_id)
            puback_fixed_header = FixedHeader(PUBACK)
            puback_variable_header = PubackVariableHeader(recv_packet.variable_data.packet_id, 0x00)
            puback_packet = MQTTPacket(puback_fixed_header, puback_variable_header)
            client_socket.sendall(puback_packet.encode())

        # Generate list of all topic filters
        topic_filter = recv_packet.variable_data.topic_name.split('/')
        topic_names = ["/".join(topic_filter[:i])+"/#" for i in range(1,len(topic_filter))]
        topic_names.extend([recv_packet.variable_data.topic_name, "#"])

        packet_id = recv_packet.variable_data.packet_id

        # Forward to all subscribers
        for topic_name in topic_names:
            if(self.topics.get(topic_name)):
                for client_id in self.topics[topic_name]:
                    if(client_id != src_client_id):
                        with self.client_locks[client_id]:    # Thread-safe send
                            self.client_sockets[client_id].sendall(encoded_recv_packet)
                            if(QoS == 1): 
                                self.waiting_clients.setdefault(packet_id, set()).add(client_id)

        # Wait for PUBACKs from all clients
        if(QoS == 1):
            while(len(self.waiting_clients[packet_id])):
                pass

    
    # Handle PUBACK from subscriber
    def __handle_ack(self, recv_packet: MQTTPacket, src_client_id: str):
        packet_id = recv_packet.variable_data.packet_id
        if(packet_id in self.waiting_clients):
            self.waiting_clients[packet_id].remove(src_client_id)
        if(len(self.waiting_clients[packet_id]) == 0):
            self.waiting_clients.pop(packet_id)
        

    # Handle SUBSCRIBE requests
    def __handle_subscribe(self, recv_packet: MQTTPacket, client_socket: socket.socket, src_client_id: str):
        if self.verbosity > 0: print("Received subscribe packet from", src_client_id)

        for topic in recv_packet.variable_data.topics:
            self.client_subs[src_client_id].add(topic[0])
            if(topic[0] not in self.topics):
                self.topics[topic[0]] = set()
            self.topics[topic[0]].add(src_client_id)    

        # Send SUBACK to client
        suback_fixed_header = FixedHeader(SUBACK)
        suback_variable_header = SubackVariableHeader(recv_packet.variable_data.packet_id, 0x00)
        suback_packet = MQTTPacket(suback_fixed_header, suback_variable_header)
        client_socket.sendall(suback_packet.encode())


# Entry point
if(__name__ == "__main__"):

    if len(sys.argv) != 2:
        print("Usage: python broker.py <BrokerIP>")
        sys.exit(1)

    mqttb = Broker(sys.argv[1])  # Create broker with given IP
    mqttb.loop()                 # Start broker loop
