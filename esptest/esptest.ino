#include <WiFi.h>  //for esp32
// #include <ESP8266WiFi.h>  //for esp8266
#include <PubSubClient.h>

#define RESOLUTION  1000
float remain_Quantity ;

// إعدادات الشبكة
const char* ssid = "Abdo123";
const char* password = "01063677938Abdo123@";

// إعدادات MQTT
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* truck_id = "port1";


#define firstCloseTime 1
#define secondCloseTime 1
#define thirdCloseTime 1

#define firstCloseLagV 1
#define secondCloseLagV 1
#define thirdCloseLagV 1

#define TIME_OPEN_DC 1

bool firstCloseStatus = 0, secondCloseStatus = 0, thirdCloseStatus = 0;

// تعريف المتغيرات
volatile int flow_meter_value = 0;
volatile float flow_meter_prev_value = 0;
int required_Quantity = 0;
bool is_running = false;
bool updated = true;
WiFiClient espClient;
PubSubClient client(espClient);
String logdata = "";



#include <FS.h> 
#include <SPIFFS.h> 

#define QUEUE_SIZE 10
#define STRING_MAX_LENGTH 50

int write_index = 0; 

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

    required_Quantity = message.toInt();    
    flow_meter_prev_value = flow_meter_value;
    Serial.print("Target quantity set to: ");
    Serial.println(required_Quantity);
    String topic = String(truck_id) + "/state";
    String payload = "filling";
    client.publish(topic.c_str(), payload.c_str());

  }

  else if (topicStr == String(truck_id) + "/logdata") {
    // Serial.println("hello");
    logdata = message ;
    // add_string_to_queue(logdata.c_str());
  }

  else if (topicStr == String(truck_id) + "/state") {

    Serial.print("message set to: ");
    Serial.println(message);
    if (message == "start") {
      is_running = true;
      Serial.println("Truck started");
    }

    else if (message == "stop") {
      is_running = false;
      Serial.println("Truck stopped");
      logdata += "," + String(flow_meter_value - flow_meter_prev_value);
      add_string_to_queue(logdata.c_str());
      print_queue();
    }
  }

  // //under tested
  // else if (topicStr == String(truck_id) + "/conf") {
  //   Serial.print("config set to: ");
  //   Serial.println(message);
  //   updated = false;
  // }

  // // end of under tested
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

void setup() {
  Serial.begin(115200);
  setup_wifi();
  pinMode(LED_BUILTIN, OUTPUT);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  init_spiffs();
  load_index_from_spiffs();

  // //under test
  if (!client.connected()) 
    reconnect();
  // while (updated) {
    String topic = String(truck_id) + "/flowmeter";
    String payload = String(flow_meter_value);
    client.publish(topic.c_str(), payload.c_str());
  //   delay(100);
  //   topic = String(truck_id) + "/update";
  //   payload = "config";
  //   client.publish(topic.c_str(), payload.c_str());
  //   delay(100);
  // }
  // // end of under test
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  static unsigned long lastPublishTime = 0;
  if (millis() - lastPublishTime > 100) {

    if (is_running) {

      lastPublishTime = millis();
      digitalWrite(LED_BUILTIN, HIGH);

      flow_meter_value += random(1, 5);

      String topic = String(truck_id) + "/flowmeter";
      String payload = String(flow_meter_value);
      client.publish(topic.c_str(), payload.c_str());
      // Serial.print("Flow meter value published: ");
      // Serial.println(payload);

      remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value );
      float precentage = ((required_Quantity - remain_Quantity)/required_Quantity)*100;
      Serial.print(remain_Quantity);
      Serial.print("    ,     ");
      Serial.println(precentage);

      if (flow_meter_value >= required_Quantity + flow_meter_prev_value) {
        digitalWrite(LED_BUILTIN, LOW); 

        is_running = false; 
        Serial.println("Target quantity reached, stopping...");
        client.publish((String(truck_id) + "/state").c_str(), "stop");
      }
    } else {
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
}