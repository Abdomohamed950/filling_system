#include <ESP8266WiFi.h>  //for esp8266
#include <PubSubClient.h>
#include <ModbusMaster.h>
#include <FS.h>
#include <LittleFS.h>
#include <ESP8266WebServer.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <Encoder.h>
#include "defines.h"


// ------------------------------------memory functions--------------------------------


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
  for (int i = 0; i < QUEUE_SIZE; i++) {
    char filename[20];
    snprintf(filename, sizeof(filename), "/queue_%d.txt", i);

    File file = LittleFS.open(filename, "r");
    if (file) {
      String content = file.readStringUntil('\n');
      file.close();
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
    if (!offline)
      client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());
  } else {
    if (!offline)
      client.publish((String(truck_id) + "/flowmeter").c_str(), "العداد غير متصل");
  }
}

void test_reader() {
  if (is_running)
    flow_meter_value += random(0, 3);
  if (!offline)
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
  return 0.0;  // Ensure a return value
}

// ------------------------------------valve functions-------------------------------
void RelayOpenDC(void) {  
  digitalWrite(RELAY_CLOSE, LOW);
  digitalWrite(RELAY_OPEN, HIGH);
  unsigned long td = millis();
  while ((millis() - td < TIME_OPEN_DC)) {
    ESP.wdtFeed();
    yield();
    if (offline)
      scroll();
    static unsigned long last = 0;
    if (millis() - last > 100) {
      last = millis();
      flowmeter_reader();
      if (!offline)
        client.publish((String(truck_id) + "/valve_state").c_str(), "جاري الفتح");
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
    ESP.wdtFeed();
    yield();
    if (offline)
      scroll();
    static unsigned long lasst = 0;
    if (millis() - lasst > 100) {
      lasst = millis();
      flowmeter_reader();
      if (!offline)
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
  WiFi.begin(ssid, password);
  unsigned long startAttemptTime = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
    lcd(15, "connected to " + String(ssid));
  } else {
    startAPMode();
    while (1) {
      server.handleClient();
    }
  }
}

void startAPMode() {
  WiFi.softAP(ap_ssid, ap_password);

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


  if (topicStr == String(truck_id) + "/quantity") {
    required_Quantity = message.toFloat();
    flow_meter_prev_value = flow_meter_value;
    client.publish((String(truck_id) + "/state").c_str(), "filling");
  }

  else if (topicStr == String(truck_id) + "/logdata")
    logdata = message;

  else if (topicStr == String(truck_id) + "/reset")
    ESP.restart();

  else if (topicStr == String(truck_id) + "/state") {
    if (message == "start") {
      is_running = true;
      force_stop = 1;
      firstCloseStatus = 0;
      secondCloseStatus = 0;
      thirdCloseStatus = 0;
      RelayOpenDC();
      client.publish((String(truck_id) + "/valve_state").c_str(), "مفتوح");
    }

    else if (message == "stop") {
      if (force_stop)
        RelayCloseDC(TIME_OPEN_DC + added_time);
      is_running = false;
      client.publish((String(truck_id) + "/valve_state").c_str(), "مغلق");
      logdata += "," + String(flow_meter_value - flow_meter_prev_value);
      add_string_to_queue(logdata.c_str());
      print_queue();
    }
  }

  else if (topicStr == String(truck_id) + "/conf") {
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
    if (client.connect((String("ESPTruckClient_") + truck_id).c_str())) {
      client.subscribe((String(truck_id) + "/quantity").c_str());
      client.subscribe((String(truck_id) + "/state").c_str());
      client.subscribe((String(truck_id) + "/refresh").c_str());
      client.subscribe((String(truck_id) + "/logdata").c_str());
      client.subscribe((String(truck_id) + "/conf").c_str());
      client.subscribe((String(truck_id) + "/reset").c_str());
    } else {
      delay(5000);
    }
  }
}



// ------------------------------------lcd----------------------------------------
bool isBold[3] = { false, false, false };

void drawMenu() {
  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x12_tf);
  u8g2.setCursor(90, 15);
  u8g2.print("[");
  u8g2.print(flow_meter_value);
  u8g2.print("]");

  // **Quantity Row**
  u8g2.setFont(isBold[0] ? u8g2_font_6x13B_tf : u8g2_font_6x12_tf);
  u8g2.setCursor(5, 15);
  if (currentMenuIndex == 0) u8g2.print("> ");
  u8g2.print("Quantity: ");
  u8g2.print(quantity);

  // **Start Row**
  u8g2.setFont(isBold[1] ? u8g2_font_6x13B_tf : u8g2_font_6x12_tf);
  u8g2.setCursor(5, 30);
  if (currentMenuIndex == 1) u8g2.print("> ");
  u8g2.print("Start");

  // **Stop Row**
  u8g2.setFont(isBold[2] ? u8g2_font_6x13B_tf : u8g2_font_6x12_tf);
  u8g2.setCursor(5, 45);
  if (currentMenuIndex == 2) u8g2.print("> ");
  u8g2.print("Stop");

  drawProgressBar();
  u8g2.sendBuffer();
}

void scroll() {
  int newEncoderPos = myEnc.read() / 4;

  if (newEncoderPos != lastEncoderPos) {
    if (editingQuantity) {
      quantity += (newEncoderPos > lastEncoderPos) ? 1 : -1;
      if (quantity < 0) quantity = 0;
    } else {

      currentMenuIndex += (newEncoderPos > lastEncoderPos) ? 1 : -1;
      if (currentMenuIndex < 0) currentMenuIndex = 0;
      if (currentMenuIndex > 2) currentMenuIndex = 2;
    }
    lastEncoderPos = newEncoderPos;
  }

  if (digitalRead(ENCODER_BUTTON) == HIGH) {
    delay(200);

    if (currentMenuIndex == 0) {
      editingQuantity = !editingQuantity;
      isBold[0] = editingQuantity;
    } else {
      isBold[currentMenuIndex] = !isBold[currentMenuIndex];

      if (currentMenuIndex == 1 && isBold[1]) startFunction();
      if (currentMenuIndex == 2 && isBold[2]) stopFunction();
    }
  }

  drawMenu();
}



void lcd(int pos, String s) {
  // u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_6x12_tf);
  u8g2.setCursor(5, pos);
  u8g2.print(s);
  u8g2.sendBuffer();
}




void drawProgressBar() {
  u8g2.drawFrame(5, 55, 118, 8);
  u8g2.drawBox(5, 55, progressBar, 8);
}




void startFunction() {
  progressBar = 0;
  is_running = 1;
  firstCloseStatus = 0;
  secondCloseStatus = 0;
  thirdCloseStatus = 0;
  flow_meter_prev_value = flow_meter_value;
  required_Quantity = quantity;
  RelayOpenDC();
}

// دالة الإيقاف
void stopFunction() {
  is_running = 0;
  RelayCloseDC(firstCloseTime + secondCloseTime + thirdCloseTime + added_time);
  isBold[1] = 0;
  isBold[2] = 0;
}



void if_long_press() {

  if (digitalRead(ENCODER_BUTTON) == HIGH) {
    if (!isButtonPressed) {
      pressStartTime = millis();
      isButtonPressed = true;
    }
  } else {
    if (isButtonPressed) {
      unsigned long pressDuration = millis() - pressStartTime;

      if (pressDuration > 5000) {
        lcd(45, "config page");
        startAPMode();
        while (1) {
          server.handleClient();
        }
      }
    }
  }
}






//-----------------------------------------------------------------------------------------------------------------------------------------------




void measureWaterFlow() {
  int samples = 10;    // عدد القراءات لأخذ متوسط
  float adcSum = 0.0;  // مجموع القراءات من المستشعر
  float adcMean, mV, current_mA, flowRate;

  // أخذ عدة قراءات لحساب المتوسط
  for (int i = 0; i < samples; i++) {
    adcSum += analogRead(FLOW_SENSOR_PIN);
    delayMicroseconds(100);  // تأخير بسيط بين القراءات
  }

  // حساب متوسط القراءة من ADC
  adcMean = adcSum / samples;

  // تحويل القراءة الرقمية إلى جهد (mV)
  mV = (adcMean / ADC_RESOLUTION) * V_REF;

  // حساب التيار المار في المستشعر بناءً على قيمة المقاومة
  current_mA = mV / RESISTANCE_OHM;

  // التأكد من أن التيار لا يقل عن 4mA
  current_mA = (current_mA >= MIN_MA) ? current_mA : MIN_MA;

  // تحويل التيار إلى معدل تدفق المياه باستخدام المعايرة (بين 4mA و 20mA)
  flowRate = map_ranges(current_mA, MIN_MA, MAX_MA, MIN_FLOW, MAX_FLOW);
}

// دالة لضبط القيم بين النطاقات (مشابهة لدالة map في أردوينو)
float map_ranges(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}









// ---------------------------------app begin---------------------------------------
void setup() {


  pinMode(RELAY_OPEN, OUTPUT);
  pinMode(RELAY_CLOSE, OUTPUT);
  pinMode(ENCODER_BUTTON, INPUT_PULLUP);
  u8g2.begin();
  if (digitalRead(D7)) {

    pinMode(MAX485_RE_NEG, OUTPUT);
    pinMode(MAX485_DE, OUTPUT);
    postTransmission();
    Serial.begin(115200, SERIAL_8N2);
    node.begin(1, Serial);
    node.preTransmission(preTransmission);
    node.postTransmission(postTransmission);
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
    offline = 1;

    while (1) {
      ESP.wdtFeed();
      yield();
      offline_loop();
    }
  }


  LittleFS.begin();
  truck_id = readFile("/port_id.txt");
  ssid = readFile("/username.txt");
  password = readFile("/password.txt");
  mqtt_server = readFile("/mqtt_address.txt");

  setup_wifi();
  lcd(30, truck_id);

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
    thirdCloseTime = config[10].toInt();
    added_time = config[11].toInt();
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
    while (1) {
      ESP.wdtFeed();
      yield();
      modbus_loop();
    }
  }

  if (config[0] == "milli ampere") {
    Serial.begin(115200);
    Serial.println("start in milli mode");

    MIN_MA = config[1].toInt();
    MAX_MA = config[2].toInt();
    RESISTANCE_OHM = config[3].toInt();
    firstCloseTime = config[4].toInt();
    secondCloseTime = config[5].toInt();
    firstCloseLagV = config[6].toInt();
    secondCloseLagV = config[7].toInt();
    thirdCloseTime = config[8].toInt();
    added_time = config[9].toInt();
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
    Serial.println("end in milli mode");

    while (1) {
      ESP.wdtFeed();
      yield();
      MA_loop();
    }
  }

  if (config[0] == "pulse") {

    leter_per_pulse = config[1].toInt();
    firstCloseTime = config[2].toInt();
    secondCloseTime = config[3].toInt();
    firstCloseLagV = config[4].toInt();
    secondCloseLagV = config[5].toInt();
    thirdCloseTime = config[6].toInt();
    added_time = config[7].toInt();
    TIME_OPEN_DC = firstCloseTime + secondCloseTime + thirdCloseTime;
    while (1) {
      ESP.wdtFeed();
      yield();
      pulse_loop();
    }
  }
}

