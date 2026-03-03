/*
 * SIP Домофон - Контроллер двери для LilyGo T-Call ESP32
 * Версия: 5.2 
 */

#include <Arduino.h>

// --- Настройка пинов ---
#define WIEGAND_D0    4      // DATA0
#define WIEGAND_D1    5      // DATA1
#define RELAY_PIN     14     // реле замка
#define DOOR_SENSOR   12     // геркон
#define EXIT_BUTTON   32     // кнопка выхода
#define CALL_BUTTON   33     // кнопка вызова

// Аппаратный UART2
#define UART2_RX_PIN  13     // GPIO13 - RX от камеры
#define UART2_TX_PIN  15     // GPIO15 - TX к камере
HardwareSerial cameraSerial(2);

// --- Константы ---
#define UART_BAUD      115200
#define RELAY_DEFAULT_TIME 5000
#define DEBOUNCE_DELAY 300
#define BUTTON_HOLD_TIME 2000
#define CALL_NUMBER    "100"
#define STATUS_INTERVAL 5000

// --- Глобальные переменные ---
volatile unsigned long lastWiegandBitTime = 0;
volatile unsigned long wiegandCode = 0;
volatile int wiegandBitCount = 0;

bool relayActive = false;
unsigned long relayOffTime = 0;
int relayDuration = RELAY_DEFAULT_TIME;

int lastDoorState = HIGH;
unsigned long lastDoorDebounceTime = 0;

// Для кнопок
int lastExitButtonState = HIGH;
int lastCallButtonState = HIGH;
unsigned long lastExitDebounceTime = 0;
unsigned long lastCallDebounceTime = 0;
unsigned long exitPressTime = 0;
unsigned long callPressTime = 0;
bool exitPressed = false;
bool callPressed = false;
bool exitHandled = false;
bool callHandled = false;

unsigned long lastStatusTime = 0;

// --- Wiegand прерывания ---
void IRAM_ATTR wiegandD0ISR() {
  lastWiegandBitTime = micros();
  wiegandCode = wiegandCode << 1;
  wiegandBitCount++;
}

void IRAM_ATTR wiegandD1ISR() {
  lastWiegandBitTime = micros();
  wiegandCode = (wiegandCode << 1) | 1;
  wiegandBitCount++;
}

// --- Отправка на камеру ---
void sendToCamera(const String& message) {
  cameraSerial.println(message);
  cameraSerial.flush();
  Serial.print("[UART ->] ");
  Serial.println(message);
}

// --- Отправка статуса ---
void sendStatus() {
  String status = "STATUS:relay=" + String(relayActive ? "1" : "0");
  status += ",door=" + String(digitalRead(DOOR_SENSOR) == LOW ? "closed" : "open");
  status += ",exit_btn=" + String(digitalRead(EXIT_BUTTON) == LOW ? "pressed" : "released");
  status += ",call_btn=" + String(digitalRead(CALL_BUTTON) == LOW ? "pressed" : "released");
  sendToCamera(status);
}

// --- Открытие двери ---
void openDoor(int duration = relayDuration, const char* source = "UNKNOWN") {
  if (duration <= 0) duration = RELAY_DEFAULT_TIME;
  
  digitalWrite(RELAY_PIN, HIGH);
  relayActive = true;
  relayOffTime = millis() + duration;
  
  sendToCamera("DOOR_OPENED:" + String(source));
  Serial.printf("Door opened by %s for %dms\n", source, duration);
}

// --- ЗВОНОК (отдельная команда!) ---
void makeCall() {
  String cmd = "CALL:" + String(CALL_NUMBER);
  sendToCamera(cmd);
  Serial.println(">>> SENT CALL COMMAND: " + cmd);
}

// --- Обработка ключа ---
void handleWiegandKey(uint32_t code, int bits) {
  if (bits < 20) return;
  sendToCamera("KEY:" + String(bits) + ":" + String(code));
  Serial.println("Key sent: " + String(code) + " (" + String(bits) + " bits)");
}

// --- Обработка команд с камеры ---
void handleUartCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  
  Serial.println("[UART <-] " + cmd);
  
  if (cmd.startsWith("OPEN")) {
    int colonIndex = cmd.indexOf(':');
    if (colonIndex > 0) {
      String durationStr = cmd.substring(colonIndex + 1);
      int duration = durationStr.toInt();
      openDoor(duration > 0 ? duration : relayDuration, "CAMERA");
    } else {
      openDoor(relayDuration, "CAMERA");
    }
  }
  else if (cmd == "STATUS") {
    sendStatus();
  }
  else if (cmd.startsWith("SET_DEFAULT_TIME:")) {
    int timeMs = cmd.substring(17).toInt();
    if (timeMs >= 500 && timeMs <= 60000) {
      relayDuration = timeMs;
      sendToCamera("DEFAULT_TIME_SET:" + String(relayDuration));
    }
  }
}

