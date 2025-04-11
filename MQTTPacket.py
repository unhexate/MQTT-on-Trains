from utils import * 
import variableheaders

CONNECT = 1
CONNACK = 2
PUBLISH = 3
PUBACK = 4
PUBREC = 5
PUBREL = 6
PUBCOMP = 7
SUBSCRIBE = 8
SUBACK = 9
UNSUBSCRIBE = 10 
UNSUBACK = 11
PINGREQ = 12
PINGRESP = 13
DISCONNECT = 14
AUTH = 15

class FixedHeader:
    def __init__(self, packet_type: int, flags: int = 0):
        self.packet_type = packet_type
        if(packet_type == PUBLISH):
            self.flags = flags
        else:
            # raise error if flags!=0 ?
            self.flags = 0
        # remaining length can be calculated from packet itself

    def encode(self):
        encoded = (self.packet_type<<4|self.flags).to_bytes()
        return encoded;

    @classmethod
    def decode(cls, encoded: bytes):
        packet_type = encoded[0]>>4
        flags = encoded[0]&0x0f
        return FixedHeader(packet_type, flags)


class MQTTPacket:

    def __init__(self, fixed_header: FixedHeader, 
                 variable_data = None):
        self.fixed_header = fixed_header
        if(self.fixed_header.packet_type in variableheaders.variableHeaders
           and variable_data == None):
            raise ValueError("Variable data required for this packet type")
        self.variable_data = variable_data

    def encode(self):
        encoded = b""
        if(self.variable_data): 
            encoded += self.variable_data.encode()
        encoded = int_to_var_bytes(len(encoded)) + encoded
        encoded = self.fixed_header.encode() + encoded
        return encoded
    
    @classmethod
    def decode(cls, encoded:bytes):
        fixed_header = FixedHeader.decode(encoded)

        variable_data = None
        if(fixed_header.packet_type in variableheaders.variableHeaders):
            variable_data = variableheaders.variableHeaders[fixed_header.packet_type].decode(encoded)
        return MQTTPacket(fixed_header, variable_data= variable_data)
        
