#ifndef DEFINES_H_
#define DEFINES_H_


#include <WiFi.h>
#include <PubSubClient.h>
#include <ModbusMaster.h>



const char* ssid = "abdo";
const char* password = "abdo1234";

// إعدادات MQTT
const char* mqtt_server = "10.42.0.1";
const int mqtt_port = 1883;
const char* truck_id = "truck_1";  // معرف الشاحنة

// Modbus إعدادات

#define MAX485_DE 32
#define MAX485_RE_NEG 33
#define SLAVE_ID 1
#define SLAVE_ADDRESS_REG_STR_RNG 2003
#define REG_IN_ROW 2
#define POLL_TIMEOUT_MS 100
#define SERIAL_MODBUS_BAUD_RATE 115200
#define RXD2 16
#define TXD2 17
#define MOTOR_PIN 25  // قم بتحديد رقم منفذ التحكم بالموتور

typedef union {
  uint32_t intVal;
  float f;
} int2f;

uint16_t DATA[2];
volatile float flow_meter_value = 0.0;  // القيمة الحالية لمقياس التدفق
int target_quantity = 0;                // الكمية المستهدفة
bool is_running = false;   


#endif  //End  DEFINES_H_