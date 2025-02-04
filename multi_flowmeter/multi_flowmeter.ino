#include <ModbusMaster.h>

// Modbus defines
#define MAX485_DE 32
#define MAX485_RE_NEG 33
#define SLAVE_ADDRESS_REG_STR_RNG 2003
#define REG_IN_ROW 2
#define POLL_TIMEOUT_MS 1000
#define SERIAL_MODBUS_BAUD_RATE 115200
#define RXD2 16  // RO
#define TXD2 17  // DI

#define SERIAL_DEBUG_BAUD_RATE 115200

typedef union {
  uint32_t intVal;
  float f;
} int2f;

const uint8_t SLAVE_IDS[] = { 1, 2, 3 };  
const uint8_t NUM_FLOWMETERS = sizeof(SLAVE_IDS) / sizeof(SLAVE_IDS[0]);

// Modbus Global Variables
ModbusMaster node;
uint16_t DATA[2];

uint32_t AABBCCDD(uint16_t firstRecv, uint16_t secondRecv) {
  uint8_t u1_right = firstRecv & 0x00ff;
  uint8_t u1_left = firstRecv >> 8;
  uint8_t u2_right = secondRecv & 0x00ff;
  uint8_t u2_left = secondRecv >> 8;
  return (((uint32_t)u2_right << 24) | ((uint32_t)u2_left << 16) | ((uint32_t)u1_right << 8) | (uint32_t)u1_left);
}

// Function for setting state of Pins DE & RE of RS-485
void preTransmission() {
  digitalWrite(MAX485_RE_NEG, HIGH);
  digitalWrite(MAX485_DE, HIGH);
}

void postTransmission() {
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);
}

void setup() {
  pinMode(MAX485_RE_NEG, OUTPUT);
  pinMode(MAX485_DE, OUTPUT);
  postTransmission();

  Serial.begin(SERIAL_DEBUG_BAUD_RATE);
  Serial2.begin(SERIAL_MODBUS_BAUD_RATE, SERIAL_8N2, RXD2, TXD2);

  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);
}

void loop() {
  for (uint8_t i = 0; i < NUM_FLOWMETERS; i++) {
    node.begin(SLAVE_IDS[i], Serial2); 
    Serial.print("Reading from Flowmeter ID: ");
    Serial.println(SLAVE_IDS[i]);

    uint16_t result = node.readHoldingRegisters(SLAVE_ADDRESS_REG_STR_RNG, REG_IN_ROW);

    Serial.print("Result message= ");
    Serial.println(result);
    Serial.print("Address Register: ");
    Serial.println(SLAVE_ADDRESS_REG_STR_RNG);

    if (result == node.ku8MBSuccess) {
      Serial.println("Accepted...");
      DATA[0] = node.getResponseBuffer(0);
      DATA[1] = node.getResponseBuffer(1);
      Serial.println("Received data: ");

      uint32_t value = AABBCCDD(DATA[0], DATA[1]);
      Serial.println("Raw data value: " + String(value));

      int2f int2f_obj;
      int2f_obj.intVal = value;
      double finalValue = int2f_obj.f;

      char buffer[10];
      dtostrf(finalValue, 0, 4, buffer);
      Serial.println("Converted value: " + String(buffer));
    } else {
      Serial.println("Failed to read from device!");
    }
  }
  delay(POLL_TIMEOUT_MS);
}
