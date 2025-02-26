#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

#define LED_PIN    D5
#define LED_COUNT  23

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

uint32_t wheel(byte pos) {
  if (pos < 85) {
    return strip.Color(pos * 3, 255 - pos * 3, 0);
  } else if (pos < 170) {
    pos -= 85;
    return strip.Color(255 - pos * 3, 0, pos * 3);
  } else {
    pos -= 170;
    return strip.Color(0, pos * 3, 255 - pos * 3);
  }
}

void rainbow() {
  for (int j = 0; j < 256; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, wheel((i + j) & 255));
    }
    strip.show();
    delay(20);
  }
}

void rainbowCycle() {
  for (int j = 0; j < 256; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      int pos = ((i * 256 / LED_COUNT) + j) & 255;
      strip.setPixelColor(i, wheel(pos));
    }
    strip.show();
    delay(20);
  }
}

void spinner() {
  for (int i = 0; i < LED_COUNT; i++) {
    strip.clear();
    strip.setPixelColor(i, strip.Color(255, 0, 0));
    strip.show();
    delay(100);
  }
}

void breathe() {
  for (int brightness = 0; brightness <= 255; brightness += 5) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, strip.Color((255 * brightness) / 255, 0, 0));
    }
    strip.show();
    delay(20);
  }
  for (int brightness = 255; brightness >= 0; brightness -= 5) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, strip.Color((255 * brightness) / 255, 0, 0));
    }
    strip.show();
    delay(20);
  }
}

void meteorRain(int r, int g, int b, int size, int decay) {
  for (int i = 0; i < LED_COUNT + size; i++) {
    strip.clear();
    for (int j = 0; j < size; j++) {
      if (i - j >= 0 && i - j < LED_COUNT) {
        strip.setPixelColor(i - j, strip.Color(r / (j + 1), g / (j + 1), b / (j + 1)));
      }
    }
    strip.show();
    delay(decay);
  }
}

void fireFlicker() {
  for (int i = 0; i < LED_COUNT; i++) {
    int flicker = random(50, 255);
    strip.setPixelColor(i, strip.Color(flicker, flicker / 2, 0));
  }
  strip.show();
  delay(random(50, 150));
}

void comet(int r, int g, int b, int speed) {
  for (int i = 0; i < LED_COUNT; i++) {
    strip.clear();
    strip.setPixelColor(i, strip.Color(r, g, b));
    if (i > 0) strip.setPixelColor(i - 1, strip.Color(r / 2, g / 2, b / 2));
    strip.show();
    delay(speed);
  }
}

void wave() {
  for (int j = 0; j < 256; j += 5) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, wheel((i * 256 / LED_COUNT + j) & 255));
    }
    strip.show();
    delay(50);
  }
}

void setup() {
  Serial.begin(115200);
  strip.begin();
  strip.show();
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    // Expected "SET" command: "SET index r g b"
    if (cmd.startsWith("SET")) {
      int idx, r, g, b;
      int num = sscanf(cmd.c_str(), "SET %d %d %d %d", &idx, &r, &g, &b);
      if (num == 4 && idx >= 0 && idx < LED_COUNT) {
        // Fade in animation for single LED
        for (int brightness = 0; brightness <= 255; brightness += 25) {
          int rr = (r * brightness) / 255;
          int gg = (g * brightness) / 255;
          int bb = (b * brightness) / 255;
          strip.setPixelColor(idx, strip.Color(rr, gg, bb));
          strip.show();
          delay(10);
        }
      }
    }
    // New: "ANIMATE <animation>" command handling
    else if (cmd.startsWith("ANIMATE")) {
      char anim[20];
      if (sscanf(cmd.c_str(), "ANIMATE %s", anim) == 1) {
        if (strcmp(anim, "RAINBOW") == 0) rainbow();
        else if (strcmp(anim, "RAINBOW_CYCLE") == 0) rainbowCycle();
        else if (strcmp(anim, "SPINNER") == 0) spinner();
        else if (strcmp(anim, "BREATHE") == 0) breathe();
        else if (strcmp(anim, "METEOR") == 0) meteorRain(255, 255, 255, 5, 50);
        else if (strcmp(anim, "FIRE") == 0) fireFlicker();
        else if (strcmp(anim, "COMET") == 0) comet(0, 255, 255, 50);
        else if (strcmp(anim, "WAVE") == 0) wave();
      }
    }
  }
}
