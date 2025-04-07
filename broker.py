import socket

"""server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.listen()
client_socket,client_address = server_socket.accept()
"""

def recv_fixed_header(conn: socket.socket):
    encoded = conn.recv(2)
    if(encoded == b'\x00'): return 0
    decoded = 0; i=1
    while encoded[i]&128:
        decoded = (encoded[i]-128)<<7*i|decoded
        encoded += conn.recv(1)
        i+=1
    decoded = (encoded[i])<<7*i|decoded
    return encoded, decoded

class Broker:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        