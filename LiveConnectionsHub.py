# Import necessary classes and functions from Mininet
from mininet.topo import Topo                # Used to define a custom topology
from mininet.net import Mininet              # Used to create and manage the Mininet network
from mininet.node import OVSController       # Open vSwitch Controller
from mininet.link import TCLink              # Used to set link characteristics (like delay)
from mininet.cli import CLI                  # To interact with the Mininet network via CLI

# Define a custom topology for the train system
class TrainSystemTopo(Topo):
    
    def build(self):
        # Add a single switch to the topology
        s1 = self.addSwitch('s1')

        # Add hosts representing different entities in the system
        broker = self.addHost('broker')      # MQTT broker
        control = self.addHost('control')    # Control Center
        trainA = self.addHost('trainA')      # Train A
        trainB = self.addHost('trainB')      # Train B

        # Connect each host to the switch with specified link delay
        self.addLink(trainA, s1, cls=TCLink, delay='50ms')   # Train A to switch, with 50ms delay
        self.addLink(trainB, s1, cls=TCLink, delay='50ms')   # Train B to switch, with 50ms delay
        self.addLink(control, s1, cls=TCLink, delay='20ms')  # Control Center to switch, with 20ms delay
        self.addLink(broker, s1, cls=TCLink, delay='20ms')   # Broker to switch, with 20ms delay

# Main block to run the network
if __name__ == '__main__':
    from mininet.log import setLogLevel
    setLogLevel('info')    # Set log level to show network activity in terminal

    topo = TrainSystemTopo()    # Instantiate the custom topology
    net = Mininet(topo=topo, controller=OVSController, link=TCLink)  # Create the network using the topology
    net.start()                 # Start the network

    # Get the host objects from the network by name
    trainA = net.get('trainA')
    trainB = net.get('trainB')
    broker = net.get('broker')
    control = net.get('control')

    # Run broker.py script on the broker node, bind to 10.0.0.1 IP (background process)
    broker.cmd("python broker.py 10.0.0.1&")

    # Run ControlCenter.py with broker and HTTP IP addresses (background process)
    control.cmd("python ControlCenter.py 10.0.0.1 10.0.0.2 &")

    # Run Train.py for Train A, connect to broker IP (background process)
    trainA.cmd("python Train.py 'Train A' 10.0.0.1 &")

    # Run Train.py for Train B, connect to broker IP (background process)
    trainB.cmd("python Train.py 'Train B' 10.0.0.1 &")

    # Launch Mininet CLI to interact with the network manually
    CLI(net)

    # Stop the network once the CLI session ends
    net.stop()
