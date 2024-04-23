# Home IOT System

This project, named "Home-IoT", is a comprehensive home Internet of Things (IoT) system designed to run on a Raspberry Pi. It integrates with Discord, MongoDB, and MQTT, providing a robust and interactive platform for home automation.

The project is structured into several key components:

- Discord Bot: The Discord bot is implemented in bot.py. It uses the discord.py library to communicate with various channels on a Discord server. The bot token and channel IDs are defined in this file. This bot serves as the main interface for users to interact with the home IoT system.

- MongoDB Integration: The MongoDB integration is handled by mongodb.py. This script manages the connection and data transfer to a MongoDB database, which is used for storing and retrieving data related to the IoT system.

- MQTT Broker: The MQTT broker is implemented in mqtt_broker.py. It manages the communication with IoT devices using the MQTT protocol. Data received from the devices is appended to the data.json file, providing a log of device activity.

- Main Script: The main script is main.py. It imports the Discord bot, MongoDB, and MQTT broker scripts and runs them asynchronously. This script serves as the entry point for running the entire home IoT system.

- Arduino Sensor: The Arduino sensor code is located in sensor.ino. This script reads data from a sensor and sends it to the MQTT broker, allowing the system to collect and process sensor data.

> The project also includes a .gitignore file that specifies files and directories that Git should ignore, including the __pycache__ directory within the RPI/ directory.

> The MQTT broker's configuration can be adjusted in the mosquitto.conf file, allowing for customization of the MQTT communication settings.
## Installation

Install the dependencies.
```python
pip install pymongo
pip install paho-mqtt
pip install discord.py
```
