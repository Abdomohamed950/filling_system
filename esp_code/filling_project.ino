#include "defines.h"


WiFiClient espClient;
PubSubClient client(espClient);
ModbusMaster node;

// تحويل البيانات المجمعة إلى قيمة
uint32_t AABBCCDD(uint16_t firstRecv, uint16_t secondRecv) {
  uint8_t u1_right = firstRecv & 0x00ff;
  uint8_t u1_left = firstRecv >> 8;
  uint8_t u2_right = secondRecv & 0x00ff;
  uint8_t u2_left = secondRecv >> 8;
  return (((uint32_t)u2_right << 24) | ((uint32_t)u2_left << 16) | ((uint32_t)u1_right << 8) | (uint32_t)u1_left);
}


void controlMotor(bool state) {
  digitalWrite(MOTOR_PIN, state ? HIGH : LOW);  // HIGH لتشغيل الموتور، LOW لإيقافه
}


// إعداد الـ WiFi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// إرسال واستقبال البيانات من RS-485
void preTransmission() {
  digitalWrite(MAX485_RE_NEG, HIGH);
  digitalWrite(MAX485_DE, HIGH);
}

void postTransmission() {
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);
}

// وظيفة استقبال رسائل MQTT
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

  if (topicStr.endsWith("/quantity")) {
    target_quantity = message.toInt() + flow_meter_value;
    Serial.print("Target quantity set to: ");
    Serial.println(target_quantity);
  } else if (topicStr.endsWith("/state")) {
    if (message == "start") {
      is_running = true;
      flow_meter_value = 0;
      Serial.println("Truck started");
    } else if (message == "stop") {
      is_running = false;
      Serial.println("Truck stopped");
    }
  }
}

// إعادة الاتصال بـ MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESPTruckClient")) {
      Serial.println("connected");
      client.subscribe((String(truck_id) + "/quantity").c_str());
      client.subscribe((String(truck_id) + "/state").c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// إعداد البرنامج
void setup() {
  Serial.begin(115200);
  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // إعدادات Modbus
  pinMode(MAX485_RE_NEG, OUTPUT);
  pinMode(MAX485_DE, OUTPUT);
  postTransmission();
  node.begin(SLAVE_ID, Serial2);
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);
  Serial2.begin(SERIAL_MODBUS_BAUD_RATE, SERIAL_8N2, RXD2, TXD2);

  pinMode(MOTOR_PIN, OUTPUT);
  controlMotor(false);  // تأكد من أن الموتور متوقف عند بدء التشغيل
}

// الحلقة الرئيسية
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  uint16_t result = node.readHoldingRegisters(SLAVE_ADDRESS_REG_STR_RNG, REG_IN_ROW);

  if (result == node.ku8MBSuccess) {
    DATA[0] = node.getResponseBuffer(0);
    DATA[1] = node.getResponseBuffer(1);
    uint32_t value = AABBCCDD(DATA[0], DATA[1]);

    int2f int2f_obj;
    int2f_obj.intVal = value;
    flow_meter_value = int2f_obj.f;
  }

  if (is_running) {
    // نشر القيمة الحالية
    String topic = String(truck_id) + "/flowmeter";
    String payload = String(flow_meter_value, 4);
    client.publish(topic.c_str(), payload.c_str());
    Serial.print("Flow meter value published: ");
    Serial.println(payload);

    // التحقق من الوصول إلى الكمية المطلوبة
    if (flow_meter_value >= target_quantity) {
      is_running = false;
      controlMotor(false);  // إيقاف الموتور
      Serial.println("Target quantity reached, stopping...");
      client.publish((String(truck_id) + "/state").c_str(), "stop");
    } else {
      controlMotor(true);  // تشغيل الموتور إذا لم يتم الوصول للكمية المطلوبة
    }

    delay(POLL_TIMEOUT_MS);
  } else {
    controlMotor(false);  // إيقاف الموتور إذا كان في وضع الإيقاف
  }
}