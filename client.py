import socket, threading, time
import random, string
from MQTTPacket import FixedHeader, MQTTPacket
from variableheaders import *
from utils import *

def recv_fixed_header(conn: socket.socket):
    encoded = conn.recv(2)
    if(encoded == b'\x00\x00'): return 0
    multiplier = 1
    value = encoded[-1]&127
    while(encoded[-1] & 128 != 0):
        encoded += conn.recv(1)
        value += (encoded[-1] & 127) * multiplier
        multiplier *= 128
    return encoded, value

class Client:
    '''
    MQTT client class

    client.connect(broker, port, keep_alive): connects to a broker

    client.loop(): starts listening for packets
    
    client.subscribe(topics): subscribe to a topic or list of topics
    
    client.publish(topic_name, payload, flags): publish to a topic
    '''

    def __init__(self, client_id: str = ""):
        if(client_id == ""):
            self.client_id = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(64)])
        else:
            self.client_id = client_id
        self.conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected: bool = False
        self.broker: str = ""
        self.port: int = 8000
        self.keep_alive: int = 0
        self.last_packet_time: float = 0.0
        self.packet_id: int = 1
        self.waiting_acks : dict[int, bytes] = dict() #packet_id with waiting acks
        self.ack_reason_code: int = 0

        self.on_connect = lambda flags, reason_code: None
        self.on_message = lambda msg: None


    def connect(self, broker: str, port: int, keep_alive: int = 0):
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
        self.connected = True
        self.broker = broker
        self.port = port
        self.keep_alive = keep_alive

        self.on_connect(connack_packet.variable_data.flags,
                        connack_packet.variable_data.reason_code)


    def loop(self):
        thread = threading.Thread(target = self.__listen)
        thread.start()

        if(len(self.waiting_acks)):
            for packet in self.waiting_acks.values():
                self.conn.sendall(packet)

    def __listen(self):
        while True:
            try:
                data = recv_fixed_header(self.conn)
            except Exception as e:
                if(not self.connected):
                    return
                else:
                    raise e
            self.last_packet_time = time.time()
            
            if(data):
                last_packet_time = time.time()
                encoded_packet,packet_len = data
                encoded_packet += self.conn.recv(packet_len)
                recv_packet = MQTTPacket.decode(encoded_packet)

                # print(self.client_id, "received packet of type", recv_packet.fixed_header.packet_type)
                # print(encoded_packet.hex(' '))
                # print()

                if(recv_packet.fixed_header.packet_type == PUBLISH):
                    #TODO: assume QoS 0 for now
                    self.on_message(recv_packet.variable_data.payload)
                if(recv_packet.fixed_header.packet_type == SUBACK):
                    self.__handle_ack(recv_packet)
                if(recv_packet.fixed_header.packet_type == PUBACK):
                    self.__handle_ack(recv_packet)


    def subscribe(self, topics: str | tuple[str, int] | list[tuple[str, int]]):
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
        # print(self.client_id, "sent packet of type subscribe")
        # print(subscribe_packet_encoded.hex(' '))
        # print()
        
        cur_packet_id = self.packet_id
        self.waiting_acks[cur_packet_id] = subscribe_packet_encoded
        self.packet_id+=1
        while(cur_packet_id in self.waiting_acks):
            pass
        return self.ack_reason_code


    def __handle_ack(self, recv_packet: MQTTPacket):
        if(recv_packet.variable_data.packet_id in self.waiting_acks):
            #if this was async, maybe there'd be a producer consumer model
            #since simple sync model, just set a shared variable for reason code
            self.ack_reason_code = recv_packet.variable_data.reason_code
            self.waiting_acks.pop(recv_packet.variable_data.packet_id)

    
    def publish(self, topic_name: str, payload: str, flags: int = 0):
        if(time.time() - self.last_packet_time > self.keep_alive):
            #ping
            pass

        if((flags & 0b0110) == 0b0000): #QoS 0
            publish_fixed_header = FixedHeader(PUBLISH, flags)
            publish_variable_header = PublishVariableHeader(topic_name, payload)
            publish_packet = MQTTPacket(publish_fixed_header, publish_variable_header)
            publish_packet_encoded = publish_packet.encode()
            self.conn.sendall(publish_packet_encoded)
            # print(self.client_id, "sent packet of type publish")
            # print(publish_packet_encoded.hex(' '))
            # print()
        
        elif((flags & 0b0110) == 0b0010): #QoS 1
            publish_fixed_header = FixedHeader(PUBLISH, flags)
            publish_variable_header = PublishVariableHeader(topic_name, payload, self.packet_id)
            publish_packet = MQTTPacket(publish_fixed_header, publish_variable_header)
            publish_packet_encoded = publish_packet.encode()
            self.conn.sendall(publish_packet_encoded)
            # print(self.client_id, "sent packet of type publish")
            # print(publish_packet_encoded.hex(' '))
            # print()

            cur_packet_id = self.packet_id
            self.waiting_acks[cur_packet_id] = publish_packet_encoded
            self.packet_id+=1
            while(cur_packet_id in self.waiting_acks):
                pass
            return self.ack_reason_code

    def disconnect(self):
        self.connected = False
        disconnect_fixed_header = FixedHeader(DISCONNECT)
        disconnect_variable_header = DisconnectVariableHeader(0x00)
        disconnect_packet = MQTTPacket(disconnect_fixed_header, disconnect_variable_header)
        disconnect_packet_encoded = disconnect_packet.encode()
        self.conn.sendall(disconnect_packet_encoded)
        self.conn.close()

if(__name__ == "__main__"):

    def clientA():
        def on_message(msg: str):
            print("Message from A:",msg)

        mqttca = Client("A")
        mqttca.on_message = on_message
        mqttca.connect("localhost", 1883, 10)
        mqttca.loop()
        mqttca.subscribe("trains/#")
        time.sleep(2)
        mqttca.publish("trains/train1", "go to chennai", 0b0010)
        time.sleep(0.5)
        mqttca.publish("trains/train2", "go to mumbai", 0b0010)
        mqttca.disconnect()

    def clientB():
        def on_message(msg: str):
            print("Message from B:",msg)

        mqttcb = Client("B")
        mqttcb.on_message = on_message
        time.sleep(0.5)
        mqttcb.connect("localhost", 1883, 5)
        mqttcb.loop()
        mqttcb.subscribe("trains/train1")
        time.sleep(1)
        mqttcb.publish("trains/train1", "train from mumbai")
        time.sleep(5)
        mqttcb.disconnect()

    def clientC():
        def on_message(msg: str):
            print("Message from C:",msg)

        mqttcc = Client("C")
        mqttcc.on_message = on_message
        time.sleep(1)
        mqttcc.connect("localhost", 1883, 10)
        mqttcc.loop()
        mqttcc.subscribe("trains/train2")
        time.sleep(1)
        mqttcc.publish("trains/train2", "train from chennai")
        time.sleep(5)
        mqttcc.disconnect()

    threadA = threading.Thread(target=clientA)
    threadB = threading.Thread(target=clientB)
    threadC = threading.Thread(target=clientC)
    threadA.start()
    threadB.start()
    threadC.start()