// --- Обработка кнопки выхода ---
void handleExitButton() {
  int reading = digitalRead(EXIT_BUTTON);
  
  if (reading != lastExitButtonState) {
    lastExitDebounceTime = millis();
  }
  
  if ((millis() - lastExitDebounceTime) > DEBOUNCE_DELAY) {
    if (reading == LOW && lastExitButtonState == HIGH) {
      exitPressTime = millis();
      exitPressed = true;
      exitHandled = false;
      Serial.println("Exit button pressed");
    }
    
    if (reading == HIGH && lastExitButtonState == LOW) {
      if (exitPressed && !exitHandled) {
        unsigned long pressDuration = millis() - exitPressTime;
        
        if (pressDuration < BUTTON_HOLD_TIME) {
          openDoor(relayDuration, "EXIT_BUTTON");
          Serial.printf("Exit button short press (%dms)\n", pressDuration);
        } else {
          sendToCamera("EXIT_BUTTON_HELD:" + String(pressDuration));
          Serial.printf("Exit button long press (%dms)\n", pressDuration);
        }
        exitHandled = true;
      }
      exitPressed = false;
    }
  }
  lastExitButtonState = reading;
}

// --- Обработка кнопки вызова - ИСПРАВЛЕНО!!! ---
void handleCallButton() {
  int reading = digitalRead(CALL_BUTTON);
  
  if (reading != lastCallButtonState) {
    lastCallDebounceTime = millis();
  }
  
  if ((millis() - lastCallDebounceTime) > DEBOUNCE_DELAY) {
    if (reading == LOW && lastCallButtonState == HIGH) {
      callPressTime = millis();
      callPressed = true;
      callHandled = false;
      Serial.println("Call button pressed");
    }
    
    if (reading == HIGH && lastCallButtonState == LOW) {
      if (callPressed && !callHandled) {
        unsigned long pressDuration = millis() - callPressTime;
        
        if (pressDuration < BUTTON_HOLD_TIME) {
          // КОРОТКОЕ НАЖАТИЕ - ОТПРАВЛЯЕМ CALL КОМАНДУ!
          Serial.println("=== SHORT PRESS - SENDING CALL ===");
          makeCall();  // Это отправляет CALL:100
        } else {
          // Длинное нажатие - специальная функция
          sendToCamera("CALL_BUTTON_HELD:" + String(pressDuration));
          Serial.printf("Call button long press (%dms)\n", pressDuration);
        }
        callHandled = true;
      }
      callPressed = false;
    }
  }
  lastCallButtonState = reading;
}

// --- Setup ---
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=================================");
  Serial.println("Door Controller v5.2 - FIXED CALL");
  Serial.println("=================================");
  
  cameraSerial.begin(UART_BAUD, SERIAL_8N1, UART2_RX_PIN, UART2_TX_PIN);
  cameraSerial.setTimeout(100);
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  pinMode(DOOR_SENSOR, INPUT_PULLUP);
  pinMode(EXIT_BUTTON, INPUT_PULLUP);
  pinMode(CALL_BUTTON, INPUT_PULLUP);
  
  pinMode(WIEGAND_D0, INPUT_PULLUP);
  pinMode(WIEGAND_D1, INPUT_PULLUP);
  
  attachInterrupt(digitalPinToInterrupt(WIEGAND_D0), wiegandD0ISR, FALLING);
  attachInterrupt(digitalPinToInterrupt(WIEGAND_D1), wiegandD1ISR, FALLING);
  
  delay(500);
  sendToCamera("ESP32_READY");
  sendToCamera("FW_VERSION:5.2-CALL-FIXED");
  
  Serial.println("Ready! CALL button will send CALL:100 command");
}

// --- Loop ---
void loop() {
  if (cameraSerial.available()) {
    String command = cameraSerial.readStringUntil('\n');
    handleUartCommand(command);
  }
  
  if (wiegandBitCount > 0 && (micros() - lastWiegandBitTime) > 5000) {
    handleWiegandKey(wiegandCode, wiegandBitCount);
    wiegandCode = 0;
    wiegandBitCount = 0;
  }
  
  if (relayActive && millis() >= relayOffTime) {
    digitalWrite(RELAY_PIN, LOW);
    relayActive = false;
    sendToCamera("DOOR_CLOSED (timer)");
  }
  
  int currentDoorReading = digitalRead(DOOR_SENSOR);
  if (currentDoorReading != lastDoorState) {
    lastDoorDebounceTime = millis();
  }
  if ((millis() - lastDoorDebounceTime) > DEBOUNCE_DELAY) {
    if (currentDoorReading != lastDoorState) {
      lastDoorState = currentDoorReading;
      sendToCamera(lastDoorState == LOW ? "DOOR_CLOSED" : "DOOR_OPEN");
    }
  }
  
  if (millis() - lastStatusTime > STATUS_INTERVAL) {
    sendStatus();
    lastStatusTime = millis();
  }
  
  handleExitButton();
  handleCallButton();  // Здесь теперь правильно!
  
  delay(10);
}
