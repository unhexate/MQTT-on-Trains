# Import the custom MQTT client class
from client import Client

# Standard Python libraries
import time
import threading
import random
import sys
import math

# Dictionary of major non-coastal cities in India with their [latitude, longitude]
TOP_CITIES = {
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946],
    "Hyderabad": [17.3850, 78.4867],
    "Ahmedabad": [23.0225, 72.5714],
    "Pune": [18.5204, 73.8567],
    "Jaipur": [26.9124, 75.7873],
    "Lucknow": [26.8467, 80.9462]
}

# Define the Train class
class Train:
    def __init__(self, id: str):
        # Set train ID
        self.id = id

        # Create a new MQTT client for this train
        self.client = Client(id)

        # Randomly pick a source city from the list
        self.src = random.choice([k for k in TOP_CITIES])[:]

        # Set current position to source city coordinates
        self.pos = TOP_CITIES[self.src][:]

        # Randomly pick a destination city different from source
        self.dest = random.choice([k for k in TOP_CITIES if k != self.src])[:]

        # Calculate steps needed to simulate train travel using Euclidean distance
        self.steps = int(math.sqrt((TOP_CITIES[self.dest][0] - TOP_CITIES[self.src][0])**2 
                                   + (TOP_CITIES[self.dest][1] - TOP_CITIES[self.src][1])**2) * 2)

        # Initialize current step count to 0
        self.current_steps = 0

    # Optional message handler – currently commented out
    # def __on_msg(self, msg):
    #     command = msg.split()
    #     if(command[0] == "goto"):
    #         if(self.current_steps == self.steps and command[1] in TOP_CITIES.values):
    #             self.src = self.dest
    #             self.dest = TOP_CITIES[command[1]]
    #             self.current_steps = 0

    # Private method to simulate train movement
    def __move(self):
        while(True):
            # If train hasn't reached its destination
            if self.current_steps != self.steps:
                # Get fresh copies of source and destination coordinates
                src_coords = TOP_CITIES[self.src][:]
                dest_coords = TOP_CITIES[self.dest][:]

                # Increment step count
                self.current_steps += 1

                # Calculate current position using linear interpolation
                self.pos[0] = round(src_coords[0] + (dest_coords[0]-src_coords[0])/self.steps * self.current_steps, 4)
                self.pos[1] = round(src_coords[1] + (dest_coords[1]-src_coords[1])/self.steps * self.current_steps, 4)

                # Publish current location to the broker
                self.client.publish(f"trains/{self.id}", f"location,{self.id},{self.pos[0]},{self.pos[1]}")

            else:
                # Reached destination: set new source to old destination
                self.src = self.dest
                self.current_steps = 0

                # Randomly pick a new destination different from the current one
                self.dest = random.choice([k for k in TOP_CITIES if k != self.src])[:]

                # Recalculate steps to reach new destination
                self.steps = int(math.sqrt((TOP_CITIES[self.dest][0] - TOP_CITIES[self.src][0])**2 
                                           + (TOP_CITIES[self.dest][1] - TOP_CITIES[self.src][1])**2) * 2)

                # Publish route update message
                self.client.publish(f"trains/{self.id}", f"route,{self.id},{self.src},{self.dest}")

            # Wait for 1 second between steps to simulate movement speed
            time.sleep(1)

    # Connect the train client to MQTT broker
    def connect(self, broker: str, port: int, keep_alive: int = 10):
        self.client.connect(broker, port, keep_alive)        # Connect to broker
        self.client.loop()                                   # Start MQTT loop to handle messages
        self.client.subscribe(f"trains/{self.id}")           # Subscribe to its own topic for commands

    # Start train simulation
    def start(self):
        # Publish initial greeting message with position and route
        self.client.publish(f"trains/{self.id}", f"hello,{self.id},{self.pos[0]},{self.pos[1]},{self.src},{self.dest}")
        
        # If needed, we can define a callback for message handling
        # self.client.on_message = self.__on_msg

        # Run the __move method in a separate thread to simulate motion
        move_thread = threading.Thread(target=self.__move)
        move_thread.start()


# Run this block only if the script is executed directly (not imported)
if __name__ == "__main__":

    # Ensure the script gets exactly 2 command-line arguments: TrainName and BrokerIP
    if len(sys.argv) != 3:
        print("Usage: python Train.py <TrainName> <BrokerIP>")
        sys.exit(1)

    # Get train name and broker IP from command line
    train_name = sys.argv[1]
    broker_ip = sys.argv[2]

    # Create the Train instance
    train = Train(train_name)

    # Connect to the broker
    train.connect(broker_ip, 1883)

    # Start the movement and communication logic
    train.start()
