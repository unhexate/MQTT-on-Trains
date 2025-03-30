# MQTT Train Control Demo

This project aims to implement a basic version of the MQTT protocol, and simulate communication within a train network. 

Inspired by https://iot.eclipse.org/community/resources/case-studies/pdf/Eclipse%20IoT%20Success%20Story%20-%20DB.pdf

train.py should simulate the trains (client)
control-center should simulate the control center (client)
broker.py should simulate the broker which maintains publishers and subscribers
mqtt.py provides the packets and methods to encode and decode them