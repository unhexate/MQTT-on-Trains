import csv
import os
from datetime import datetime

class ConnectionLogger:
    def __init__(self, filename="connection_logs.csv"):
        self.filename = filename
        self.headers = ["Timestamp", "Source", "Type", "Message"]

        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)

    def log(self, source, msg_type, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp,
                source,
                msg_type,
                message[:100]  
            ])

if __name__ == "__main__":
    logger = ConnectionLogger()
    logger.log("Client-001", "MQTT", "Train delay update: Mumbai Local is delayed by 10 mins")
    logger.log("192.168.0.12:50123", "SOCKET", "SIM:45:NDLS,GZB")
    print("Logs written to connection_logs.csv")
