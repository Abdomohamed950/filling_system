#include <WiFi.h>           //for esp32
// #include <ESP8266WiFi.h>  //for esp8266
#include <PubSubClient.h>

// إعدادات الشبكة
const char* ssid = "abdo";
const char* password = "abdo1234";

// إعدادات MQTT
const char* mqtt_server = "10.42.0.1";
const int mqtt_port = 1883;
const char* truck_id = "port1";  // معرف الشاحنة

// تعريف المتغيرات
volatile int flow_meter_value = 0;  // القيمة الحالية لمقياس التدفق
int target_quantity = 0;            // الكمية المستهدفة
bool is_running = false;            // حالة التشغيل

WiFiClient espClient;
PubSubClient client(espClient);

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

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

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

  // معالجة المواضيع
  if (topicStr == String(truck_id) + "/quantity") {
    target_quantity = message.toInt()+flow_meter_value;  // تحديث الكمية المستهدفة
    Serial.print("Target quantity set to: ");
    Serial.println(target_quantity);
  } else if (topicStr == String(truck_id) + "/state") {
    Serial.print("message set to: ");
    Serial.println(message);
    if (message == "start") {
      is_running = true;     // بدء التشغيل
      // flow_meter_value = 0;  // إعادة ضبط مقياس التدفق
      Serial.println("Truck started");
    } else if (message == "stop") {
      is_running = false;  // إيقاف التشغيل
      Serial.println("Truck stopped");
    }
  }
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect((String("ESPTruckClient_") + truck_id).c_str())) {
      Serial.println("connected");
      client.subscribe((String(truck_id) + "/quantity").c_str());
      client.subscribe((String(truck_id) + "/state").c_str());
      client.subscribe((String(truck_id) + "/refresh").c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  pinMode(LED_BUILTIN, OUTPUT);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  if (is_running) {
    // محاكاة مقياس التدفق
    static unsigned long lastPublishTime = 0;
    if (millis() - lastPublishTime > 100) {
      lastPublishTime = millis();
      digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)

      flow_meter_value += random(1, 5);  // زيادة عشوائية لمحاكاة التدفق
      String topic = String(truck_id) + "/flowmeter";
      String payload = String(flow_meter_value);
      client.publish(topic.c_str(), payload.c_str());
      Serial.print("Flow meter value published: ");
      Serial.println(payload);

      // التحقق من حالة التوقف
      if (flow_meter_value >= target_quantity) {
        digitalWrite(LED_BUILTIN, LOW);  // turn the LED off by making the voltage LOW

        is_running = false;  // إيقاف التشغيل
        Serial.println("Target quantity reached, stopping...");
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }
    }
  } else {
    digitalWrite(LED_BUILTIN, LOW);
  }
}
