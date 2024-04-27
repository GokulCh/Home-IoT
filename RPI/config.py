import os
import json
import logging
import datetime
from functools import wraps

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
def create_empty_json_files():
    "Create empty JSON files for RPI, ESP, and data"
    config_folder = "Config"
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)

    file_names = ["rpi.json", "esp.json", "data.json"]
    for file_name in file_names:
        file_path = os.path.join(config_folder, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                file.write("\n")


@handle_error
def add_data_json(data):
    """Add data to a JSON file"""
    config_folder = "Config"
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)

    file_path = os.path.join(config_folder, "data.json")

    timestamp = str(datetime.datetime.now())
    data["timestamp"] = timestamp

    with open(file_path, "a+") as file:
        json.dump(data, file)
        file.write("\n")


@handle_error
def add_esp_rpi_json(mac_address, status, filename):
    """Add data to a JSON file"""
    config_folder = "Config"
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    file_path = os.path.join(config_folder, filename + ".json")
    timestamp = str(datetime.datetime.now())
    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                try:
                    entry = json.loads(line)
                    existing_data.append(entry)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON line: {line}")
    mac_exists = False
    for entry in existing_data:
        if entry["mac_address"] == mac_address:
            if status == "On":
                entry.update({"status": status, "time": timestamp})
            else:
                entry.update({"status": status})
            mac_exists = True
            break
    if not mac_exists:
        data = {
            "mac_address": mac_address,
            "status": status,
            "time": timestamp if status == "On" else "",
        }
        existing_data.append(data)
    with open(file_path, "w") as file:
        for entry in existing_data:
            file.write(json.dumps(entry) + "\n")


@handle_error
def run():
    create_empty_json_files()


if __name__ == "__main__":
    run()
