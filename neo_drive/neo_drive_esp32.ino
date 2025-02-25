#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

#define LED_PIN    5
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
  // Simple rainbow that affects all pixels
  for (int j = 0; j < 256; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, wheel((i + j) & 255));
    }
    strip.show();
    delay(20);
  }
}

void rainbowCycle() {
  // Uniformly distribute rainbow colors on strip
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
  // Spinner effect on LED strip: rotate one lit LED
  for (int i = 0; i < LED_COUNT; i++) {
    strip.clear();
    strip.setPixelColor(i, strip.Color(255, 0, 0));
    strip.show();
    delay(100);
  }
}

void breathe() {
  // Breathe animation for entire strip using fade in/out
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

void setup() {
  Serial.begin(115200);
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
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
        // Compare animation type and call corresponding function
        if (strcmp(anim, "RAINBOW") == 0) {
          rainbow();
        } else if (strcmp(anim, "RAINBOW_CYCLE") == 0) {
          rainbowCycle();
        } else if (strcmp(anim, "SPINNER") == 0) {
          spinner();
        } else if (strcmp(anim, "BREATHE") == 0) {
          breathe();
        }
      }
    }
  }
}
