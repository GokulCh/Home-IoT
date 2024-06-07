import os
import time
import json
import uuid
import platform
import logging
import datetime
import warnings
import threading
import paho.mqtt.client as mqtt

import bot
import config

# Constants
MQTT_HOST = "172.18.220.138"
MQTT_PORT = 1883
TOPICS = {
    "CLIENT": "rpi_client",
    "SENSOR_DATA": "esp32/sensor_data",
    "SENSOR_CHECK": "esp32/sensor_check",
    # "SLEEP": "esp32/sleep"
}

RPI_MAC_ADDRESS = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2 * 6, 2)])

# Global variables
triggered_sensors = {}

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Callback functions
@config.handle_error
def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the server."""
    if rc == 0:
        logging.info("[on_connect] Connected to MQTT server")
        # for topic in [f"{TOPICS['SENSOR_DATA']}/#", f"{TOPICS['SENSOR_CHECK']}/#", f"{TOPICS['SLEEP']}/#"]:
        for topic in [f"{TOPICS['SENSOR_DATA']}/#", f"{TOPICS['SENSOR_CHECK']}/#"]:
            client.subscribe(topic)
        bot.send_discord_message("mqtt_rpi_connection", f"**Address:**\n``{RPI_MAC_ADDRESS}``")
    else:
        logging.error(f"[on_connect] Failed to connect to MQTT server, return code: {rc}")

@config.handle_error
def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the server."""
    if rc == 0:
        logging.info("[on_disconnect] Disconnected from MQTT server")
    else:
        logging.error(f"[on_disconnect] Unexpected disconnection from MQTT server, return code: {rc}")
    bot.send_discord_message("mqtt_rpi_connection", f"**Address:**\n``{RPI_MAC_ADDRESS}``")

@config.handle_error
def on_message(client, userdata, msg):
    """Callback for when a message is received from the server."""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    logging.info(f"[on_message] [{topic}] Received: {payload}")

    try:
        if topic.startswith(TOPICS["SENSOR_DATA"] + "/"):
            handle_sensor_data(topic, payload)
        elif topic.startswith(TOPICS["SENSOR_CHECK"] + "/"):
            handle_sensor_check(topic, payload)
        # elif topic.startswith(TOPICS["SLEEP"] + "/"):
            # handle_sleep(topic, payload)
        else:
            raise ValueError(f"Unexpected topic: {topic}")
    except Exception as error:
        logging.error(f"[on_message] Error processing message: {error}")


def handle_sensor_data(topic, payload):
    mac_address = topic.split("/")[2]
    json_object = json.loads(payload)
    sensor_type = json_object["sensor_type"]
    sensor_id = json_object["sensor_id"]

    if sensor_type == "pir":
        triggered_sensors[sensor_id] = datetime.datetime.now()

        if len(triggered_sensors) == 2:
            print("Triggered DWAIDbbd")
            sensor_ids = sorted(triggered_sensors.keys())
            first_sensor_id, second_sensor_id = sensor_ids
            first_trigger_time = triggered_sensors[first_sensor_id]
            second_trigger_time = triggered_sensors[second_sensor_id]

            if first_sensor_id == 1 and first_trigger_time < second_trigger_time:
                direction = "Enter"
            else:
                direction = "Exit"
                
            json_object["direction"] = direction
            config.add_data_json(json_object)
            bot.send_discord_message("mqtt_data_received", f"**ESP32:**\n``{mac_address}``\n**Received:**\n``{payload}``\n**Direction:** {direction}")
            triggered_sensors.clear()
        else:
            config.add_data_json(json_object)
            bot.send_discord_message("mqtt_data_received", f"**ESP32:**\n``{mac_address}``\n**Received:**\n``{payload}``")

def handle_sensor_check(topic, payload):
    mac_address = topic.split("/")[2]
    if payload == "pong":
        config.add_esp_rpi_json(mac_address, "On", "esp")
        bot.send_discord_message("esp32_connection", f"**ESP32:**\n``{mac_address}``\n**Status:**\n``Online``")
    else:
        logging.error(f"[on_message] Unexpected message on {topic}: {payload}")

def handle_sleep(topic, payload):
    mac_address = topic.split("/")[2]
    if payload == "slept":
        logging.info(f"ESP32 device {mac_address} has gone to sleep.")
        bot.send_discord_message("esp32_connection", f"**ESP32:**\n``{mac_address}``\n**Status:**\n``Sleep``")
    else:
        logging.error(f"[on_message] Unexpected message on {topic}: {payload}")

@config.handle_error
def establish_connection():
    """Establishes the MQTT connection."""
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
def check_and_publish_sleep(client):
    """Checks time and publishes sleep duration to MQTT topic."""
    sleep_sent = False

    while True:
        current_time = datetime.datetime.now().time()

        if current_time < datetime.time(8, 0) or current_time > datetime.time(20, 0):
            if not sleep_sent:
                wake_up_time = datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0))
                if current_time > datetime.time(20, 0):
                    wake_up_time += datetime.timedelta(days=1)
                sleep_duration = (wake_up_time - datetime.datetime.now()).total_seconds()
                client.publish(TOPICS["SLEEP"], str(int(sleep_duration)))
                sleep_sent = True
                logging.info(f"Going to sleep for {sleep_duration} seconds.")
            sleep_time = (datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0)) - datetime.datetime.now()).total_seconds()
            if sleep_time < 0:
                sleep_time += 86400  # Add a day in seconds if already past 8 AM
            time.sleep(sleep_time)
            sleep_sent = False
        else:
            time.sleep(60)

@config.handle_error
def check_alive_devices(client):
    """Checks the alive status of devices and publishes a ping message."""
    config_folder = "Config"
    esp_file_path = os.path.join(config_folder, "esp.json")

    while True:
        current_time = datetime.datetime.now()
        next_hour = (current_time.replace(second=0, microsecond=0) + datetime.timedelta(hours=1)).replace(minute=0)
        time_until_next_hour = (next_hour - current_time).total_seconds()
        time.sleep(time_until_next_hour)

        client.publish(TOPICS["SENSOR_CHECK"], "ping")

        if os.path.exists(esp_file_path):
            with open(esp_file_path, "r") as file:
                for line in file:
                    try:
                        entry = json.loads(line)
                        mac_address = entry["mac_address"]
                        last_seen = datetime.datetime.fromisoformat(entry["time"])

                        if (current_time - last_seen).total_seconds() >= 3600:
                            logging.warning(f"ESP32 device {mac_address} has not been seen for 1 hour or more.")
                            bot.send_discord_message("esp32_connection", f"**ESP32:**\n``{mac_address}``\n**Status:** Offline")
                            config.add_esp_rpi_json(mac_address, "Off", "esp")
                    except json.JSONDecodeError:
                        logging.error(f"Skipping invalid JSON line: {line}")
        else:
            logging.warning(f"File '{esp_file_path}' does not exist.")

@config.handle_error
def start_threads():
    """Starts the necessary threads for checking device status and publishing sleep data."""
    client = establish_connection()

    threading.Thread(target=check_alive_devices, args=(client,)).start()
    # threading.Thread(target=check_and_publish_sleep, args=(client,)).start()

@config.handle_error
def run():
    """Main entry point for the script."""
    start_threads()

if __name__ == "__main__":
    run()
