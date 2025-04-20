from MQTTPacket import FixedHeader, MQTTPacket
from variableheaders import *
from utils import *

fixed = FixedHeader(PUBLISH, 0b0010)
var = PublishVariableHeader("trains", "hello",0x20)
packet = MQTTPacket(fixed, var)
print(packet.variable_data.packet_id)
print(packet.encode().hex(' '))