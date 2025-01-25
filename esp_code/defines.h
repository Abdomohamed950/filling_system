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
#define RELAY_OPEN 5
#define RELAY_CLOSE 6

typedef union {
  uint32_t intVal;
  float f;
} int2f;
uint16_t DATA[2];

#define firstCloseTime 1
#define secondCloseTime 1
#define thirdCloseTime 1

#define firstCloseLagV 1
#define secondCloseLagV 1
#define thirdCloseLagV 1

#define TIME_OPEN_DC 1

bool firstCloseStatus = 0, secondCloseStatus = 0, thirdCloseStatus = 0;


// إعدادات الشبكة
const char* ssid = "Abdo123";
const char* password = "01063677938Abdo123@";

// إعدادات MQTT
const char* mqtt_server = "192.168.1.7";
const int mqtt_port = 1883;
const char* truck_id = "port1";

// تعريف المتغيرات
uint16_t result = 1;
volatile float flow_meter_value = 0;
volatile float flow_meter_prev_value = 0;
float remain_Quantity;
int required_Quantity = 0;
bool is_running = false;
bool updated = true;
String logdata = "";


//تعريف الopjects
WiFiClient espClient;
PubSubClient client(espClient);
ModbusMaster node;


//اعدادات الذاكره
#define QUEUE_SIZE 10
#define STRING_MAX_LENGTH 50

int write_index = 0; 




