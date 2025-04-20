import socket, threading, time
from MQTTPacket import FixedHeader, MQTTPacket
from variableheaders import *
from utils import *

def recv_fixed_header(conn: socket.socket):
    encoded = conn.recv(2)
    if(encoded):
        if(encoded == b'\x00'): return 0
        decoded_len = 0; i=1
        while encoded[-1]&128:
            decoded_len = (encoded[-1]-128)<<7*i|decoded_len
            encoded += conn.recv(1)
            i+=1
        decoded_len = (encoded[-1])<<7*i|decoded_len
        return encoded, decoded_len


class Broker:

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 1883))
        self.server_socket.listen(5)
        self.client_sockets = dict() #each client_id with socket
        self.client_subs = dict() #each client_id with set of subbed topics
        self.topics = dict() #each topic with set of subbed clients
        self.client_locks = dict() # for forwarding publish packets to the same client 
        self.verbosity = 0

        self.waiting_clients: dict[int, set[str]] = dict() #packet_id with list of waiting clients


    #this is for server socket waiting for conn
    def __listen_for_clients(self):
        while True:
            client_socket, _ = self.server_socket.accept()
            encoded_packet, packet_len = recv_fixed_header(client_socket)
            encoded_packet += client_socket.recv(packet_len)
            recv_packet = MQTTPacket.decode(encoded_packet)
            assert recv_packet.encode() == encoded_packet
            if(recv_packet.fixed_header.packet_type == CONNECT):
                thread = threading.Thread(target = self.__handle_connect, args=(recv_packet, client_socket))
                thread.start()


    def loop(self, verbosity = 0):
        self.verbosity = verbosity
        wait_for_client_thread = threading.Thread(target=self.__listen_for_clients)
        wait_for_client_thread.start()


    def __handle_connect(self, conn_packet: MQTTPacket, client_socket: socket.socket):
        client_id = conn_packet.variable_data.client_id
        if(client_id not in self.client_sockets):
            self.client_sockets[client_id] = client_socket
            self.client_subs[client_id] = set()
            self.client_locks[client_id] = threading.Lock()
        else:
            print(f'Repeat connect for {client_id}')
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
        
        connack_fixed_header = FixedHeader(CONNACK)
        connack_var_header = ConnackVariableHeader(0, 0x00)
        connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
        client_socket.send(connack_packet.encode())
        print(f'Connected to {client_id}')
        self.__recv_packets(client_socket, conn_packet.variable_data.keep_alive, conn_packet.variable_data.client_id)


    def __recv_packets(self, client_socket, keep_alive: int, client_id: str):

        last_packet_time = time.time()

        while True:
            data = recv_fixed_header(client_socket)
            if(time.time()-last_packet_time > keep_alive*1.5):
                client_socket.close()
                self.client_sockets.pop(client_id)
                self.client_lock.pop(client_id)
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
                # print()
                # print("Received packet of type", recv_packet.fixed_header.packet_type)
                # print(encoded_recv_packet.hex(' '))

                if(recv_packet.fixed_header.packet_type == CONNECT):
                    #this should just disconnect
                    print(f"Repeat connect from {client_id}")
                    connack_fixed_header = FixedHeader(CONNACK)
                    connack_var_header = ConnackVariableHeader(0, 0x82) 
                    connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
                    client_socket.sendall(connack_packet.encode())
                    client_socket.close()
                    self.client_sockets.pop(client_id)
                    self.client_lock.pop(client_id)
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
                    self.client_lock.pop(client_id)
                    for topic in self.client_subs[client_id]:
                        self.topics[topic].discard(client_id)
                    self.client_subs[client_id].discard(client_id)
                    return
    

    def __handle_publish(self, recv_packet: MQTTPacket, client_socket: socket.socket, src_client_id: str):

        #forward to all other clients who have subscribed

        encoded_recv_packet = recv_packet.encode()

        if self.verbosity > 0: print("Received publish packet from", src_client_id)
        if self.verbosity > 0: print(encoded_recv_packet.hex(' '))
        if self.verbosity > 0: print(recv_packet.variable_data.payload)

        QoS = (recv_packet.fixed_header.flags & 0b0110) >> 1

        if(QoS == 1):
            puback_fixed_header = FixedHeader(PUBACK)
            puback_variable_header = PubackVariableHeader(recv_packet.variable_data.packet_id, 0x00)
            puback_packet = MQTTPacket(puback_fixed_header, puback_variable_header)
            puback_packet_encoded = puback_packet.encode()
            client_socket.sendall(puback_packet_encoded)
            if self.verbosity > 0: print("Sending puback packet to", src_client_id)
            if self.verbosity > 0: print(puback_packet_encoded.hex(' '))

        topic_filter = recv_packet.variable_data.topic_name.split('/')
        topic_names = ["/".join(topic_filter[:i])+"/#" for i in range(1,len(topic_filter))]
        topic_names.extend([recv_packet.variable_data.topic_name, "#"])

        packet_id = recv_packet.variable_data.packet_id
        for topic_name in topic_names:
            if(self.topics.get(topic_name)):
                for client_id in self.topics[topic_name]:
                    if(client_id != src_client_id):
                        with self.client_locks[client_id]:
                            print("payload:",recv_packet.variable_data.payload)
                            if self.verbosity > 0: print("Sending to", client_id)
                            self.client_sockets[client_id].sendall(encoded_recv_packet)
                            if(QoS == 1): 
                                if packet_id in self.waiting_clients:
                                    self.waiting_clients[packet_id].add(client_id)
                                else:
                                    self.waiting_clients[packet_id] = set((client_id,))

        if(QoS == 1):
            while(len(self.waiting_clients[packet_id])):
                pass

    
    def __handle_ack(self, recv_packet: MQTTPacket, src_client_id: str):
        packet_id = recv_packet.variable_data.packet_id
        if(packet_id in self.waiting_clients):
            self.waiting_clients[packet_id].remove(src_client_id)
        if(len(self.waiting_clients) == 0):
            self.waiting_clients.pop(packet_id)
        

    def __handle_subscribe(self, recv_packet: MQTTPacket, client_socket: socket.socket, src_client_id: str):

        #TODO: sub options

        if self.verbosity > 0: print("Received subscribe packet from", src_client_id)

        for topic in recv_packet.variable_data.topics:
            self.client_subs[src_client_id].add(topic[0])
            if(not self.topics.get(topic[0])):
                self.topics[topic[0]] = set()
            self.topics[topic[0]].add(src_client_id)    

        suback_fixed_header = FixedHeader(SUBACK)
        suback_variable_header = SubackVariableHeader(recv_packet.variable_data.packet_id, 0x00)
        suback_packet = MQTTPacket(suback_fixed_header, suback_variable_header)
        suback_packet_encoded = suback_packet.encode()
        client_socket.sendall(suback_packet_encoded)

        if self.verbosity > 0: print("Sent suback packet")
        if self.verbosity > 0: print(suback_packet_encoded.hex(' '))


        

if(__name__ == "__main__"):
    mqttb = Broker()
    mqttb.loop()