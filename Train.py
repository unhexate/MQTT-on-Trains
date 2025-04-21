from client import Client
import time
import threading
import random
import sys
import math

# Non-coastal cities
TOP_CITIES = {
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

class Train:
    def __init__(self, id: str):
        self.id = id
        self.client = Client(id)
        self.src = random.choice([k for k in TOP_CITIES])
        self.pos = TOP_CITIES[self.src]
        self.dest = random.choice([k for k in TOP_CITIES if k!=self.src])
        self.steps = int(math.sqrt((TOP_CITIES[self.dest][0] - TOP_CITIES[self.src][0])**2 
                                   + (TOP_CITIES[self.dest][1] - TOP_CITIES[self.src][1])**2)*2)
        print(self.steps)
                    # how many steps to take, how many secs
        self.current_steps = 0

    # def __on_msg(self,msg):
    #     command = msg.split()
    #     if(command[0] == "goto"):
    #         if(self.current_steps == self.steps and command[1] in TOP_CITIES.values):
    #             self.src = self.dest
    #             self.dest = TOP_CITIES[command[1]]
    #             self.current_steps = 0
        
    def __move(self):
        while(True):
            if(self.current_steps != self.steps):
                src_coords = TOP_CITIES[self.src]
                dest_coords = TOP_CITIES[self.dest]
                self.current_steps+=1
                self.pos[0] = round(src_coords[0] + (dest_coords[0]-src_coords[0])/self.steps * self.current_steps, 4)
                self.pos[1] = round(src_coords[1] + (dest_coords[1]-src_coords[1])/self.steps * self.current_steps, 4)
                self.client.publish(f"trains/{self.id}", f"location,{self.id},{self.pos[0]},{self.pos[1]}")
            else:
                self.src = self.dest
                self.current_steps = 0
                # time.sleep(5)
                self.dest = random.choice([k for k in TOP_CITIES if k!=self.src])
                self.steps = int(math.sqrt((TOP_CITIES[self.dest][0] - TOP_CITIES[self.src][0])**2 
                                   + (TOP_CITIES[self.dest][1] - TOP_CITIES[self.src][1])**2) * 2)
                print(self.steps)
                self.client.publish(f"trains/{self.id}", f"route,{self.id},{self.src},{self.dest}")
            time.sleep(1)

            
    def connect(self, broker: str, port: int, keep_alive: int = 10):
        self.client.connect(broker, port, keep_alive)
        self.client.loop()
        self.client.subscribe(f"trains/{self.id}")

    def start(self):
        self.client.publish(f"trains/{self.id}", f"hello,{self.id},{self.pos[0]},{self.pos[1]},{self.src},{self.dest}")
        # self.client.on_message = self.__on_msg
        move_thread = threading.Thread(target = self.__move)
        move_thread.start()


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python Train.py <TrainName> <BrokerIP>")
        sys.exit(1)

    train_name = sys.argv[1]
    broker_ip = sys.argv[2]

    train = Train(train_name)
    train.connect(broker_ip, 1883)
    train.start()