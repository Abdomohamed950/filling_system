// إعدادات الشبكة
String ssid = "";
String password = "";
String truck_id = "";
String mqtt_server = "";
const int mqtt_port = 1883;


// Modbus إعداد ات

#define MAX485_DE D0
#define MAX485_RE_NEG D0
#define RELAY_OPEN D6
#define RELAY_CLOSE D5
#define ENCODER_PIN_A D3
#define ENCODER_PIN_B D4
#define ENCODER_BUTTON D8
#define FLOW_SENSOR_PIN A0  // الدبوس الموصول بالمستشعر

#define REG_IN_ROW 2

typedef union {
  uint32_t intVal;
  float f;
} int2f;
uint16_t DATA[2];

int firstCloseTime  = 8000 ;
int secondCloseTime  = 2000 ;
int thirdCloseTime = 3000 ;
int firstCloseLagV  = 500 ;
int secondCloseLagV =300 ;
int thirdCloseLagV =100;
int added_time = 2000;

int MIN_MA ;
int MAX_MA ;
int RESISTANCE_OHM ;
int leter_per_pulse ;



#define ADC_RESOLUTION 1024 // دقة قراءة ADC (مثلاً في أردوينو 10-bit)
#define V_REF 3300          // الجهد المرجعي للمتحكم (5V → 5000mV)

#define MIN_FLOW 0.0  
#define MAX_FLOW 100.0




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
bool isButtonPressed = false;
unsigned long pressStartTime = 0;

bool offline = false;
int litter =1000;




U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/D1, /* data=*/D2, /* reset=*/U8X8_PIN_NONE);
// إعداد الإنكودر (تعديل الـ Pins حسب التوصيل لديك)


Encoder myEnc(ENCODER_PIN_A, ENCODER_PIN_B);
int lastEncoderPos = 0;
int currentMenuIndex = 0;
int quantity = 0;
bool editingQuantity = false;
int progressBar = 0;

//تعريف الopjects
WiFiClient espClient;
PubSubClient client(espClient);
ModbusMaster node;


//اعدادات الذاكره
#define QUEUE_SIZE 10
#define STRING_MAX_LENGTH 50

int write_index = 0; 


String config[13];
