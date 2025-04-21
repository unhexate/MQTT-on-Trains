# Import utility functions from utils module (like int_to_var_bytes)
from utils import * 

# Import dictionary that maps packet types to their variable header structures
import variableheaders

# MQTT Packet Type Constants as per MQTT protocol specification
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

# Class representing the fixed header of an MQTT packet
class FixedHeader:
    def __init__(self, packet_type: int, flags: int = 0):
        self.packet_type = packet_type              # Store packet type (e.g., CONNECT, PUBLISH)
        
        if(packet_type == PUBLISH):
            self.flags = flags                      # PUBLISH packets can have flags like DUP, QoS, RETAIN
        else:
            self.flags = 0                          # For all other packet types, flags are defaulted to 0

        # Remaining length will be calculated later during encoding (not stored here)

    def encode(self):
        # Combine packet type (high nibble) and flags (low nibble), then convert to single byte
        encoded = (self.packet_type << 4 | self.flags).to_bytes(1, byteorder='big')
        return encoded                              # Return the fixed header byte

    @classmethod
    def decode(cls, encoded: bytes):
        # Extract packet type by right-shifting 4 bits
        packet_type = encoded[0] >> 4

        # Extract flags by masking lower 4 bits
        flags = encoded[0] & 0x0f

        # Return a FixedHeader object with extracted values
        return FixedHeader(packet_type, flags)

# Class representing the entire MQTT packet including fixed and variable parts
class MQTTPacket:

    def __init__(self, fixed_header: FixedHeader, variable_data = None):
        self.fixed_header = fixed_header                  # Store fixed header

        # Check if packet type requires variable header, and it hasn't been provided
        if(self.fixed_header.packet_type in variableheaders.variableHeaders
           and variable_data == None):
            raise ValueError("Variable data required for this packet type")  # Raise error

        self.variable_data = variable_data                # Store variable header / payload (if any)

    def encode(self):
        encoded = b""                                     # Initialize empty byte string for encoded output

        if(self.variable_data): 
            encoded += self.variable_data.encode()        # Encode variable header and payload

        # Prepend remaining length using MQTT variable-length encoding
        encoded = int_to_var_bytes(len(encoded)) + encoded

        # Prepend fixed header at the beginning
        encoded = self.fixed_header.encode() + encoded

        return encoded                                     # Return full encoded packet
    
    @classmethod
    def decode(cls, encoded: bytes):
        # Decode fixed header from the first byte
        fixed_header = FixedHeader.decode(encoded)

        variable_data = None

        # If packet type requires variable header, decode it using corresponding decode class
        if(fixed_header.packet_type in variableheaders.variableHeaders):
            variable_data = variableheaders.variableHeaders[fixed_header.packet_type].decode(encoded)

        # Return full decoded MQTTPacket object
        return MQTTPacket(fixed_header, variable_data= variable_data)
