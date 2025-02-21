// إعدادات الشبكة
String ssid = "";
String password = "";
String truck_id = "";
String mqtt_server = "";
const int mqtt_port = 1883;


// Modbus إعداد ات

#define MAX485_DE 32
#define MAX485_RE_NEG 33
#define SLAVE_ID 1
#define SLAVE_ADDRESS_REG_STR_RNG 2003
#define REG_IN_ROW 2
#define POLL_TIMEOUT_MS 100
#define SERIAL_MODBUS_BAUD_RATE 9600
#define RXD2 16
#define TXD2 17
#define RELAY_OPEN 25
#define RELAY_CLOSE 26
#define open_putton 18
#define close_putton 19

typedef union {
  uint32_t intVal;
  float f;
} int2f;
uint16_t DATA[2];

int firstCloseTime   ;
int secondCloseTime  ;
int thirdCloseTime ;
int firstCloseLagV   ;
int secondCloseLagV  ;
int thirdCloseLagV =100;
int added_time;

int TIME_OPEN_DC ;

bool firstCloseStatus = 0, secondCloseStatus = 0, thirdCloseStatus = 0;


// تعريف المتغيرات
uint16_t result = 1;
volatile float flow_meter_value = 0;
volatile float flow_meter_prev_value = 0;
float remain_Quantity;
float required_Quantity = 0;
bool is_running = false;
bool updated = true;
String logdata = "";
bool force_stop =1 ;

//تعريف الopjects
WiFiClient espClient;
PubSubClient client(espClient);
ModbusMaster node;


//اعدادات الذاكره
#define QUEUE_SIZE 10
#define STRING_MAX_LENGTH 50

int write_index = 0; 


String config[12];
