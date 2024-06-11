import logging
from functools import wraps
import datetime
import requests
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebhookURLs:
    def __init__(self, urls):
        self.urls = urls
    
    def getTitle(self, key):
        return self.urls[key][0]

    def getUrl(self, key):
        return self.urls[key][1]

webhook_urls = {
    "mqtt_messages_sent": ["MQTT | Messages Sent", "https://discord.com/api/webhooks/1235229793960591370/BEk99ZhDcJD4fWd9-J7Y16mFiqEs5XccPcJxSgamQJDX882w_DDy_p63T1ikPWxsuXTv"],
    "mqtt_messages_received": ["MQTT | Messages Received", "https://discord.com/api/webhooks/1235054880960544819/g4ZhSroAchmgFaNuUtKUofchKLRLvQjeCjmD3Dn8NUJ9KYQ48nDA8P8O-zBbnMTOBQPh"],
    "mqtt_data_received": ["MQTT | Data Received", "https://discord.com/api/webhooks/1233573861493047406/ATt5Y2bpWeS72ivKQvolFKo72l-ZPaNk3SbtoTBtTroRL12h0ZqBB_nE9RJSl97MPOvY"],
    "mqtt_rpi_connection": ["MQTT | RPI Connection", "https://discord.com/api/webhooks/1233520406594584640/lFJs1xKpUEzYv5hyiZYzmkMJ_J5vZN2QCEF0hx8g4OL0vOm7c4f0RLj6tE9utZz_RdGn"],
    "esp32_messages_sent": ["ESP32 | Messages Sent", "https://discord.com/api/webhooks/1235232509457858601/1hrChlxW_BFwBnqijcpvuGBLahU35v0KzgWZnBBCSdmSS5o4_jI_uTt53YbjX5YZiKsb"],
    "esp32_messages_received": ["ESP32 | Messages Received", "https://discord.com/api/webhooks/1235232594157768808/om9Tr8aID9cTbIfWNkrBv9hMiWBOEjvmxCiYGunm8zAztwzufqm6tzs4wLWsIa8xqQch"],
    "esp32_connection": ["ESP32 | Connection", "https://discord.com/api/webhooks/1233517061129637908/wUtbwtUSwGIanNhT2lfvj9Z4iNKEOy42ruFMjGxP79nWBi1rUrWCWjVcl1XZn5sfrjJv"],
    "esp32_overview": ["ESP32 | Overview", "https://discord.com/api/webhooks/1238625610302230569/7GIkCHCkuPNJs23i1OjrMHWDSYNfLfq0Or_ohJxVXQvcXCrb_23NsxTxv9HpFyHSIR3P"],
}

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
def send_discord_message(title, description, color=0x99E550):
    """Send a message to a Discord webhook"""
    webhook_manager = WebhookURLs(webhook_urls)
    get_title = webhook_manager.getTitle(title)
    get_url = webhook_manager.getUrl(title)
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = {"text": f"Timestamp: {current_time}"}
    
    embed = {"title": get_title, "description": description, "color": color}
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(get_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Discord message: {e}")