void modbus_loop() {

  if_long_press();

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 100) {
    lastPublishTime = millis();
    flowmeter_reader();
    client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());    
    if (is_running) {
      // flow_meter_value += random(0, 3);
      client.publish((String(truck_id) + "/valve_state").c_str(), "مفتوح");
      float FlowRate = flow_rate_reader();
      remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value);
      Serial.print("remain_Quantity = ");
      Serial.print(remain_Quantity);
      Serial.print("required_Quantity =");
      Serial.println(required_Quantity);
      double ExtraWater = (FlowRate / 2.0) * thirdCloseTime / litter;
      if (remain_Quantity <= float(firstCloseLagV) / litter && firstCloseStatus == 0) {
        RelayCloseDC(firstCloseTime);
        firstCloseStatus = 1;
      } else if (remain_Quantity <= float(secondCloseLagV) / litter && secondCloseStatus == 0) {
        RelayCloseDC(secondCloseTime);
        secondCloseStatus = 1;
      } else if (remain_Quantity - ExtraWater / litter <= 0 && thirdCloseStatus == 0) {
        RelayCloseDC(thirdCloseTime + added_time);
        thirdCloseStatus = 1;
        force_stop = 0;
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }
    }
  }
}

void pulse_loop() {
}

void MA_loop() {
}

void offline_loop() {

  scroll();


  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 100) {
    lastPublishTime = millis();
    flowmeter_reader();
    if (is_running) {
      // flow_meter_value++;
      float FlowRate = flow_rate_reader();
      remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value);
      double ExtraWater = (FlowRate / 2.0) * thirdCloseTime / litter;
      progressBar = map(required_Quantity - remain_Quantity, 0, required_Quantity, 0, 118);
      if (remain_Quantity <= float(firstCloseLagV) / litter && firstCloseStatus == 0) {
        RelayCloseDC(firstCloseTime);
        firstCloseStatus = 1;
      } else if (remain_Quantity <= float(secondCloseLagV) / litter && secondCloseStatus == 0) {
        RelayCloseDC(secondCloseTime);
        secondCloseStatus = 1;
      } else if (remain_Quantity - ExtraWater / litter <= 0 && thirdCloseStatus == 0) {
        RelayCloseDC(thirdCloseTime + added_time);
        thirdCloseStatus = 1;
        is_running = 0;
        isBold[1] = 0;
        isBold[2] = 0;
      }
    }
  }
}


void loop() {
}
