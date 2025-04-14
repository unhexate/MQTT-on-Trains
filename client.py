import socket, threading, time
import random, string
from MQTTPacket import FixedHeader, MQTTPacket
from variableheaders import *
from utils import *

def recv_fixed_header(conn: socket.socket):
    encoded = conn.recv(2)
    if(encoded == b'\x00\x00'): return 0
    decoded = 0; i=1
    while encoded[-1]&128:
        decoded = (encoded[-1]-128)<<7*i|decoded
        encoded += conn.recv(1)
        i+=1
    decoded = (encoded[-1])<<7*i|decoded
    return encoded, decoded

class Client:

    def __init__(self, client_id: str = ""):
        if(client_id == ""):
            self.client_id = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(64)])
        else:
            self.client_id = client_id
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broker = ""
        self.port = 8000
        self.keep_alive = 0
        self.last_packet_time = 0
        self.packet_id = 1
        self.suback_ids = set() #empty if not waiting for suback
        self.suback_reason_code = 0

    on_connect = lambda self, flags, reason_code: None
    on_message = lambda self, msg: None


    def connect(self, broker: str, port: int, keep_alive: int):
        try:
            self.conn.close()
        except:
            pass
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((broker, port))

        connect_fixed_header = FixedHeader(CONNECT)
        connect_var_header = ConnectVariableHeader(self.client_id, keep_alive=keep_alive)
        connect_packet = MQTTPacket(connect_fixed_header, connect_var_header)
        connect_packet_encoded = connect_packet.encode()

        self.conn.sendall(connect_packet_encoded)

        connack_packet_encoded, connack_packet_len = recv_fixed_header(self.conn)
        connack_packet_encoded += self.conn.recv(connack_packet_len)
        connack_packet = MQTTPacket.decode(connack_packet_encoded)

        self.last_packet_time = time.time()
        self.broker = broker
        self.port = port
        self.keep_alive = keep_alive
        self.on_connect(connack_packet.variable_data.flags,
                        connack_packet.variable_data.reason_code)


    def loop(self):
        thread = threading.Thread(target = self.__listen)
        thread.start()

    def __listen(self):
        while True:
            data = recv_fixed_header(self.conn)

            self.last_packet_time = time.time()
            
            if(data):
                last_packet_time = time.time()
                encoded_packet,packet_len = data
                encoded_packet += self.conn.recv(packet_len)
                recv_packet = MQTTPacket.decode(encoded_packet)

                print(self.client_id, "received packet of type", recv_packet.fixed_header.packet_type)
                print(encoded_packet.hex(' '))
                print()

                if(recv_packet.fixed_header.packet_type == PUBLISH):
                    #TODO: assume QoS 0 for now
                    self.on_message(recv_packet.variable_data.payload)
                if(recv_packet.fixed_header.packet_type == SUBACK):
                    self.__handle_suback(recv_packet)


    def subscribe(self, topics: list[str, int] | list[tuple[str, int]]):
        if(time.time() - self.last_packet_time > self.keep_alive):
            #TODO: ping
            pass
        subscribe_fixed_header = FixedHeader(SUBSCRIBE)
        if(isinstance(topics, str)):
            subscribe_variable_header = SubscribeVariableHeader(self.packet_id, [(topics, 0)])
        elif(isinstance(topics, tuple) and len(topics)==1):
            subscribe_variable_header = SubscribeVariableHeader(self.packet_id, [topics])
        else:
            subscribe_variable_header = SubscribeVariableHeader(self.packet_id, topics)
        subscribe_packet = MQTTPacket(subscribe_fixed_header, subscribe_variable_header)
        subscribe_packet_encoded = subscribe_packet.encode()

        self.conn.sendall(subscribe_packet_encoded)
        print(self.client_id, "sent packet of type subscribe")
        print(subscribe_packet_encoded.hex(' '))
        print()
        
        self.suback_ids.add(self.packet_id)
        while(self.packet_id in self.suback_ids):
            pass
        self.packet_id+=1
        return self.suback_reason_code


    def __handle_suback(self, recv_packet: MQTTPacket):
        if(recv_packet.variable_data.packet_id in self.suback_ids):
            self.suback_ids.remove(recv_packet.variable_data.packet_id)

    
    def publish(self, topic_name: str, payload: str, flags: int = 0):
        if(time.time() - self.last_packet_time > self.keep_alive):
            #ping
            pass
        if((flags & 0b0110) == 0b0000): #QoS 0
            publish_fixed_header = FixedHeader(PUBLISH, flags)
            publish_variable_header = PublishVariableHeader(topic_name, payload, self.packet_id)
            publish_packet = MQTTPacket(publish_fixed_header, publish_variable_header)
            publish_packet_encoded = publish_packet.encode()
            self.conn.sendall(publish_packet_encoded)
            print(self.client_id, "sent packet of type publish")
            print(publish_packet_encoded.hex(' '))
            print()

if(__name__ == "__main__"):

    def clientA():
        def on_message(msg: str):
            print("Message from A:",msg)

        mqttca = Client("A")
        mqttca.on_message = on_message
        mqttca.connect("localhost", 1883, 10)
        mqttca.loop()
        time.sleep(1)
        mqttca.subscribe("trains/#")
        time.sleep(1)

    def clientB():
        def on_message(msg: str):
            print("Message from B:",msg)

        mqttcb = Client("B")
        mqttcb.on_message = on_message
        time.sleep(0.5)
        mqttcb.connect("localhost", 1883, 10)
        mqttcb.loop()
        time.sleep(1)
        mqttcb.publish("trains/train1", "train from mumbai")

    threadA = threading.Thread(target=clientA)
    threadB = threading.Thread(target=clientB)
    threadA.start()
    threadB.start()
