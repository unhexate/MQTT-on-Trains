# Import the Train class from Train.py – represents an individual train node
from Train import Train

# Import the ControlCenter class from ControlCenter.py – acts like a central controller
from ControlCenter import ControlCenter

# Import the Broker class from broker.py – represents the MQTT message broker
from broker import Broker

# Create an instance of the Broker running on 'localhost'
broker = Broker('localhost')

# Create a Train object named 'Train A'
train_A = Train('Train A')

# Create another Train object named 'Train B'
train_B = Train('Train B')

# Create the ControlCenter object which will manage/train monitor from 'localhost'
control_center = ControlCenter('localhost')


# Start the MQTT broker's event loop so it begins handling connections and messages
broker.loop()

# Connect the control center to the MQTT broker at localhost on port 1883
control_center.connect("localhost", 1883)

# Start the control center’s behavior (likely a loop that listens and responds to trains)
control_center.start()

# Connect Train A to the MQTT broker at localhost on port 1883
train_A.connect("localhost", 1883)

# Start Train A’s behavior (like sending location, status, etc.)
train_A.start()

# Connect Train B to the MQTT broker at localhost on port 1883
train_B.connect("localhost", 1883)

# Start Train B’s behavior
train_B.start()
