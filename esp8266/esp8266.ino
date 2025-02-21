#include <ESP8266WiFi.h>  //for esp8266
#include <PubSubClient.h>
#include <ModbusMaster.h>
#include "defines.h"
#include <FS.h>
#include <LittleFS.h>
#include <ESP8266WebServer.h>
#include <SoftwareSerial.h>

// ------------------------------------memory functions--------------------------------
void init_fs() {
  if (!LittleFS.begin()) {
    Serial.println("An Error has occurred while mounting LittleFS");
    return;
  }
  Serial.println("LittleFS mounted successfully");
}

void load_index_from_fs() {
  File file = LittleFS.open("/index.txt", "r");
  if (!file || file.size() == 0) {
    write_index = 0;
  } else {
    write_index = file.parseInt();
  }
  file.close();
}

void save_index_to_fs() {
  File file = LittleFS.open("/index.txt", "w");
  if (file) {
    file.println(write_index);
    file.close();
  }
}

void add_string_to_queue(const char* str) {
  char filename[20];
  snprintf(filename, sizeof(filename), "/queue_%d.txt", write_index);

  File file = LittleFS.open(filename, "w");
  if (file) {
    file.println(str);
    file.close();
  } else {
    Serial.printf("Failed to write to file: %s\n", filename);
  }

  write_index = (write_index + 1) % QUEUE_SIZE;
  save_index_to_fs();
}

void print_queue() {
  Serial.println("Queue contents:");
  for (int i = 0; i < QUEUE_SIZE; i++) {
    char filename[20];
    snprintf(filename, sizeof(filename), "/queue_%d.txt", i);

    File file = LittleFS.open(filename, "r");
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
  if (result == node.ku8MBSuccess) {
    DATA[0] = node.getResponseBuffer(0);
    DATA[1] = node.getResponseBuffer(1);
    if (config[3] == "AABBCCDD")
      value = AABBCCDD(DATA[0], DATA[1]);

    int2f int2f_obj;
    int2f_obj.intVal = value;
    flow_meter_value = int2f_obj.f;
    client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
  } else
    client.publish((String(truck_id) + "/flowmeter").c_str(), "العداد غير متصل");
}

void test_reader() {
  if (is_running)
    flow_meter_value += random(0, 3);
  client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
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
  return 0.0; // Ensure a return value
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
      client.publish((String(truck_id) + "/valve_state").c_str(), "جاري الفتح");
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
      client.publish((String(truck_id) + "/valve_state").c_str(), "جاري الغلق");
    }
  }
  digitalWrite(RELAY_CLOSE, LOW);
}

// --------------------------------------wifi function------------------------------
String readFile(const char* path) {
    File file = LittleFS.open(path, "r");
    if (!file) return "";
    String content = file.readString();
    file.close();
    return content;
}

// Function to write values
void writeFile(const char* path, String message) {
    File file = LittleFS.open(path, "w");
    if (file) {
        file.print(message);
        file.close();
    }
}



const char* ap_ssid = "ESP32_AP";    
const char* ap_password = "12345678";


ESP8266WebServer server(80);

void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  unsigned long startAttemptTime = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    Serial.print(".");
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect! Starting AP mode...");
    startAPMode();
    while(1)
    {
        server.handleClient();
    }
  }
}

void startAPMode() {
  WiFi.softAP(ap_ssid, ap_password);
  Serial.println("Access Point Started!");
  Serial.print("AP IP Address: ");
  Serial.println(WiFi.softAPIP());

  server.on("/", handleRoot);
  server.on("/submit", HTTP_POST, handleFormSubmit);
  server.begin();
}

void handleRoot() {
  server.send(200, "text/html",
              "<!DOCTYPE html>"
              "<html>"
              "<head>"
              "<style>"
              "body { "
              "    font-family: Arial, sans-serif; "
              "    text-align: center; "
              "    background-color: #121212; "
              "    color: #ffffff; "
              "    padding: 20px; "
              "    border-radius: 10px; "
              "}"
              "h1 { color: #ffffff; }"
              "form { "
              "    display: inline-block; "
              "    margin-top: 20px; "
              "    background-color: #1e1e1e; "
              "    padding: 20px; "
              "    border-radius: 10px; "
              "    text-align: left; "
              "}"
              "form div {"
              "    margin-bottom: 10px;"
              "}"
              "label {"
              "    display: inline-block;"
              "    width: 120px;"
              "    text-align: right;"
              "    margin-right: 10px;"
              "}"
              "input[type='text'] { "
              "    padding: 10px; "
              "    margin: 5px; "
              "    background-color: #333333; "
              "    color: #ffffff; "
              "    border: 1px solid #555555; "
              "    width: 200px;"
              "}"
              "input[type='submit'] { "
              "    padding: 10px; "
              "    margin: 5px auto; "
              "    display: block; "
              "    background-color: #4CAF50; "
              "    color: white; "
              "    border: none; "
              "    cursor: pointer; "
              "    width: 80%;"
              "    border-radius: 7px;"
              "}"
              "input[type='submit']:hover { "
              "    background-color: #45a049; "
              "}"
              "</style>"
              "</head>"
              "<body>"
              "<h1>HYPER SCADA</h1>"
              "<p>filling system</p>"
              "<form action=\"/submit\" method=\"POST\">"
              "    <div>"
              "        <label for=\"value1\">user name:</label>"
              "        <input type=\"text\" id=\"value1\" name=\"value1\">"
              "    </div>"
              "    <div>"
              "        <label for=\"value2\">password:</label>"
              "        <input type=\"text\" id=\"value2\" name=\"value2\">"
              "    </div>"
              "    <div>"
              "        <label for=\"value3\">mqtt address:</label>"
              "        <input type=\"text\" id=\"value3\" name=\"value3\">"
              "    </div>"
              "    <div>"
              "        <label for=\"value4\">port name:</label>"
              "        <input type=\"text\" id=\"value4\" name=\"value4\">"
              "    </div>"
              "    <input type=\"submit\" value=\"Submit\">"
              "</form>"
              "</body>"
              "</html>");
}

