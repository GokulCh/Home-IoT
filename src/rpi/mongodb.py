import logging
from functools import wraps
import pymongo
import json
import time
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MongoDB credentials
MONGODB_KEY = "mongodb+srv://Gokul:SXG7hH1tqjkZrdTG@iotcluster.if6cdfg.mongodb.net/"
MONGODB_DB = "IoTDataArchive"
MONGODB_COLLECTION = "sensor_data"

# Global variable to store MongoDB collection
collection = None

def handle_error(func):
    """Decorator to handle exceptions and log them"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"[{func.__name__}] Error: {e}")
    return wrapper

@handle_error
def establish_connection():
    """Establish connection to MongoDB"""
    global collection
    client = pymongo.MongoClient(MONGODB_KEY)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    logging.info("[establish_connection] Established connection to MongoDB")

@handle_error
def get_collection():
    """Get the MongoDB collection"""
    return collection

@handle_error
def add_data(data):
    """Add data to the MongoDB collection"""
    get_collection().insert_one(data)

@handle_error
def create_data_json():
    """Create an empty data.json file"""
    with open("data.json", "w") as file:
        file.write("")
    logging.info("[create_data_json] Data.json has been created")

@handle_error
def add_json_data():
    """Add data from data.json to MongoDB"""
    try:
        with open("data.json", "r") as file:
            if file.read().strip():
                file.seek(0)
                for line in file:
                    try:
                        data = json.loads(line.strip())
                        add_data(data)
                    except json.JSONDecodeError as error:
                        logging.error(f"[add_json_data] Error decoding JSON: {error}")
        logging.info("[add_json_data] Data sent to MongoDB")
        with open("data.json", "w") as clear_file:
            clear_file.write("")
    except FileNotFoundError:
        create_data_json()

@handle_error
def periodic_send():
    """Periodically send data from data.json to MongoDB"""
    def send_data():
        while True:
            add_json_data()
            time.sleep(1800)  # In seconds

    thread = threading.Thread(target=send_data, daemon=True)
    thread.start()

@handle_error
def run():
    """Set up the MongoDB connection and start periodic sending"""
    establish_connection()
    periodic_send()

if __name__ == "__main__":
    run()