#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Constants
const char* SSID = "Verizon-RC400L-FA";
const char* WIFI_PASSWORD = "12ff7959";
const char* MQTT_SERVER = "192.168.1.117";
const String SENSOR_NAME = F("house_1");
const String SENSOR_TYPE = F("door");
const String SENSOR_LOC = F("front_door");
const int SENSOR_ID = 1;
const uint16_t MQTT_PORT = 1883;
const int SENSOR_PIN = 5;
const int LED_PIN = 2;

// Global variables
int previousSensorState = HIGH;
WiFiClient espClient;
PubSubClient mqttClient(espClient);
String macAddress;

// Function prototypes
void connectWiFi();
void connectMQTTServer();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void blinkLED(uint8_t times, uint16_t duration);
void publishSensorData(int sensorState);

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);

  if (SENSOR_TYPE.equals("pir")){
    pinMode(23, OUTPUT);
    digitalWrite(23, LOW);
  }
  WiFi.mode(WIFI_STA);
  WiFi.setHostname("ESP32_Sensor");

  connectWiFi();

  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  macAddress = WiFi.macAddress();
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
  WiFi.disconnect();
  WiFi.begin(SSID, WIFI_PASSWORD);
  Serial.print(F("Connecting to WiFi "));
  Serial.println(SSID);

  uint8_t retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 10) {
    blinkLED(2, 200);
    delay(1000);
    Serial.print(F("."));
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(F("\nWiFi connected"));
    Serial.print(F("IP address: "));
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(F("\nFailed to connect to WiFi"));
    ESP.restart();
  }
}

void connectMQTTServer() {
  while (!mqttClient.connected()) {
    if (WiFi.status() != WL_CONNECTED) {
      connectWiFi();
    }

    Serial.print(F("Attempting MQTT connection..."));
    String clientId = "ESP32_" + String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println(F("connected"));
      mqttClient.subscribe("esp32/sensor_check");
      mqttClient.subscribe("esp32/sleep");
    } else {
      Serial.print(F("failed, rc="));
      Serial.print(mqttClient.state());
      Serial.println(F(" trying again in 5 seconds"));
      blinkLED(3, 200);
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print(F("Message arrived ["));
  Serial.print(topic);
  Serial.print(F("] "));

  char messageTemp[length + 1];
  memcpy(messageTemp, payload, length);
  messageTemp[length] = '\0';
  Serial.println(messageTemp);

  if (String(topic) == "esp32/sensor_check") {
    String pongTopic = "esp32/sensor_check/" + macAddress;
    mqttClient.publish(pongTopic.c_str(), "pong");
  }

  if (String(topic) == "esp32/sleep") {
    String pongTopic = "esp32/sleep/" + macAddress;
    mqttClient.publish(pongTopic.c_str(), "slept");
    Serial.print(F("Sleep for: "));
    Serial.println(messageTemp);

    long sleepDuration = atol(messageTemp);
    ESP.deepSleep(sleepDuration * 1e6);
  }
}

void blinkLED(uint8_t times, uint16_t duration) {
  for (uint8_t i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(duration);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void publishSensorData(int sensorState) {
  StaticJsonDocument<256> doc;
  doc["mac_address"] = macAddress;
  doc["sensor_name"] = SENSOR_NAME;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["sensor_loc"] = SENSOR_LOC;
  doc["sensor_id"] = SENSOR_ID;

  if (sensorState == LOW) {
    Serial.println(F("Sensor triggered!"));
    doc["event"] = "triggered";
  } else {
    Serial.println(F("Sensor released!"));
    doc["event"] = "released";
  }

  char buffer[256];
  size_t n = serializeJson(doc, buffer, sizeof(buffer));
  String dataTopic = "esp32/sensor_data/" + macAddress;
  mqttClient.publish(dataTopic.c_str(), buffer, n);
}