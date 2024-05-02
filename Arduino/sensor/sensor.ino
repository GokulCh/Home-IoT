#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Constants
const char* SSID = "rpi";
const char* WIFI_PASSWORD = "somepassword";
const char* MQTT_SERVER = "10.42.0.1";
const String SENSOR_NAME = F("house_1");
const String SENSOR_TYPE = F("door_1");
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

  WiFi.mode(WIFI_STA);
  WiFi.setHostname("ESP32_Sensor");
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

  delay(30000);
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
  doc["sensor_name"] = SENSOR_NAME;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["mac_address"] = macAddress;

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