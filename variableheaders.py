from utils import *

# NOTE: Variable headers also contain payload, I found it easier to use flags this way

__all__ = [
    "ConnectVariableHeader",
    "ConnackVariableHeader",
    "PublishVariableHeader",
    "PubackVariableHeader",
    "PubrecVariableHeader",
    "PubrelVariableHeader",
    "PubcompVariableHeader",
    "SubscribeVariableHeader",
    "SubackVariableHeader",
    "UnsubscribeVariableHeader",
    "UnsubackVariableHeader",
    "DisconnectVariableHeader",
    "AuthVariableHeader",
]

def removeFixedHeader(encoded: bytes):
    encoded=encoded[1:]
    remaining_len = var_bytes_to_int(encoded)
    encoded = encoded[remaining_len.bit_length()//7+1:]
    return encoded

class ConnectVariableHeader:

    def __init__(self, client_id: str, keep_alive: int = 0, flags: int = 0):
        assert not (flags&1) # check that reserved is 0
        self.flags = flags
        self.keep_alive = keep_alive
        # self.properties = properties
        self.client_id = client_id

    def encode(self):
        encoded = b'\x00\x04MQTT' # protocol MQTT
        encoded += b'\x05' # version 5
        encoded += self.flags.to_bytes(1)
        encoded += self.keep_alive.to_bytes(2)
        #TODO Add properties support
        encoded += int_to_var_bytes(0) #assume no properties for now

        encoded += str_to_bytes(self.client_id)
        #TODO add flags support
        return encoded
    
    @classmethod
    def decode(cls, encoded: bytes):
        encoded = removeFixedHeader(encoded) #removing fixed header
        assert encoded[:7] == b'\x00\x04MQTT\x05'
        flags = encoded[7]
        keep_alive = int.from_bytes(encoded[8:10])
        i = 10
        i+=1 # accounting for no properties
        client_id, client_id_size = bytes_to_str(encoded[i:])
        i+= client_id_size+2
        #idek how to decode properties, problem for later
        return ConnectVariableHeader(client_id, keep_alive, flags)


class ConnackVariableHeader:

    def __init__(self, flags: int, reason_code: int, username: str = "", password: str = ""):
        assert not (flags & 0xfe) #check that bits 1-7 are 0
        self.flags = flags
        assert reason_code in connack_reason_codes
        self.reason_code = reason_code
        # self.properties = properties

    def encode(self):
        encoded = self.flags.to_bytes(1)
        encoded += self.reason_code.to_bytes(1)
        #TODO Add properties support
        encoded += int_to_var_bytes(0) #assume no properties for now
        return encoded

    @classmethod
    def decode(cls, encoded: bytes):
        encoded = removeFixedHeader(encoded) #removing fixed header
        flags = encoded[0]
        reason_code = encoded[1]
        return ConnackVariableHeader(flags, reason_code)

class PublishVariableHeader:

    def __init__(self, topic_name: str, payload: str, packet_id: int | None = None):
        self.topic_name = topic_name
        self.packet_id = packet_id
        self.payload = payload
        # self.properties = properties

    def encode(self):
        encoded = str_to_bytes(self.topic_name)
        if(self.packet_id):
            encoded += self.packet_id.to_bytes(2)
        encoded += int_to_var_bytes(0) #assume no properties for now
        encoded += self.payload.encode('utf-8')
        return encoded

    @classmethod
    def decode(cls, encoded:bytes):
        var_header = removeFixedHeader(encoded) #removing fixed header
        topic_name, topic_name_size = bytes_to_str(var_header)
        i = topic_name_size+2
        packet_id = None
        if(encoded[0] & 0b0110): #QoS not 0
            packet_id = int.from_bytes(var_header[i:i+2])
            i+=2
        i+=1 # no props
        payload = var_header[i:].decode('utf-8')
        if(packet_id):
            return PublishVariableHeader(topic_name, payload, packet_id)
        return PublishVariableHeader(topic_name, payload)        


class PubackVariableHeader:

    def __init__(self, packet_id: int, reason_code: int):
        self.packet_id = packet_id
        assert reason_code in puback_reason_codes
        self.reason_code = reason_code
        # self.properties = properties
        pass

    def encode(self):
        encoded = self.packet_id.to_bytes(2)
        encoded += self.reason_code.to_bytes(1)
        encoded += (0).to_bytes(1) #assume no properties
        return encoded

    @classmethod
    def decode(cls, encoded:bytes):
        encoded = removeFixedHeader(encoded)
        packet_id = int.from_bytes(encoded[:2])
        reason_code = encoded[2]
        return PubackVariableHeader(packet_id, reason_code)


class PubrecVariableHeader:
    def __init__(self):
        # self.properties = properties
        pass


class PubrelVariableHeader:
    def __init__(self):
        # self.properties = properties
        pass


class PubcompVariableHeader:
    def __init__(self):
        # self.properties = properties
        pass


class SubscribeVariableHeader:

    def __init__(self, packet_id: int, topics: list[tuple[str, int]]):
        # self.properties = properties
        self.packet_id = packet_id
        self.topics = topics

    def encode(self):
        encoded = self.packet_id.to_bytes(2)
        encoded += int_to_var_bytes(0) #assume no properties for now
        for topic_filter, sub_options in self.topics:
            encoded += str_to_bytes(topic_filter)
            encoded += sub_options.to_bytes(1)
        return encoded
    
    @classmethod
    def decode(cls, encoded: bytes):
        encoded = removeFixedHeader(encoded) #removing fixed header
        packet_id = int.from_bytes(encoded[0:2])
        i = 3 # 2 for packet_id, 1 for no props
        topics = []
        while(i < len(encoded)):
            topic_filter, topic_len = bytes_to_str(encoded[i:])
            i += topic_len+2
            sub_options = encoded[i]
            i+=1
            topics.append((topic_filter, sub_options))
        return SubscribeVariableHeader(packet_id, topics)


class SubackVariableHeader:

    def __init__(self, packet_id: int, reason_code: int):
        # self.properties = properties
        self.packet_id = packet_id
        assert reason_code in suback_reason_codes
        self.reason_code = reason_code

    def encode(self):
        encoded = self.packet_id.to_bytes(2)
        encoded += int_to_var_bytes(0) #assume no properties for now
        encoded += self.reason_code.to_bytes(1)
        return encoded
    
    @classmethod
    def decode(cls, encoded: bytes):
        encoded = removeFixedHeader(encoded) #removing fixed header
        packet_id = int.from_bytes(encoded[0:2])
        reason_code = encoded[-1]
        return SubackVariableHeader(packet_id, reason_code)


class UnsubscribeVariableHeader:
    def __init__(self):
        # self.properties = properties
        pass


class UnsubackVariableHeader:
    def __init__(self):
        # self.properties = properties
        pass


class DisconnectVariableHeader:
    def __init__(self, reason_code: int):
        assert reason_code in disconnect_reason_codes
        self.reason_code = reason_code
        # self.properties = properties

    def encode(self):
        encoded = self.reason_code.to_bytes(1)
        #TODO Add properties support
        encoded += int_to_var_bytes(0) #assume no properties for now
        return encoded

    @classmethod
    def decode(cls, encoded: bytes):
        encoded = removeFixedHeader(encoded) #removing fixed header
        reason_code = encoded[1]
        return DisconnectVariableHeader(reason_code)


class AuthVariableHeader:
    def __init__(self):
        # self.properties = properties
        pass


variableHeaders = {
    CONNECT: ConnectVariableHeader,
    CONNACK: ConnackVariableHeader,
    PUBLISH: PublishVariableHeader,
    PUBACK: PubackVariableHeader,
    PUBREC: PubrecVariableHeader,
    PUBREL: PubrelVariableHeader,
    PUBCOMP: PubcompVariableHeader,
    SUBSCRIBE: SubscribeVariableHeader,
    SUBACK: SubackVariableHeader,
    UNSUBSCRIBE: UnsubscribeVariableHeader,
    UNSUBACK: UnsubackVariableHeader,
    DISCONNECT: DisconnectVariableHeader,
    AUTH: AuthVariableHeader,
}