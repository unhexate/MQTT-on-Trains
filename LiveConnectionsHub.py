import socket
import threading
from collections import defaultdict

class ConnectionHub:
    def __init__(self):
        self.active_connections = defaultdict(dict)
        self.lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 12347))
        self.server_socket.listen(100)
        print("[Hub] Listening for connections on port 12347")

    def handle_client(self, client_socket, address):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                with self.lock:
                    if data.startswith("REGISTER:"):
                        client_id = data.split(':')[1]
                        self.active_connections[address][client_id] = client_socket
                        print(f"[Hub] Registered {client_id} from {address}")
                        client_socket.send(f"ACK:{client_id}".encode('utf-8'))
                    else:
                        print(f"[Hub] Received: {data}")
                        client_socket.send(f"ECHO:{data}".encode('utf-8'))
        except Exception as e:
            print(f"[Hub] Error: {e}")
        finally:
            with self.lock:
                if address in self.active_connections:
                    del self.active_connections[address]
            client_socket.close()

    def run(self):
        while True:
            client_socket, address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    hub = ConnectionHub()
    hub.run()
