import socket
import select
import threading

class RawSocketManager:
    def __init__(self, host='localhost', port=12348):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.running = False
        self.callback = None

    def set_callback(self, callback):
        self.callback = callback

    def start(self):
        self.running = True
        threading.Thread(target=self._listen).start()

    def stop(self):
        self.running = False
        self.socket.close()

    def _listen(self):
        while self.running:
            ready = select.select([self.socket], [], [], 1)
            if ready[0]:
                data, addr = self.socket.recvfrom(65535)
                if self.callback:
                    self.callback(data, addr)

    def send_raw(self, data, dest_addr):
        try:
            self.socket.sendto(data, (dest_addr, self.port))
            return True
        except Exception as e:
            print(f"Raw socket error: {e}")
            return False

if __name__ == "__main__":
    def callback(data, addr):
        print(f"Received from {addr}: {data[:20]}...")

    manager = RawSocketManager()
    manager.set_callback(callback)
    manager.start()
    
    try:
        while True:
            message = input("Enter message to send (or 'quit'): ")
            if message.lower() == 'quit':
                break
            manager.send_raw(message.encode('utf-8'), 'localhost')
    finally:
        manager.stop()
