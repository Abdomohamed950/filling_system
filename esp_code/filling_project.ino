#include <WiFi.h>  //for esp32
// #include <ESP8266WiFi.h>  //for esp8266
#include <PubSubClient.h>
#include <ModbusMaster.h>
#include "defines.h"
#include <FS.h>
#include <SPIFFS.h>
// #include <LittleFS.h>
// #define SPIFFS LittleFS



// ------------------------------------memory functions--------------------------------
void init_spiffs() {
  if (!SPIFFS.begin(true)) {
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
  Serial.println("SPIFFS mounted successfully");
}

void load_index_from_spiffs() {
  File file = SPIFFS.open("/index.txt", "r");
  if (!file || file.size() == 0) {
    write_index = 0;
  } else {
    write_index = file.parseInt();
  }
  file.close();
}

void save_index_to_spiffs() {
  File file = SPIFFS.open("/index.txt", "w");
  if (file) {
    file.println(write_index);
    file.close();
  }
}

void add_string_to_queue(const char* str) {

  char filename[20];
  snprintf(filename, sizeof(filename), "/queue_%d.txt", write_index);

  File file = SPIFFS.open(filename, "w");
  if (file) {
    file.println(str);
    file.close();
  } else {
    Serial.printf("Failed to write to file: %s\n", filename);
  }

  write_index = (write_index + 1) % QUEUE_SIZE;
  save_index_to_spiffs();
}

void print_queue() {
  Serial.println("Queue contents:");
  for (int i = 0; i < QUEUE_SIZE; i++) {
    char filename[20];
    snprintf(filename, sizeof(filename), "/queue_%d.txt", i);

    File file = SPIFFS.open(filename, "r");
    if (file) {
      String content = file.readStringUntil('\n');
      Serial.printf("Index %d: %s\n", i, content.c_str());
      file.close();
    } else {
      Serial.printf("Index %d: (empty)\n", i);
    }
  }
}








// ------------------------------modbus functions------------------------------------
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
  // Serial.print("result = ");
  // Serial.println(result);

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
}



// ------------------------------------valve functions-------------------------------
void RelayOpenDC(void) {
  digitalWrite(RELAY_CLOSE, LOW);
  digitalWrite(RELAY_OPEN, HIGH);
  long td = millis();
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
  long td = millis();
  while ((millis() - td < closeTime)) {
    static unsigned long lasst = 0;
    if (millis() - lasst > 100) {
      lasst = millis();
      flowmeter_reader();
      client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
    }
  }
  digitalWrite(RELAY_CLOSE, LOW);
}





// --------------------------------------wifi function------------------------------
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password, 0, nullptr, true);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}




// ---------------------------------mqtt functions-------------------------------------
void callback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);
  String message = "";

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message received on topic: ");
  Serial.print(topicStr);
  Serial.print(". Message: ");
  Serial.println(message);

  if (topicStr == String(truck_id) + "/quantity") {

    required_Quantity = message.toInt();
    flow_meter_prev_value = flow_meter_value;
    Serial.print("Target quantity set to: ");
    Serial.println(required_Quantity);
    client.publish((String(truck_id) + "/state").c_str(), "filling");

  }

  else if (topicStr == String(truck_id) + "/logdata")
    logdata = message;

  else if (topicStr == String(truck_id) + "/state") {

    Serial.print("message set to: ");
    Serial.println(message);
    if (message == "start") {
      is_running = true;
      force_stop = 1;
      firstCloseStatus = 0;
      secondCloseStatus = 0;
      thirdCloseStatus = 0;
      RelayOpenDC();
      Serial.println("Truck started");
    }

    else if (message == "stop") {
      if (is_running) {
        if (force_stop)
          RelayCloseDC(TIME_OPEN_DC);
        is_running = false;
        Serial.println("Truck stopped");
        logdata += "," + String(flow_meter_value - flow_meter_prev_value);
        add_string_to_queue(logdata.c_str());
        print_queue();
      }
    }
  }

  //under tested
  else if (topicStr == String(truck_id) + "/conf") {
    Serial.print("config set to: ");
    Serial.println(message);
    splitString(message, ',', config, 10);
    updated = false;
  }

  // end of under tested
}

void splitString(const String& str, char delimiter, String result[], int maxParts) {
  int currentIndex = 0;
  int startIndex = 0;
  int endIndex = str.indexOf(delimiter);

  while (endIndex >= 0 && currentIndex < maxParts - 1) {
    result[currentIndex++] = str.substring(startIndex, endIndex);
    startIndex = endIndex + 1;
    endIndex = str.indexOf(delimiter, startIndex);
  }
  result[currentIndex] = str.substring(startIndex);
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect((String("ESPTruckClient_") + truck_id).c_str())) {
      Serial.println("connected");
      client.subscribe((String(truck_id) + "/quantity").c_str());
      client.subscribe((String(truck_id) + "/state").c_str());
      client.subscribe((String(truck_id) + "/refresh").c_str());
      client.subscribe((String(truck_id) + "/logdata").c_str());
      client.subscribe((String(truck_id) + "/conf").c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}








// ---------------------------------app begin---------------------------------------
void setup() {
  Serial.begin(115200);
  setup_wifi();
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(RELAY_OPEN, OUTPUT);
  pinMode(RELAY_CLOSE, OUTPUT);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  init_spiffs();
  load_index_from_spiffs();

  //under test
  if (!client.connected()) {
    reconnect();
  }
  while (updated) {
    client.publish((String(truck_id) + "/update").c_str(), "config");
    client.loop();
    delay(1000);
  }
  // end of under test

  if (config[0] == "modbus") {
    int frame;
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

    // إعدادات Modbus
    pinMode(MAX485_RE_NEG, OUTPUT);
    pinMode(MAX485_DE, OUTPUT);
    postTransmission();
    Serial2.begin(config[1].toInt(), frame, RXD2, TXD2);
    node.begin(config[4].toInt(), Serial2);
    node.preTransmission(preTransmission);
    node.postTransmission(postTransmission);

    firstCloseTime = config[6].toInt();
    secondCloseTime = config[7].toInt();
    firstCloseLagV = config[8].toInt();
    secondCloseLagV = config[9].toInt();
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
  }

  for (int i = 0; i < 10; i++) 
    Serial.println("config of " + String(i) + "=\t"+config[i]);
  Serial.println("time_open_dc =\t"+String(TIME_OPEN_DC));
  
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
    // Serial.println(flow_meter_value);
    client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());

    if (is_running && result == node.ku8MBSuccess) {
      float FlowRate = flow_rate_reader();
      remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value);
      double ExtraWater = (FlowRate / 2.0) * thirdCloseTime;

      if (remain_Quantity <= firstCloseLagV && firstCloseStatus == 0) {
        RelayCloseDC(firstCloseTime);
        firstCloseStatus = 1;
      }

      else if (remain_Quantity <= secondCloseLagV && secondCloseStatus == 0) {
        RelayCloseDC(secondCloseTime);
        secondCloseStatus = 1;
      }

      else if (remain_Quantity-ExtraWater <= 0 && thirdCloseStatus == 0) {
        RelayCloseDC(thirdCloseTime);
        thirdCloseStatus = 1;
        force_stop = 0;
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }

    }
  }
}
