#include <Arduino.h>
#include <WiFi.h>  //for esp32
#include <PubSubClient.h>
#include <ModbusMaster.h>
#include "defines.h"
#include <lib.h>


void TaskMQTT(void *pvParameters) {
  for (;;) {
    Serial.println("TaskMQTT");
    if (!client.connected()) {
      reconnect();
    }
    client.loop();
    vTaskDelay(200 / portTICK_PERIOD_MS);
  }
}

void Task_config_update(void *pvParameters) {
  for (;;) {
    for (int i = 1; i < portnum + 1; i++)
      client.publish(("port" + String(i) + "/update").c_str(), "config");
    vTaskDelay(30000 / portTICK_PERIOD_MS);
  }
}

void task_flowmeter(void *pvParameters) {
  for (;;) {
    Serial.println("task_flowmeter");
    flowmeter_reader();
    flow_rate_reader();
    vTaskDelay(100 / portTICK_PERIOD_MS);
  }
}

void taskruning(void *pvParameters) {
  for (;;) {
    for (int i = 1; i < portnum + 1; i++) {
      if (port[i].is_running) {
        port[i].remain_Quantity = (port[i].flow_meter_prev_value + port[i].required_Quantity - port[i].flow_meter_value);

        if (port[i].remain_Quantity <= port_conf[i].firstCloseLagV / 1000 && port[i].firstCloseStatus == 0) {
          // RelayCloseDC(firstCloseTime);
          firstCloseStatus = 1;
        }

        else if (port[i].remain_Quantity <= port_conf[i].secondCloseLagV / 1000 && port[i].secondCloseStatus == 0) {
          // RelayCloseDC(secondCloseTime);
          secondCloseStatus = 1;
        }

        else if (port[i].remain_Quantity - port[i].ExtraWater / 1000 <= 0 && port[i].thirdCloseStatus == 0) {
          // RelayCloseDC(thirdCloseTime + 1000);
          thirdCloseStatus = 1;
          port[i].force_stop = 0;
          client.publish((String(truck_id) + "/state").c_str(), "stop");
        }
      }
    }
    vTaskDelay(100 / portTICK_PERIOD_MS);
  }
}



// ---------------------------------app begin---------------------------------------
void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N2, RXD2, TXD2);
  setup_wifi();

  pinMode(RELAY_OPEN, OUTPUT);
  pinMode(RELAY_CLOSE, OUTPUT);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  if (!client.connected()) {
    reconnect();
  }

  for (int i = 1; i < portnum + 1; i++)
    client.publish(("port" + String(i) + "/update").c_str(), "config");
  delay(1000);

  xTaskCreate(TaskMQTT, "TaskMQTT", 10000, NULL, 1, NULL);
  xTaskCreate(Task_config_update, "Task_config_update", 10000, NULL, 5, NULL);
  xTaskCreate(task_flowmeter, "task_flowmeter", 10000, NULL, 5, NULL);
  xTaskCreate(taskruning, "taskruning", 4096, NULL, 1, NULL);
}



void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // static unsigned long lastPublishTime = 0;
  // if (millis() - lastPublishTime > 100) {
  //   lastPublishTime = millis();
  //   flowmeter_reader();
  //   // Serial.println(flow_meter_value);
  //   client.publish((String(truck_id) + "/flowmeter").c_str(), String(flow_meter_value).c_str());

  //   if (is_running && result == node.ku8MBSuccess) {
  //     flow_rate_reader();
  //     remain_Quantity = (flow_meter_prev_value + required_Quantity - flow_meter_value);
  //     double ExtraWater = (FlowRate / 2.0) * thirdCloseTime / 1000;

  //     if (remain_Quantity <= float(firstCloseLagV) / 1000 && firstCloseStatus == 0) {
  //       RelayCloseDC(firstCloseTime);
  //       firstCloseStatus = 1;
  //     }

  //     else if (remain_Quantity <= float(secondCloseLagV) / 1000 && secondCloseStatus == 0) {
  //       RelayCloseDC(secondCloseTime);
  //       secondCloseStatus = 1;
  //     }

  //     else if (remain_Quantity - ExtraWater / 1000 <= 0 && thirdCloseStatus == 0) {
  //       RelayCloseDC(thirdCloseTime + 1000);
  //       thirdCloseStatus = 1;
  //       force_stop = 0;
  //       client.publish((String(truck_id) + "/state").c_str(), "stop");
  //     }
  //   }
  // }
}