void handleFormSubmit() {
  String usser_name = server.arg("value1");
  String pass = server.arg("value2");
  String mqtt_address = server.arg("value3");
  String port_id = server.arg("value4");
  writeFile("/username.txt", usser_name);
  writeFile("/password.txt", pass);
  writeFile("/mqtt_address.txt", mqtt_address);
  writeFile("/port_id.txt", port_id);

  // Process the values as needed
  Serial.println("Received values:");
  Serial.println("usser_name: " + usser_name);
  Serial.println("pass: " + pass);
  Serial.println("mqtt_address: " + mqtt_address);
  Serial.println("port_id: " + port_id);

  server.send(200, "text/html", "<h1>Values received</h1>");
  ESP.restart();
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
    if (result == node.ku8MBSuccess) {
      required_Quantity = message.toFloat();
      flow_meter_prev_value = flow_meter_value;
      Serial.print("Target quantity set to: ");
      Serial.println(required_Quantity);
      client.publish((String(truck_id) + "/state").c_str(), "filling");
    }
  }

  else if (topicStr == String(truck_id) + "/logdata")
    logdata = message;

  else if (topicStr == String(truck_id) + "/reset")
    ESP.reset();

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
      client.publish((String(truck_id) + "/valve_state").c_str(), "مفتوح");
      Serial.println("Truck started");
    }

    else if (message == "stop") {
      if (force_stop)
        RelayCloseDC(TIME_OPEN_DC + added_time);
      is_running = false;
      client.publish((String(truck_id) + "/valve_state").c_str(), "مغلق");
      Serial.println("Truck stopped");
      logdata += "," + String(flow_meter_value - flow_meter_prev_value);
      add_string_to_queue(logdata.c_str());
      print_queue();
    }
  }

  else if (topicStr == String(truck_id) + "/conf") {
    Serial.print("config set to: ");
    Serial.println(message);
    splitString(message, ',', config, 12);
    updated = false;
  }
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
      client.subscribe((String(truck_id) + "/reset").c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// ---------------------------------app begin---------------------------------------
SoftwareSerial swSerial(RXD2, TXD2); // RX, TX for SoftwareSerial
void setup() {
  Serial.begin(115200);  
  init_fs();
  truck_id = readFile("/port_id.txt");
  ssid = readFile("/username.txt");
  password = readFile("/password.txt");
  mqtt_server = readFile("/mqtt_address.txt");  

  Serial.println(truck_id);
  setup_wifi();
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(RELAY_OPEN, OUTPUT);
  pinMode(RELAY_CLOSE, OUTPUT);
  pinMode(open_putton, INPUT_PULLUP);
  pinMode(close_putton, INPUT_PULLUP);

  client.setServer(mqtt_server.c_str(), mqtt_port);
  client.setCallback(callback);
  load_index_from_fs();

  if (!client.connected()) {
    reconnect();
  }
  while (updated) {
    client.publish((String(truck_id) + "/update").c_str(), "config");
    client.loop();
    delay(1000);
  }

  if (config[0] == "modbus") {
    swSerial.begin(config[1].toInt());
    node.begin(config[4].toInt(), swSerial);
    node.preTransmission(preTransmission);
    node.postTransmission(postTransmission);

    firstCloseTime = config[6].toInt();
    secondCloseTime = config[7].toInt();
    firstCloseLagV = config[8].toInt();
    secondCloseLagV = config[9].toInt();
    thirdCloseTime =  config[10].toInt();
    added_time =  config[11].toInt();
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
  }

  for (int i = 0; i < 12; i++)
    Serial.println("config of " + String(i) + "=\t" + config[i]);
  Serial.println("time_open_dc =\t" + String(TIME_OPEN_DC));
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  if (!digitalRead(open_putton)) {
    RelayOpenDC();
    client.publish((String(truck_id) + "/valve_state").c_str(), "مفتوح");
    while (!digitalRead(open_putton))
      ;
  }
  if (!digitalRead(close_putton)) {
    RelayCloseDC(TIME_OPEN_DC);
    client.publish((String(truck_id) + "/valve_state").c_str(), "مغلق");
    while (!digitalRead(close_putton))
      ;
  }

  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 100) {
    lastPublishTime = millis();
    flowmeter_reader();
    // test_reader();

    if (is_running) {
      client.publish((String(truck_id) + "/valve_state").c_str(), "مفتوح");
      float FlowRate = flow_rate_reader();
      remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value);
      double ExtraWater = (FlowRate / 2.0) * thirdCloseTime / 1000;

      if (remain_Quantity <= float(firstCloseLagV) / 1000 && firstCloseStatus == 0) {
        RelayCloseDC(firstCloseTime);
        firstCloseStatus = 1;
      }

      else if (remain_Quantity <= float(secondCloseLagV) / 1000 && secondCloseStatus == 0) {
        RelayCloseDC(secondCloseTime);
        secondCloseStatus = 1;
      }

      else if (remain_Quantity - ExtraWater / 1000 <= 0 && thirdCloseStatus == 0) {
        RelayCloseDC(thirdCloseTime + added_time);
        thirdCloseStatus = 1;
        force_stop = 0;
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }
    }
  }
}