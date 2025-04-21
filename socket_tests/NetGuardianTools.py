# Import necessary modules
import socket               # For creating and managing sockets
import select               # For monitoring socket events
import threading            # For running the listener in a separate thread

# Define a class to manage raw socket communication
class RawSocketManager:
    def __init__(self, host='localhost', port=12348):
        self.host = host    # Host address
        self.port = port    # Port number
        # Create a raw socket using IPv4 and raw protocol
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        # Allow address reuse
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the host and port
        self.socket.bind((host, port))
        self.running = False  # Control flag for running listener
        self.callback = None  # Placeholder for callback function

    # Set a callback function to be called when data is received
    def set_callback(self, callback):
        self.callback = callback

    # Start the listening thread
    def start(self):
        self.running = True
        threading.Thread(target=self._listen).start()  # Launch listener in new thread

    # Stop the listener and close the socket
    def stop(self):
        self.running = False
        self.socket.close()  # Close socket on stop

    # Internal method to listen for incoming raw data
    def _listen(self):
        while self.running:
            # Wait for socket to be ready for reading
            ready = select.select([self.socket], [], [], 1)
            if ready[0]:
                # Receive data from the socket
                data, addr = self.socket.recvfrom(65535)
                # If a callback is set, call it with received data
                if self.callback:
                    self.callback(data, addr)

    # Method to send raw data to a destination address
    def send_raw(self, data, dest_addr):
        try:
            # Send raw data to the given destination address
            self.socket.sendto(data, (dest_addr, self.port))
            return True  # Return success
        except Exception as e:
            # Print error if sending fails
            print(f"Raw socket error: {e}")
            return False  # Return failure

# Main block for running the manager
if __name__ == "__main__":
    # Define a callback function to handle received data
    def callback(data, addr):
        # Print the sender's address and the first 20 bytes of data
        print(f"Received from {addr}: {data[:20]}...")

    # Create an instance of the raw socket manager
    manager = RawSocketManager()
    # Set the callback function
    manager.set_callback(callback)
    # Start listening for data
    manager.start()
    
    try:
        while True:
            # Get user input
            message = input("Enter message to send (or 'quit'): ")
            if message.lower() == 'quit':
                break  # Exit loop if user types 'quit'
            # Send the message as raw data to localhost
            manager.send_raw(message.encode('utf-8'), 'localhost')
    finally:
        # Stop the manager and close the socket
        manager.stop()
