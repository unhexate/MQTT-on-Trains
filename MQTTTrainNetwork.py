from Train import Train
from ControlCenter import ControlCenter
from broker import Broker

broker = Broker('localhost')
train_A = Train('Train A')
train_B = Train('Train B')
control_center =  ControlCenter('localhost')


broker.loop()
control_center.connect("localhost", 1883)
control_center.start()
train_A.connect("localhost", 1883)
train_A.start()
train_B.connect("localhost", 1883)
train_B.start()
