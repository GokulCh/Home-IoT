import threading
import time
import json
import warnings
import datetime
import platform
import logging
import uuid
from functools import wraps
import paho.mqtt.client as mqtt
import bot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOPIC_SENSOR_DATA = "esp32/sensor_data"
TOPIC_SENSOR_CHECK = "esp32/sensor_check"

MQTT_HOST = "10.247.42.220"
MQTT_PORT = 1883

ESP32_DEVICES = {}

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
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        pi_mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
        for ele in range(0,8*6,8)][::-1])

        client.subscribe(TOPIC_SENSOR_DATA)
        client.subscribe(TOPIC_SENSOR_CHECK + "/#")

        logging.info("[on_connect] Connected to MQTT server")

        bot.send_discord_message(
            "RPI MQTT Connection",
            "**Status:** Online"
            + "\n"
            + "**mac_address:** "
            + pi_mac_address
            + "\n"
            + "**Last seen:** "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "\n"
            + "**Subscribed to topics:** "
            + f"{TOPIC_SENSOR_DATA}, {TOPIC_SENSOR_CHECK}/#",
            bot.MQTT_WEBHOOK_URL,
        )

    else:
        logging.error(f"[on_connect] Failed to connect to MQTT server, return code: {rc}")


@handle_error
def on_disconnect(client, userdata, rc):
    if rc == 0:
        logging.info("[on_disconnect] Disconnected from MQTT server")
    else:
        logging.error(f"[on_disconnect] Unexpected disconnection from MQTT server, return code: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    logging.info(f"[on_message] [{topic}] Message received: {payload}")

    if topic == TOPIC_SENSOR_DATA:
        try:
            json_object = json.loads(payload)
            json_object["timestamp"] = str(datetime.datetime.now())
            mac_address = json_object["mac_address"]
            ESP32_DEVICES[mac_address] = datetime.datetime.now()
            logging.info(json.dumps(json_object, indent=2))
            add_json(json_object)
        except Exception as error:
            logging.error(f"[on_message] Error processing message: {error}")
    elif topic.startswith(TOPIC_SENSOR_CHECK + "/"):
        mac_address = topic.split("/")[2]  # Extract MAC address from the topic
        if payload == "pong":
            ESP32_DEVICES[mac_address] = datetime.datetime.now()

            bot.send_discord_message(f"ESP32 Status Check", f"**Status:** Online\n**mac_address:** {mac_address}\n**Last seen:** {ESP32_DEVICES[mac_address]}")

            logging.info(f"[on_message] Received 'pong' from ESP32 device {mac_address}")
        else:
            logging.error(f"[on_message] Unexpected message on {topic}: {payload}")
    else:
        logging.error(f"[on_message] Unexpected topic: {topic}, payload: {payload}")


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
            client.loop_start()
            break
        except Exception as error:
            logging.error(f"[establish_connection] Error connecting to MQTT server: {error}")
            logging.info("[establish_connection] Retrying in 60 seconds...")
            time.sleep(60)
    return client


@handle_error
def check_alive_devices(client):
    while True:
        client.publish(TOPIC_SENSOR_CHECK + "/42:24q::4;", "pong")
        time.sleep(30)
        current_time = datetime.datetime.now()
        for mac_address, last_seen in ESP32_DEVICES.copy().items():
            if (current_time - last_seen).total_seconds() >= 3600:  # Check if device hasn't been seen for 1 hour
                bot.send_discord_message(f"ESP32 Statys Check", f"**Status:** Offline\n**mac_address:** {mac_address}\n**Last seen:** {last_seen}")
                logging.warning(f"ESP32 device {mac_address} has not been seen for 1 hour or more.")
                del ESP32_DEVICES[mac_address]  # Remove the device from the dictionary
        time.sleep(3600)  # Check every hour


@handle_error
def start_threads():
    client = establish_connection()
    thread_check = threading.Thread(target=check_alive_devices, args=(client,))
    thread_check.start()


@handle_error
def run():
    start_threads()


if __name__ == "__main__":
    run()