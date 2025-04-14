import json
from enum import Enum

class MessageType(Enum):
    TRAIN_INFO = 1
    DELAY_ALERT = 2
    BOOKING_REQUEST = 3
    SYSTEM_STATUS = 4

class RailProtocol:
    @staticmethod
    def encode_message(msg_type, payload):
        return json.dumps({
            "version": "1.0",
            "type": msg_type.name,
            "payload": payload,
            "checksum": sum(payload.encode('utf-8')) % 1000
        }).encode('utf-8')

    @staticmethod
    def decode_message(data):
        try:
            message = json.loads(data.decode('utf-8'))
            if message.get("checksum") != sum(message["payload"].encode('utf-8')) % 1000:
                raise ValueError("Checksum mismatch")
            message["type"] = MessageType[message["type"]]
            return message
        except Exception as e:
            print(f"Protocol error: {e}")
            return None

    @staticmethod
    def create_train_info(train_data):
        return RailProtocol.encode_message(
            MessageType.TRAIN_INFO,
            json.dumps(train_data)
        )

    @staticmethod
    def create_delay_alert(train_name, delay):
        return RailProtocol.encode_message(
            MessageType.DELAY_ALERT,
            f"{train_name}:{delay} minutes"
        )

if __name__ == "__main__":
    # Protocol demonstration
    train_data = {"train": "Mumbai Local 1", "delay": 15}
    encoded = RailProtocol.create_train_info(train_data)
    print("Encoded:", encoded)
    
    decoded = RailProtocol.decode_message(encoded)
    print("Decoded:", decoded)
