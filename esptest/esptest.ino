#include <WiFi.h>  //for esp32
// #include <ESP8266WiFi.h>  //for esp8266
#include <PubSubClient.h>

// إعدادات الشبكة
const char* ssid = "Abdo123";
const char* password = "01063677938Abdo123@";

// إعدادات MQTT
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* truck_id = "port1"; 

// تعريف المتغيرات
volatile int flow_meter_value = 0;
int target_quantity = 0;          
bool is_running = false;          

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password, 0, nullptr, true); // تحديد الشبكة المخفية

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

    target_quantity = message.toInt() + flow_meter_value; 
    Serial.print("Target quantity set to: ");
    Serial.println(target_quantity);
    String topic = String(truck_id) + "/state";
    String payload = "filling";
    client.publish(topic.c_str(), payload.c_str());

  } else if (topicStr == String(truck_id) + "/state") {
    Serial.print("message set to: ");
    Serial.println(message);
    if (message == "start") {
      is_running = true;       
      Serial.println("Truck started");
    } else if (message == "stop") {
      is_running = false;
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

  String topic = String(truck_id) + "/flowmeter";
  String payload = String(flow_meter_value);
  client.publish(topic.c_str(), payload.c_str());
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 100) {
    if (is_running) {
      // محاكاة مقياس التدفق
      lastPublishTime = millis();
      digitalWrite(LED_BUILTIN, HIGH); 

      flow_meter_value += random(1, 5);
      String topic = String(truck_id) + "/flowmeter";
      String payload = String(flow_meter_value);
      client.publish(topic.c_str(), payload.c_str());
      Serial.print("Flow meter value published: ");
      Serial.println(payload);

      if (flow_meter_value >= target_quantity) {
        digitalWrite(LED_BUILTIN, LOW);  // turn the LED off by making the voltage LOW

        is_running = false;  // إيقاف التشغيل
        Serial.println("Target quantity reached, stopping...");
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }
    } else {
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
}