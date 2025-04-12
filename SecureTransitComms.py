import socket
import ssl
from train_system import TrainSystem

class SecureSocketServer:
    def __init__(self, host='localhost', port=12346):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile='server.crt', keyfile='server.key')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.system = TrainSystem()

    def handle_client(self, conn):
        try:
            data = conn.recv(1024).decode('utf-8')
            print(f"[SecureSocket] Received: {data}")
            response = self.system.book_trains(data.split(',')[0], data.split(',')[1])
            conn.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Secure socket error: {e}")
        finally:
            conn.close()

    def run(self):
        print("[SecureSocket] SSL Server running on port 12346")
        while True:
            conn, addr = self.sock.accept()
            secure_conn = self.context.wrap_socket(conn, server_side=True)
            print(f"[SecureSocket] Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(secure_conn,)).start()

class SecureSocketClient:
    def __init__(self):
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.context.load_verify_locations('server.crt')

    def send_message(self, message):
        with socket.create_connection(('localhost', 12346)) as sock:
            with self.context.wrap_socket(sock, server_hostname='localhost') as secure_sock:
                secure_sock.send(message.encode('utf-8'))
                return secure_sock.recv(1024).decode('utf-8')

if __name__ == "__main__":
    import threading
    server = SecureSocketServer()
    threading.Thread(target=server.run, daemon=True).start()
    
    client = SecureSocketClient()
    while True:
        msg = input("Enter source,destination (e.g., CSTM,THANE): ")
        print(client.send_message(msg))
