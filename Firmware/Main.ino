#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>
#include <TinyUSB_Keyboard.h>
#include <Wire.h>

#define NUM_ROWS 5
#define NUM_COLS 14
#define NUM_LEDS 8

const uint8_t rowPins[NUM_ROWS] = {16, 17, 19, 18, 27};
const uint8_t colPins[NUM_COLS] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
const uint8_t rowLens[NUM_ROWS] = {14, 14, 13, 12, 8};

const uint8_t encoderA = 20;
const uint8_t encoderB = 21;
const uint8_t encoderBtn = 22;

const uint8_t ledPin = 26;

Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_NeoPixel leds(NUM_LEDS, ledPin, NEO_GRB + NEO_KHZ800);
TinyUSB_Keyboard keyboard;

int lastEncoder = 0;
int lastEncoderState = 0;
int colorIndex = 0;
unsigned long lastPressTime = 0;
int keyCount = 0;

const uint8_t colors[3][3] = {
  {0, 0, 50},
  {50, 0, 0},
  {0, 50, 0}
};

const uint8_t keymap[5][14] = {
  {KEY_ESC, 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '-', '=', KEY_BACKSPACE},
  {KEY_TAB, 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', 0, KEY_RETURN},
  {KEY_LEFT_SHIFT, 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, 0, 0},
  {KEY_LEFT_CTRL, KEY_LEFT_GUI, KEY_LEFT_ALT, 0, 0, ' ', ' ', 0, 0, 0, KEY_LEFT, KEY_DOWN, KEY_UP, KEY_RIGHT},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
};

void setup() {
  for (int i = 0; i < NUM_COLS; i++) {
    pinMode(colPins[i], OUTPUT);
    digitalWrite(colPins[i], HIGH);
  }
  for (int i = 0; i < NUM_ROWS; i++) {
    pinMode(rowPins[i], INPUT_PULLUP);
  }

  pinMode(encoderA, INPUT_PULLUP);
  pinMode(encoderB, INPUT_PULLUP);
  pinMode(encoderBtn, INPUT_PULLUP);

  leds.begin();
  leds.setBrightness(20);
  leds.show();

  Wire.setSDA(0);
  Wire.setSCL(1);
  Wire.begin();
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);

  keyboard.begin();
  updateLEDs();
  updateDisplay();
}

void loop() {
  scanMatrix();
  handleEncoder();
}

void scanMatrix() {
  for (int c = 0; c < NUM_COLS; c++) {
    digitalWrite(colPins[c], LOW);
    delayMicroseconds(3);
    for (int r = 0; r < NUM_ROWS; r++) {
      if (c < rowLens[r]) {
        if (!digitalRead(rowPins[r])) {
          keyboard.press(keymap[r][c]);
          keyCount++;
          updateDisplay();
          delay(10);
        } else {
          keyboard.release(keymap[r][c]);
        }
      }
    }
    digitalWrite(colPins[c], HIGH);
  }
}

void handleEncoder() {
  int a = digitalRead(encoderA);
  int b = digitalRead(encoderB);
  if (a != lastEncoderState) {
    if (b != a) {
      colorIndex++;
    } else {
      colorIndex--;
    }
    if (colorIndex < 0) colorIndex = 2;
    if (colorIndex > 2) colorIndex = 0;
    updateLEDs();
    updateDisplay();
  }
  lastEncoderState = a;
}

void updateLEDs() {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds.setPixelColor(i, leds.Color(colors[colorIndex][0], colors[colorIndex][1], colors[colorIndex][2]));
  }
  leds.show();
}

void updateDisplay() {
  display.clearDisplay();
  display.setCursor(0, 0);
  if (colorIndex == 0) {
    display.print("Color: Blue");
  } else if (colorIndex == 1) {
    display.print("Color: Red");
  } else {
    display.print("Color: Green");
  }
  display.setCursor(0, 10);
  display.print("Keypresses: ");
  display.print(keyCount);
  display.display();
}
