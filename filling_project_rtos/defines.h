#ifndef defines_h
#define defines_h

// إعدادات الشبكة
const char* ssid = "Abdo123";
const char* password = "01063677938Abdo123@";

// إعدادات MQTT
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* truck_id = "port1";

#define portnum 5
// Modbus إعدادات

#define MAX485_DE 32
#define MAX485_RE_NEG 33
#define REG_IN_ROW 2
#define RXD2 16
#define TXD2 17
#define RELAY_OPEN 25
#define RELAY_CLOSE 26

typedef union {
  uint32_t intVal;
  float f;
} int2f;
uint16_t DATA[2];

int thirdCloseTime = 3000;
int thirdCloseLagV = 100;

int TIME_OPEN_DC;

bool firstCloseStatus = 0, secondCloseStatus = 0, thirdCloseStatus = 0;




//تعريف الopjects
WiFiClient espClient;
PubSubClient client(espClient);
ModbusMaster node;

String config[10];

typedef struct {
  String mode;
  int baudrate;
  int frame;
  String endian;
  int slave_id;
  int register_address;
  int firstCloseTime;
  int secondCloseTime;
  int thirdCloseTime;
  float firstCloseLagV;
  float secondCloseLagV;  
} ports_conf;


ports_conf port_conf[portnum+1] ;

typedef struct {
  float required_Quantity;
  float flow_meter_prev_value;
  float flow_meter_value;
  float flow_rate;
  bool  is_running;
  bool  force_stop;
  bool  firstCloseStatus;
  bool  secondCloseStatus;
  bool  thirdCloseStatus;
  float remain_Quantity;
  float ExtraWater;
} ports;


ports port[portnum+1] ;

#endif