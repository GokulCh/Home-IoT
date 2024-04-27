import logging
from functools import wraps
import requests
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1233482610890637492/UeVrwTyfGU4h9zCXSsWINutB0wvkAMGEyuuuIpJYYVjtjbraXixgIvAakmy0VqCBolIU"
MQTT_DATA_WEBHOOL_URL = "https://discord.com/api/webhooks/1233573861493047406/ATt5Y2bpWeS72ivKQvolFKo72l-ZPaNk3SbtoTBtTroRL12h0ZqBB_nE9RJSl97MPOvY"
MQTT_CONNECTED_WEBHOOK_URL = "https://discord.com/api/webhooks/1233520406594584640/lFJs1xKpUEzYv5hyiZYzmkMJ_J5vZN2QCEF0hx8g4OL0vOm7c4f0RLj6tE9utZz_RdGn"
MQTT_DISCONNECTED_WEBHOOK_URL = "https://discord.com/api/webhooks/1233520625172348938/D8UY5h2OsrbkYYwtguz466RKbo9LSeq4UQDNgXFu0R_AMwbp82XmrXMaiqGjZwycO86a"

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
def send_discord_message(title, message, url, color=0x99E550):
    embed = {
        "title": title,
        "description": message,
        "color": color
    }
    payload = {
        "embeds": [embed]
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Discord message: {e}")