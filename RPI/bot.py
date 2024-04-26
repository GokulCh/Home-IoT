import logging
from functools import wraps
import requests
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1233482610890637492/UeVrwTyfGU4h9zCXSsWINutB0wvkAMGEyuuuIpJYYVjtjbraXixgIvAakmy0VqCBolIU"
MQTT_WEBHOOK_URL = "https://discord.com/api/webhooks/1233517061129637908/wUtbwtUSwGIanNhT2lfvj9Z4iNKEOy42ruFMjGxP79nWBi1rUrWCWjVcl1XZn5sfrjJv"

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
def send_discord_message(title, message, url):
    embed = {
        "title": title,
        "description": message,
        "color": 0x99E550
    }
    payload = {
        "embeds": [embed]
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Discord message: {e}")