const int buttonPins[7] = {2, 3, 4, 5, 6, 7, 8};  // D2 ~ D8
bool wasPressed[7] = {false};                    // 현재 누르고 있는 상태인지
unsigned long lastSent[7] = {0};                 // 마지막으로 신호 보낸 시간
unsigned long lastSeenHigh[7] = {0};             // 버튼이 HIGH(떨어진 상태)로 바뀐 시점

const unsigned long interval = 100;              // 0.1초 주기 (ms)
const unsigned long trustTime = 50;              // 신뢰 시간 (챠터링 허용 범위 ms)

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 7; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);        // 풀업 저항 사용 (LOW = 눌림)
    wasPressed[i] = false;
  }
}

void loop() {
  unsigned long now = millis();

  for (int i = 0; i < 7; i++) {
    bool isPressed = digitalRead(buttonPins[i]) == LOW;

    if (isPressed) {
      if (!wasPressed[i] || now - lastSent[i] >= interval) {
        Serial.println(String(i + 1));  // 예: "1"
        lastSent[i] = now;
        wasPressed[i] = true;
      }
      lastSeenHigh[i] = 0;
    } else {
      if (wasPressed[i]) {
        if (lastSeenHigh[i] == 0) {
          lastSeenHigh[i] = now;  // 처음 떨어진 시점 기록
        } else if (now - lastSeenHigh[i] >= trustTime) {
          Serial.println("R" + String(i + 1));  // 예: "R1"
          wasPressed[i] = false;
          lastSent[i] = 0;
          lastSeenHigh[i] = 0;
        }
      }
    }
  }
}
