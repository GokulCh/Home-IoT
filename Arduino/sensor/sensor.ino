#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Constants
const int SENSOR_PIN = 5;
const char* SSID = "Gokul Ch";
const char* WIFI_PASSWORD = "somepassword";
const char* MQTT_SERVER = "172.20.10.2";
const String SENSOR_NAME = "house_1";
const String SENSOR_TYPE = "door_1";
const uint16_t MQTT_PORT = 1883;
#define LED_PIN 2

// Global variables
int previousSensorState = HIGH;
WiFiClient espClient;
PubSubClient mqttClient(espClient);
String macAddress;

// Function prototypes
void connectWiFi();
void connectMQTTServer();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void blinkLED(unsigned int times, unsigned int duration);
void publishSensorData(int sensorState);

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);

  macAddress = WiFi.macAddress();
  connectWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (!mqttClient.connected()) {
    connectMQTTServer();
  }

  mqttClient.loop();

  int sensorState = digitalRead(SENSOR_PIN);

  if (sensorState != previousSensorState) {
    publishSensorData(sensorState);
    previousSensorState = sensorState;
  }
}

void connectWiFi() {
  WiFi.begin(SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi ");
  Serial.println(SSID);

  uint8_t retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 10) {
    blinkLED(2, 200);
    delay(1000);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi");
    ESP.restart();
  }
}

void connectMQTTServer() {
  while (!mqttClient.connected()) {
    if (WiFi.status() != WL_CONNECTED) {
      connectWiFi();
    }

    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32_" + String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      mqttClient.subscribe("esp32/sensor_check");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" trying again in 5 seconds");
      blinkLED(3, 200);
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");

    String messageTemp;
    for (unsigned int i = 0; i < length; i++) {
        Serial.print((char)payload[i]);
        messageTemp += (char)payload[i];
    }
    Serial.println();

    if (String(topic) == "esp32/sensor_check") {
        String pongTopic = "esp32/sensor_check/" + macAddress;
        mqttClient.publish(pongTopic.c_str(), "pong");
    }
}

void blinkLED(unsigned int times, unsigned int duration) {
  for (unsigned int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(duration);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void publishSensorData(int sensorState) {
  StaticJsonDocument<256> doc;
  doc["sensor_name"] = SENSOR_NAME;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["mac_address"] = macAddress;

  if (sensorState == LOW) {
    Serial.println("Sensor triggered!");
    doc["event"] = "triggered";
  } else {
    Serial.println("Sensor released!");
    doc["event"] = "released";
  }

  char buffer[256];
  size_t n = serializeJson(doc, buffer);
  mqttClient.publish("esp32/sensor_data", buffer, n);
}