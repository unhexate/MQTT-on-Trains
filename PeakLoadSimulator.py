import threading
import socket
import time
import random
from train_system import TrainSystem

class LoadSimulator:
    def __init__(self):
        self.system = TrainSystem()
        self.stations = list(set(self.system.df["Source_Station"]) | 
                           set(self.system.df["Destination_Station"]))

    def simulate_client(self, client_id):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', 12345))
            
            src = random.choice(self.stations)
            dst = random.choice([x for x in self.stations if x != src])
            
            s.send(f"SIM:{client_id}:{src},{dst}".encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            print(f"Client {client_id} got: {response[:50]}...")
            s.close()
        except Exception as e:
            print(f"Client {client_id} error: {e}")

    def run_simulation(self, num_clients=50):
        threads = []
        for i in range(num_clients):
            t = threading.Thread(target=self.simulate_client, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(random.uniform(0.1, 0.5))
        
        for t in threads:
            t.join()

if __name__ == "__main__":
    print("Starting peak load simulation...")
    simulator = LoadSimulator()
    while True:
        try:
            num = int(input("Enter number of clients to simulate (0 to exit): "))
            if num <= 0:
                break
            simulator.run_simulation(num)
        except ValueError:
            print("Please enter a valid number")
