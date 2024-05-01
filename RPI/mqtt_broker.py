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

MQTT_HOST = "10.42.0.1"
MQTT_PORT = 1883

TOPIC_CLIENT = "rpi_client"
TOPIC_SENSOR_DATA = "esp32/sensor_data"
TOPIC_SENSOR_CHECK = "esp32/sensor_check"
TOPIC_SLEEP = "esp32/sleep"

RPI_MAC_ADDRESS = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)])

ESP32_DEVICES = {}

@config.handle_error
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("[on_connect] Connected to MQTT server")
        client.subscribe(TOPIC_SENSOR_DATA)
        client.subscribe(TOPIC_SENSOR_CHECK + "/#")
        client.subscribe(TOPIC_SLEEP + "/#")

        bot.send_discord_message("MQTT - RPI Connected", f"**RPI:** {RPI_MAC_ADDRESS}", bot.MQTT_CONNECTED_WEBHOOK_URL)
    else:
        logging.error(f"[on_connect] Failed to connect to MQTT server, return code: {rc}")


@config.handle_error
def on_disconnect(client, userdata, rc):
    if rc == 0:
        logging.info("[on_disconnect] Disconnected from MQTT server")
    else:
        logging.error(f"[on_disconnect] Unexpected disconnection from MQTT server, return code: {rc}")
        bot.send_discord_message("MQTT - RPI Disconnected", f"**RPI:** {RPI_MAC_ADDRESS}", bot.MQTT_DISCONNECTED_WEBHOOK_URL)
    
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    logging.info(f"[on_message] [{topic}] Received: {payload}")
    if topic == TOPIC_SENSOR_DATA:
        try:
            json_object = json.loads(payload)
            config.add_data_json(json_object)
            bot.send_discord_message(f"MQTT Sensor Data", payload, bot.MQTT_DATA_WEBHOOL_URL)
        except Exception as error:
            logging.error(f"[on_message] Error processing message: {error}")

    elif topic.startswith(TOPIC_SENSOR_CHECK + "/"):
        mac_address = topic.split("/")[2]
        if payload == "pong":
            try:
                config.add_esp_rpi_json(mac_address, "On", "esp")
                bot.send_discord_message("ESP32 - Status Check", f"The ESP32 {mac_address} is online", bot.MQTT_STATUS_CHECK_WEBHOOK_URL)
            except Exception as error:
                logging.error(f"[on_message] Error processing message: {error}")
        else:
            logging.error(f"[on_message] Unexpected message on {topic}: {payload}")
    
    elif topic.startswith(TOPIC_SLEEP + "/"):
        mac_address = topic.split("/")[2]
        if payload == "slept":
            try:
                logging.info(f"ESP32 device {mac_address} has gone to sleep.")
                bot.send_discord_message("ESP32 - Sleep Mode", f"The ESP32 {mac_address} is now asleep 💤", bot.MQTT_STATUS_CHECK_WEBHOOK_URL)

            except Exception as error:
                logging.error(f"[on_message] Error processing message: {error}")
        else:
            logging.error(f"[on_message] Unexpected message on {topic}: {payload}")
    else:
        logging.error(f"[on_message] Unexpected topic: {topic}, payload: {payload}")
        bot.send_discord_message(f"MQTT General Messages", payload, bot.MQTT_GENERAL_WEBHOOK_URL)


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
def check_and_publish_sleep(client):
    sleep_sent = False
    
    while True:
        current_time = datetime.datetime.now().time()

        if current_time < datetime.time(8, 0) or current_time > datetime.time(20, 0):
            if not sleep_sent:
                wake_up_time = datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0))
                if current_time > datetime.time(20, 0):
                    wake_up_time += datetime.timedelta(days=1)
                sleep_duration = (wake_up_time - datetime.datetime.now()).total_seconds()
                # Publish sleep duration as string
                client.publish(TOPIC_SLEEP, str(int(sleep_duration)))
                sleep_sent = True
                logging.info(f"Going to sleep for {sleep_duration} seconds.")
            current_datetime = datetime.datetime.now()
            target_time = datetime.datetime.combine(current_datetime.date(), datetime.time(8, 0))
            if current_datetime.time() > datetime.time(8, 0):
                target_time += datetime.timedelta(days=1)
            sleep_time = (target_time - current_datetime).total_seconds()
            time.sleep(sleep_time)
            sleep_sent = False
        else:
            time.sleep(60)


        
@config.handle_error
def check_alive_devices(client):
    config_folder = "Config"
    esp_file_path = os.path.join(config_folder, "esp.json")

    while True:
        current_time = datetime.datetime.now()
        next_hour = (current_time.replace(second=0, microsecond=0) + datetime.timedelta(hours=1)).replace(minute=0)
        time_until_next_hour = (next_hour - current_time).total_seconds()
        time.sleep(time_until_next_hour)

        client.publish(TOPIC_SENSOR_CHECK, "ping")

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
                            bot.send_discord_message("ESP32 - Status Check", f"The ESP32 {mac_address} is offline", bot.MQTT_STATUS_CHECK_WEBHOOK_URL, 0xFF0000)
                            config.add_esp_rpi_json(mac_address, "Off", "esp")
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON line: {line}")
        else:
            logging.warning(f"File '{esp_file_path}' does not exist.")



@config.handle_error
def start_threads():
    client = establish_connection()

    thread_check = threading.Thread(target=check_alive_devices, args=(client,))
    thread_check.start()
    
    thread_sleep = threading.Thread(target=check_and_publish_sleep, args=(client,))
    thread_sleep.start()


@config.handle_error
def run():
    start_threads()


if __name__ == "__main__":
    run()