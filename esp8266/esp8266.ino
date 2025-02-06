#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ModbusMaster.h>
#include "defines.h"

// ------------------------------ modbus ------------------------------
uint32_t AABBCCDD(uint16_t firstRecv, uint16_t secondRecv) {
  uint8_t u1_right = firstRecv & 0x00ff;
  uint8_t u1_left = firstRecv >> 8;
  uint8_t u2_right = secondRecv & 0x00ff;
  uint8_t u2_left = secondRecv >> 8;
  return (((uint32_t)u2_right << 24) | ((uint32_t)u2_left << 16) | ((uint32_t)u1_right << 8) | (uint32_t)u1_left);
}

void preTransmission() {
  digitalWrite(MAX485_RE_NEG, HIGH);
  digitalWrite(MAX485_DE, HIGH);
}

void postTransmission() {
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);
}

void flowmeter_reader() {
  uint32_t value;
  result = node.readHoldingRegisters(config[5].toInt(), REG_IN_ROW);
  if (result == node.ku8MBSuccess) {
    DATA[0] = node.getResponseBuffer(0);
    DATA[1] = node.getResponseBuffer(1);
    if (config[3] == "AABBCCDD")
      value = AABBCCDD(DATA[0], DATA[1]);
    int2f int2f_obj;
    int2f_obj.intVal = value;
    flow_meter_value = int2f_obj.f;
  }
}

float flow_rate_reader() {
  uint32_t value;
  result = node.readHoldingRegisters(1999, REG_IN_ROW);
  if (result == node.ku8MBSuccess) {
    DATA[0] = node.getResponseBuffer(0);
    DATA[1] = node.getResponseBuffer(1);
    if (config[3] == "AABBCCDD")
      value = AABBCCDD(DATA[0], DATA[1]);
    int2f int2f_obj;
    int2f_obj.intVal = value;
    return int2f_obj.f;
  }
  return 0;
}

// ------------------------------ valve ------------------------------
void RelayOpenDC(void) {
  digitalWrite(RELAY_CLOSE, LOW);
  digitalWrite(RELAY_OPEN, HIGH);
  unsigned long td = millis();
  while ((millis() - td < TIME_OPEN_DC)) {
    static unsigned long last = 0;
    if (millis() - last > 100) {
      last = millis();
      flowmeter_reader();
      client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
      client.loop();
    }
  }
  digitalWrite(RELAY_OPEN, LOW);
}

void RelayCloseDC(uint32_t closeTime) {
  digitalWrite(RELAY_OPEN, LOW);
  digitalWrite(RELAY_CLOSE, HIGH);
  unsigned long td = millis();
  while ((millis() - td < closeTime)) {
    static unsigned long last = 0;
    if (millis() - last > 100) {
      last = millis();
      flowmeter_reader();
      client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
    }
  }
  digitalWrite(RELAY_CLOSE, LOW);
}

// ------------------------------ wifi ------------------------------
void setup_wifi() {
  WiFi.begin(ssid, password, 0, nullptr, true);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

// ------------------------------  MQTT ------------------------------
void callback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (topicStr == String(truck_id) + "/quantity") {
    required_Quantity = message.toFloat();
    flow_meter_prev_value = flow_meter_value;
    client.publish((String(truck_id) + "/state").c_str(), "filling");
  } else if (topicStr == String(truck_id) + "/logdata") {
    logdata = message;
  } else if (topicStr == String(truck_id) + "/state") {
    if (message == "start") {
      is_running = true;
      force_stop = 1;
      firstCloseStatus = 0;
      secondCloseStatus = 0;
      thirdCloseStatus = 0;
      RelayOpenDC();
    } else if (message == "stop") {
      if (is_running) {
        if (force_stop)
          RelayCloseDC(TIME_OPEN_DC);
        is_running = false;
        logdata += "," + String(flow_meter_value - flow_meter_prev_value);
      }
    }
  } else if (topicStr == String(truck_id) + "/conf") {
    int currentIndex = 0;
    int startIndex = 0;
    int endIndex = message.indexOf(',');
    while (endIndex >= 0 && currentIndex < 9) {
      config[currentIndex++] = message.substring(startIndex, endIndex);
      startIndex = endIndex + 1;
      endIndex = message.indexOf(',', startIndex);
    }
    config[currentIndex] = message.substring(startIndex);
    updated = false;
  }
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect((String("ESPTruckClient_") + truck_id).c_str())) {
      client.subscribe((String(truck_id) + "/quantity").c_str());
      client.subscribe((String(truck_id) + "/state").c_str());
      client.subscribe((String(truck_id) + "/refresh").c_str());
      client.subscribe((String(truck_id) + "/logdata").c_str());
      client.subscribe((String(truck_id) + "/conf").c_str());
    } else {
      delay(5000);
    }
  }
}

// ------------------------------ الدوال الرئيسية ------------------------------
void setup() {
  Serial.begin(115200);

  setup_wifi();

  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(RELAY_OPEN, OUTPUT);
  pinMode(RELAY_CLOSE, OUTPUT);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  if (!client.connected()) {
    reconnect();
  }

  while (updated) {
    client.publish((String(truck_id) + "/update").c_str(), "config");
    client.loop();
    delay(1000);
  }

  if (config[0] == "modbus") {
    SerialConfig frame;
    if (config[2] == "SERIAL_8N1")
      frame = SERIAL_8N1;
    else if (config[2] == "SERIAL_8N2")
      frame = SERIAL_8N2;
    else if (config[2] == "SERIAL_8O1")
      frame = SERIAL_8O1;
    else if (config[2] == "SERIAL_8O2")
      frame = SERIAL_8O2;
    else if (config[2] == "SERIAL_8E1")
      frame = SERIAL_8E1;
    else if (config[2] == "SERIAL_8E2")
      frame = SERIAL_8E2;

    pinMode(MAX485_RE_NEG, OUTPUT);
    pinMode(MAX485_DE, OUTPUT);
    postTransmission();

    Serial.begin(config[1].toInt(), frame);
    node.begin(config[4].toInt(), Serial);
    node.preTransmission(preTransmission);
    node.postTransmission(postTransmission);

    firstCloseTime = config[6].toInt();
    secondCloseTime = config[7].toInt();
    firstCloseLagV = config[8].toInt();
    secondCloseLagV = config[9].toInt();
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 100) {
    lastPublishTime = millis();
    flowmeter_reader();
    client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
    if (is_running && result == node.ku8MBSuccess) {
      float FlowRate = flow_rate_reader();
      remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value);
      double ExtraWater = (FlowRate / 2.0) * thirdCloseTime;
      if (remain_Quantity <= float(firstCloseLagV) / 1000 && firstCloseStatus == 0) {
        RelayCloseDC(firstCloseTime);
        firstCloseStatus = 1;
      } else if (remain_Quantity <= float(secondCloseLagV) / 1000 && secondCloseStatus == 0) {
        RelayCloseDC(secondCloseTime);
        secondCloseStatus = 1;
      } else if (remain_Quantity - ExtraWater / 1000 <= 0 && thirdCloseStatus == 0) {
        RelayCloseDC(thirdCloseTime);
        thirdCloseStatus = 1;
        force_stop = 0;
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }
    }
  }
}
