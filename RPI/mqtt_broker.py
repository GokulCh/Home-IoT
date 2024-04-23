import threading
import time
import json
import warnings
import datetime
import platform
import logging
from functools import wraps
import paho.mqtt.client as mqtt

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOPIC = "esp32/sensor"
MQTT_HOST = "172.20.10.2"
MQTT_PORT = 1883

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
def check_mqtt_connection(client):
    return client.is_connected()

@handle_error
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.publish(TOPIC, "A Raspberry Pi has connected to the MQTT broker!")
        client.subscribe(TOPIC)
        logging.info("[on_connect] Connected to MQTT server")
    else:
        logging.error(f"[on_connect] Failed to connect to MQTT server, return code: {rc}")

@handle_error
def on_disconnect(client, userdata, rc):
    if rc == 0:
        logging.info("[on_disconnect] Disconnected from MQTT server")
    else:
        logging.error(f"[on_disconnect] Unexpected disconnection from MQTT server, return code: {rc}")

@handle_error
def on_message(client, userdata, msg):
    logging.info(f"[on_message] Message received: {msg.payload.decode('utf-8')}")
    try:
        json_object = json.loads(msg.payload.decode("utf-8"))
        json_object["timestamp"] = str(datetime.datetime.now())
        logging.info(json.dumps(json_object, indent=2))
        add_json(json_object)
    except Exception as error:
        logging.error(f"[on_message] Error processing message: {error}")

@handle_error
def add_json(data):
    with open("data.json", "a+") as file:
        json.dump(data, file)
        file.write("\n")

@handle_error
def establish_connection():
    while True:
        try:
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            if platform.system() == "Windows" or platform.system() == "Linux":
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "rpi_client")
            if platform.system() == "Darwin":
                client = mqtt.Client("rpi_client")
            warnings.filterwarnings("default", category=DeprecationWarning)
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.on_message = on_message
            client.connect(MQTT_HOST, MQTT_PORT)
            client.loop_forever()
            break
        except Exception as error:
            logging.error(f"[establish_connection] Error connecting to MQTT server: {error}")
            logging.info("[establish_connection] Retrying in 60 seconds...")
            time.sleep(60)

@handle_error
def start_mqtt_thread():
    thread = threading.Thread(target=establish_connection)
    thread.start()

@handle_error
def run():
    start_mqtt_thread()

if __name__ == "__main__":
    run()