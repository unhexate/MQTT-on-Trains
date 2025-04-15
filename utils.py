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

def int_to_var_bytes(x: int):
    if(x==0): return (0).to_bytes()
    encoded = b''
    encoded_byte = b''
    while(x > 0):
        encoded_byte = x%128
        x//=128
        if(x > 0):
            encoded_byte = encoded_byte|128
        encoded+=encoded_byte.to_bytes()
    return encoded

def var_bytes_to_int(encoded: bytes):
    if(encoded == b'\x00'): return 0
    decoded = 0; i=0
    while encoded[i]&128:
        decoded = (encoded[i]-128)<<7*i|decoded
        i+=1
    decoded = (encoded[i])<<7*i|decoded
    return decoded

def str_to_bytes(x: str):
    return len(x).to_bytes(2) + x.encode('utf-8')
def bytes_to_str(encoded: bytes):
    utflen = int.from_bytes(encoded[0:2])
    return encoded[2:2+utflen].decode(), utflen

connack_reason_codes = {
    0x00: "Success",
    0x80: "Unspecified error",
    0x81: "Malformed Packet",
    0x82: "Protocol Error",
    0x83: "Implementation specific error",
    0x84: "Unsupported Protocol Version",
    0x85: "Client Identifier not valid",
    0x86: "Bad User Name or Password",
    0x87: "Not authorized",
    0x88: "Server unavailable",
    0x89: "Server busy",
    0x8A: "Banned",
    0x8C: "Bad authentication method",
    0x90: "Topic Name invalid",
    0x95: "Packet too large",
    0x97: "Quota exceeded",
    0x99: "Payload format invalid",
    0x9A: "Retain not supported",
    0x9B: "QoS not supported",
    0x9C: "Use another server",
    0x9D: "Server moved",
    0x9F: "Connection rate exceeded"
}

suback_reason_codes = {
    0x00: "Granted QoS 0",
    0x01: "Granted QoS 1",
    0x02: "Granted QoS 2",
    0x80: "Unspecified error",
    0x83: "Implementation specific error",
    0x87: "Not authorized",
    0x8F: "Topic Filter invalid",
    0x91: "Packet Identifier in use",
    0x97: "Quota exceeded",
    0x9E: "Shared Subscriptions not supported",
    0xA1: "Subscription Identifiers not supported",
    0xA2: "Wildcard Subscriptions not supported"
}

disconnect_reason_codes = {
    0x00: "Normal disconnection",
    0x04: "Disconnect with Will Message",
    0x80: "Unspecified error",
    0x81: "Malformed Packet",
    0x82: "Protocol Error",
    0x83: "Implementation specific error",
    0x87: "Not authorized",
    0x89: "Server busy",
    0x8B: "Server shutting down",
    0x8D: "Keep Alive timeout",
    0x8E: "Session taken over",
    0x8F: "Topic Filter invalid",
    0x90: "Topic Name invalid",
    0x93: "Receive Maximum exceeded",
    0x94: "Topic Alias invalid",
    0x95: "Packet too large",
    0x96: "Message rate too high",
    0x97: "Quota exceeded",
    0x98: "Administrative action",
    0x99: "Payload format invalid",
    0x9A: "Retain not supported",
    0x9B: "QoS not supported",
    0x9C: "Use another server",
    0x9D: "Server moved",
    0x9E: "Shared Subscriptions not supported",
    0x9F: "Connection rate exceeded",
    0xA0: "Maximum connect time",
    0xA1: "Subscription Identifiers not supported",
    0xA2: "Wildcard Subscriptions not supported"
}
