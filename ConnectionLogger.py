# Import the csv module to handle CSV file operations
import csv
# Import os module to interact with the file system
import os
# Import datetime to get current timestamp for logging
from datetime import datetime

# Define a class to log connection-related messages
class ConnectionLogger:
    # Constructor to initialize the logger with a filename
    def __init__(self, filename="connection_logs.csv"):
        self.filename = filename  # Name of the CSV file to store logs
        self.headers = ["Timestamp", "Source", "Type", "Message"]  # Column headers

        # Check if the log file already exists
        if not os.path.exists(self.filename):
            # If it doesn't exist, create it and write the headers
            with open(self.filename, mode='w', newline='') as file:
                writer = csv.writer(file)  # Create CSV writer object
                writer.writerow(self.headers)  # Write the header row

    # Method to write a log entry
    def log(self, source, msg_type, message):
        # Get current timestamp in a readable format
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Open the file in append mode to add new log entries
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)  # Create CSV writer object
            writer.writerow([
                timestamp,       # Add timestamp to log
                source,          # Add source of the message (IP, ID, etc.)
                msg_type,        # Add type of message (e.g., MQTT, SOCKET)
                message[:100]    # Truncate message to first 100 characters
            ])

# Only execute the below code when the script is run directly
if __name__ == "__main__":
    # Create an instance of the logger
    logger = ConnectionLogger()
    # Log a message coming from "Client-001" using MQTT protocol
    logger.log("Client-001", "MQTT", "Train delay update: Mumbai Local is delayed by 10 mins")
    # Log another message coming from a raw socket with some sample data
    logger.log("192.168.0.12:50123", "SOCKET", "SIM:45:NDLS,GZB")
    # Print a confirmation message
    print("Logs written to connection_logs.csv")
