import threading
import time
import json
import warnings
import datetime
import platform
import logging
import uuid
import config
import paho.mqtt.client as mqtt
import bot
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MQTT_HOST = "172.20.10.2"
MQTT_PORT = 1883

TOPIC_CLIENT = "rpi_client"
TOPIC_SENSOR_DATA = "esp32/sensor_data"
TOPIC_SENSOR_CHECK = "esp32/sensor_check"

RPI_MAC_ADDRESS = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)])

ESP32_DEVICES = {}

@config.handle_error
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("[on_connect] Connected to MQTT server")
        client.subscribe(TOPIC_SENSOR_DATA)
        client.subscribe(TOPIC_SENSOR_CHECK + "/#")
    else:
        logging.error(f"[on_connect] Failed to connect to MQTT server, return code: {rc}")


@config.handle_error
def on_disconnect(client, userdata, rc):
    if rc == 0:
        logging.info("[on_disconnect] Disconnected from MQTT server")
    else:
        logging.error(f"[on_disconnect] Unexpected disconnection from MQTT server, return code: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    logging.info(f"[on_message] [{topic}] Received: {payload}")

    if topic == TOPIC_SENSOR_DATA:
        try:
            json_object = json.loads(payload)
            bot.send_discord_message("Sensor Data", f"**sensor_name**: {json_object["sensor_name"]}\n**sensor_type**: {json_object["sensor_type"]}\n**mac_address**: {json_object["mac_address"]}\n**event**: {json_object["event"]}\n**timestamp**: {json_object["timestamp"]}", bot.MQTT_DATA_WEBHOOL_URL)

            config.add_data_json(json_object)
        except Exception as error:
            logging.error(f"[on_message] Error processing message: {error}")

    elif topic.startswith(TOPIC_SENSOR_CHECK + "/"):
        mac_address = topic.split("/")[2]
        if payload == "pong":
            try:
                config.add_esp_rpi_json(mac_address, "On", "esp")
            except Exception as error:
                logging.error(f"[on_message] Error processing message: {error}")
        else:
            logging.error(f"[on_message] Unexpected message on {topic}: {payload}")
    else:
        logging.error(f"[on_message] Unexpected topic: {topic}, payload: {payload}")


@config.handle_error
def establish_connection():
    config.add_esp_rpi_json(RPI_MAC_ADDRESS, "On", "rpi")

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


@config.handle_error
def check_alive_devices(client):
    config_folder = "Config"
    esp_file_path = os.path.join(config_folder, "esp.json")

    while True:
        client.publish(TOPIC_SENSOR_CHECK, "ping")
        time.sleep(30)
        current_time = datetime.datetime.now()

        if os.path.exists(esp_file_path):
            with open(esp_file_path, "r") as file:
                for line in file:
                    try:
                        entry = json.loads(line)
                        mac_address = entry["mac_address"]
                        last_seen_str = entry["time"]
                        last_seen = datetime.datetime.fromisoformat(last_seen_str)

                        if (current_time - last_seen).total_seconds() >= 3600:
                            logging.warning(f"ESP32 device {mac_address} has not been seen for 1 hour or more.")
                            config.add_esp_rpi_json(mac_address, "Off", "esp")
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON line: {line}")
        else:
            logging.warning(f"File '{esp_file_path}' does not exist.")
        time.sleep(3600)  # Check every hour


@config.handle_error
def start_threads():
    client = establish_connection()

    thread_check = threading.Thread(target=check_alive_devices, args=(client,))
    thread_check.start()


@config.handle_error
def run():
    start_threads()


if __name__ == "__main__":
    run()