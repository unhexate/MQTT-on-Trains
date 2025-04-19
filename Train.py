from client import Client
import time
import threading

TOP_CITIES = {
    "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Chennai": [13.0827, 80.2707],
    "Kolkata": [22.5726, 88.3639],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

class Train:
    def __init__(self, id: str, city: str):
        assert city in TOP_CITIES
        self.pos = TOP_CITIES[city]
        self.client = Client(id)
        self.src = [0,0]
        self.dest = [0,0]
        self.steps = 15 # how many steps to take, how many secs
        self.current_steps = 0

    def __on_msg(self,msg):
        command = msg.split()
        if(command[0] == "goto"):
            if(self.current_steps == self.steps and command[1] in TOP_CITIES.values):
                self.src = self.dest
                self.dest = command[1]
                self.current_steps = 0
                move_thread = threading.Thread(target = self.__move)
                move_thread.start()
        
    def __move(self):
        while(self.current_steps != self.steps):
            self.current_steps+=1
            self.pos[0] = self.src[0] + (self.dest[0]-self.src[0])/self.steps * self.current_steps
            self.pos[1] = self.src[1] + (self.dest[1]-self.src[1])/self.steps * self.current_steps
            Client.publish(f"trains/{self.id}", str(self.pos))
            time.sleep(1)
            
    def connect(self, broker: str, port: int, keep_alive: int = 60):
        self.client.connect(broker, port, keep_alive)
        self.client.loop()
        self.client.subscribe(f"trains/{self.id}")

    def start(self):
        self.client.on_message = self.__on_msg


if __name__ == "__main__":
    TrainA = Train("A")