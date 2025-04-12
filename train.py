import pandas as pd
import socket
import threading
from datetime import datetime
from client import Client

BROKER = "localhost"
TOPIC = "indian_railways/local_trains"

def initialize_train_data():
    data = {
        'Train_Number': ['101', '102', '201', '202'],
        'Train_Name': ['Mumbai Local 1', 'Delhi Local 1', 'Chennai Local 1', 'Kolkata Local 1'],
        'Source_Station': ['CSTM', 'NDLS', 'MAS', 'HWH'],
        'Destination_Station': ['THANE', 'GZB', 'TAMBARAM', 'BARRACKPORE'],
        'Departure_Time': ['08:00', '09:00', '10:00', '11:00'],
        'Arrival_Time': ['08:45', '09:45', '10:45', '11:45'],
        'Expected_Departure': ['08:10', '09:00', '10:05', '11:20'],
        'Expected_Arrival': ['08:50', '09:40', '10:50', '11:55']
    }
    df = pd.DataFrame(data)
    df.to_csv("local_trains_india.csv", index=False)
    return df

class TrainMQTTClient:
    def __init__(self, client_id=""):
        self.client = Client(client_id)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        
    def on_connect(self, flags, reason_code):
        print(f"Connected with flags {flags}, reason code {reason_code}")
        self.client.subscribe([(TOPIC, 0)])
        
    def on_message(self, msg):
        print(f"[MQTT] Received '{msg}'")
        
    def connect(self, broker, port, keep_alive):
        self.client.connect(broker, port, keep_alive)
        self.client.loop()
        
    def send_message(self, train_name, message):
        full_message = f"[{train_name}] says: {message}"
        self.client.publish(TOPIC, full_message)
        return f"MQTT sent: {full_message}"

class SocketServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('localhost', 12345))
        self.server.listen(5)
        print("[Socket] Server listening on port 12345")
        
    def handle_client(self, client_socket):
        msg = client_socket.recv(1024).decode('utf-8')
        print(f"[Socket] Received: {msg}")
        client_socket.send(f"Ack: {msg}".encode('utf-8'))
        client_socket.close()
        
    def listen(self):
        while True:
            client, addr = self.server.accept()
            print(f"[Socket] Connected with {addr}")
            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()

class TrainSystem:
    def __init__(self):
        self.df = initialize_train_data()
        self.mqtt_client = TrainMQTTClient("train_system")
        self.mqtt_client.connect(BROKER, 1883, 60)
        self.socket_server = SocketServer()
        threading.Thread(target=self.socket_server.listen, daemon=True).start()
        
    @staticmethod
    def calculate_delay(scheduled, expected):
        scheduled_dt = datetime.strptime(scheduled, "%H:%M")
        expected_dt = datetime.strptime(expected, "%H:%M")
        return int((expected_dt - scheduled_dt).total_seconds() / 60)
        
    def book_trains(self, source, destination):
        trains = self.df[(self.df["Source_Station"] == source) & 
                        (self.df["Destination_Station"] == destination)]
        if trains.empty:
            return "🚫 No trains found."
        result = ""
        for _, row in trains.iterrows():
            dep_delay = self.calculate_delay(row["Departure_Time"], row["Expected_Departure"])
            arr_delay = self.calculate_delay(row["Arrival_Time"], row["Expected_Arrival"])
            result += (
                f"🚆 Train: {row['Train_Name']} ({row['Train_Number']})\n"
                f"🔁 Route: {row['Source_Station']} ➡ {row['Destination_Station']}\n"
                f"⏰ Departure: {row['Departure_Time']} (Delay: {dep_delay} min)\n"
                f"🕒 Arrival: {row['Arrival_Time']} (Delay: {arr_delay} min)\n"
                f"--------------------------\n"
            )
        return result
        
    def send_socket_data(self, message):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 12345))
        client.send(message.encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        client.close()
        return response

def main_menu():
    system = TrainSystem()
    while True:
        print("\n1. Book Trains")
        print("2. Send MQTT Message")
        print("3. Send Socket Message")
        print("4. Exit")
        choice = input("Enter choice: ")
        
        if choice == "1":
            source = input("Enter source station: ").upper()
            destination = input("Enter destination station: ").upper()
            print(system.book_trains(source, destination))
            
        elif choice == "2":
            train_name = input("Enter train name: ")
            message = input("Enter message: ")
            print(system.mqtt_client.send_message(train_name, message))
            
        elif choice == "3":
            message = input("Enter socket message: ")
            print(system.send_socket_data(message))
            
        elif choice == "4":
            break
            
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main_menu()
