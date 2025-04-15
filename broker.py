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
        self.topics = dict() #each topic and set of subbed clients


    #this is for server socket waiting for conn
    def loop(self):
        while True:
            client_socket, _ = self.server_socket.accept()
            encoded_packet, packet_len = recv_fixed_header(client_socket)
            encoded_packet += client_socket.recv(packet_len)
            recv_packet = MQTTPacket.decode(encoded_packet)
            assert recv_packet.encode() == encoded_packet
            if(recv_packet.fixed_header.packet_type == CONNECT):
                thread = threading.Thread(target = self.__handle_connect, args=(recv_packet, client_socket))
                thread.start()

        
    def __handle_connect(self, conn_packet: MQTTPacket, client_socket):
        client_id = conn_packet.variable_data.client_id
        if(client_id not in self.client_sockets):
            self.client_sockets[client_id] = client_socket
            self.client_subs[client_id] = set()
        else:
            print("Repeat connect")
            connack_fixed_header = FixedHeader(CONNACK)
            connack_var_header = ConnackVariableHeader(0, 0x82) 
            connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
            client_socket.sendall(connack_packet.encode())
            client_socket.close()
            self.client_sockets.pop(client_id)
            for topic in self.client_subs[client_id]:
                self.topics[topic].discard(client_id)
            self.client_subs[client_id].discard(client_id)
            return

        connack_fixed_header = FixedHeader(CONNACK)
        connack_var_header = ConnackVariableHeader(0, 0x00)
        connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
        client_socket.send(connack_packet.encode())
        self.__recv_packets(client_socket, conn_packet.variable_data.keep_alive, conn_packet.variable_data.client_id)


    def __recv_packets(self, client_socket, keep_alive: int, client_id: str):

        last_packet_time = time.time()

        while True:
            data = recv_fixed_header(client_socket)
            if(time.time()-last_packet_time > keep_alive*1.5):
                client_socket.close()
                self.client_sockets.pop(client_id)
                for topic in self.client_subs[client_id]:
                    self.topics[topic].discard(client_id)
                self.client_subs[client_id].discard(client_id)
                print("Timeout")
                return
            
            if(data):
                last_packet_time = time.time()
                encoded_recv_packet,packet_len = data
                encoded_recv_packet += client_socket.recv(packet_len)
                recv_packet = MQTTPacket.decode(encoded_recv_packet)
                print("Received packet of type", recv_packet.fixed_header.packet_type)
                print(encoded_recv_packet.hex(' '))
                print()

                if(recv_packet.fixed_header.packet_type == CONNECT):
                    #this should just disconnect
                    print("Repeat connect")
                    connack_fixed_header = FixedHeader(CONNACK)
                    connack_var_header = ConnackVariableHeader(0, 0x82) 
                    connack_packet = MQTTPacket(connack_fixed_header, connack_var_header)
                    client_socket.sendall(connack_packet.encode())
                    client_socket.close()
                    self.client_sockets.pop(client_id)
                    for topic in self.client_subs[client_id]:
                        self.topics[topic].discard(client_id)
                    self.client_subs[client_id].discard(client_id)
                    return

                elif(recv_packet.fixed_header.packet_type == PUBLISH):
                    self.__handle_publish(recv_packet)

                elif(recv_packet.fixed_header.packet_type == SUBSCRIBE):
                    self.__handle_subscribe(recv_packet, client_socket, client_id)

                elif(recv_packet.fixed_header.packet_type == DISCONNECT):
                    client_socket.close()
                    self.client_sockets.pop(client_id)
                    for topic in self.client_subs[client_id]:
                        self.topics[topic].discard(client_id)
                    self.client_subs[client_id].discard(client_id)
                    return
    

    def __handle_publish(self, recv_packet):

        #forward to all other clients who have subscribed
        #TODO: assume QoS 0 for now

        encoded_recv_packet = recv_packet.encode()

        topic_filter = recv_packet.variable_data.topic_name.split('/')
        topic_names = ["/".join(topic_filter[:i])+"/#" for i in range(1,len(topic_filter))]
        topic_names.extend([recv_packet.variable_data.topic_name, "#"])
        print(topic_names)

        for topic_name in topic_names:
            if(self.topics.get(topic_name)):
                for client_id in self.topics[topic_name]:
                    print("Sending to", client_id)
                    print(encoded_recv_packet.hex(' '))
                    self.client_sockets[client_id].sendall(encoded_recv_packet)
            # else:
            #     self.topics[recv_packet.variable_data.topic_name] = set()
        

    def __handle_subscribe(self, recv_packet, client_socket, client_id):

        #TODO: sub options

        print("Received subscribe packet from", client_id)

        for topic in recv_packet.variable_data.topics:
            self.client_subs[client_id].add(topic[0])
            if(not self.topics.get(topic[0])):
                self.topics[topic[0]] = set()
            self.topics[topic[0]].add(client_id)    

        suback_fixed_header = FixedHeader(SUBACK)
        suback_variable_header = SubackVariableHeader(recv_packet.variable_data.packet_id, 0x00)
        suback_packet = MQTTPacket(suback_fixed_header, suback_variable_header)
        suback_packet_encoded = suback_packet.encode()
        client_socket.sendall(suback_packet_encoded)

        print("Sent suback packet")
        print(suback_packet_encoded.hex(' '))


        

if(__name__ == "__main__"):
    mqttb = Broker()
    mqttb.loop()