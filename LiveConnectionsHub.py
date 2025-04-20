from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.cli import CLI


class TrainSystemTopo(Topo):
    
    def build(self):
        s1 = self.addSwitch('s1')

        # add hosts
        broker = self.addHost('broker')
        control = self.addHost('control')
        trainA = self.addHost('trainA')
        trainB = self.addHost('trainB')

        # add links
        self.addLink(trainA, s1, cls=TCLink, delay='50ms')
        self.addLink(trainB, s1, cls=TCLink, delay='50ms')
        self.addLink(control, s1, cls=TCLink, delay='20ms')
        self.addLink(broker, s1, cls=TCLink, delay='20ms')


if __name__ == '__main__':
    from mininet.log import setLogLevel
    setLogLevel('info')

    topo = TrainSystemTopo()
    net = Mininet(topo=topo, controller=OVSController, link=TCLink)
    net.start()

    trainA = net.get('trainA')
    trainB = net.get('trainB')
    broker = net.get('broker')
    control = net.get('control')

    broker.cmd("python broker.py 10.0.0.1&")
    control.cmd("python ControlCenter.py 10.0.0.1 10.0.0.2 &")
    trainA.cmd("python Train.py 'Train A' 10.0.0.1 &")
    trainB.cmd("python Train.py 'Train B' 10.0.0.1 &")

    CLI(net)
    net.stop()