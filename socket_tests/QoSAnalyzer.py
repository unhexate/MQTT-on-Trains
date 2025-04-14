import time
import csv
import os
from datetime import datetime

class QoSAnalyzer:
    def __init__(self, filename="qos_metrics.csv"):
        self.filename = filename
        self.sent_times = {}   
        self.received_times = {}   
        
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Message ID", "Sent Time", "Received Time", "Delivery Delay (ms)"])

    def log_publish(self, msg_id):
        self.sent_times[msg_id] = time.time()

    def log_receive(self, msg_id):
        self.received_times[msg_id] = time.time()
        self._log_to_file(msg_id)

    def _log_to_file(self, msg_id):
        if msg_id in self.sent_times and msg_id in self.received_times:
            sent_time = self.sent_times[msg_id]
            recv_time = self.received_times[msg_id]
            delay_ms = (recv_time - sent_time) * 1000

            with open(self.filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    msg_id,
                    datetime.fromtimestamp(sent_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    datetime.fromtimestamp(recv_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    f"{delay_ms:.2f}"
                ])

    def report(self):
        print(f"QoS Delivery Report from {self.filename}:")
        with open(self.filename, mode='r') as f:
            for line in f.readlines()[1:]:
                print(line.strip())

if __name__ == "__main__":
    analyzer = QoSAnalyzer()
    analyzer.log_publish("msg_1")
    time.sleep(0.3)  # Simulate delay
    analyzer.log_receive("msg_1")
    analyzer.report()
