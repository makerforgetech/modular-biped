# NeoPixel LED Animation Library - Arduino Project

This project is an Arduino code used to control various light animations on Adafruit NeoPixel strips. Different animations can be performed on the LED strip, including color transitions, twinkle effects, pulse effects, and more.

## Table of Contents

- [Connections](#connections)
- [Color Definitions](#color-definitions)
- [Animations](#animations)
- [Functions](#functions)
- [Setup and Loop Functions](#setup-and-loop-functions)
- [Serial Commands](#serial-commands)

## Connections

The code uses the Adafruit NeoPixel library to control the NeoPixel strips. You can install the library by following these steps:

1. [Download Adafruit NeoPixel Library](https://github.com/adafruit/Adafruit_NeoPixel)
2. Add the NeoPixel library to the Arduino IDE.

## Color Definitions

Colors used in this project are defined by the `strip.Color(r, g, b)` function. Below are the available color definitions:

```cpp
// Basic Colors
#define COLOR_RED     strip.Color(255, 0, 0)
#define COLOR_GREEN   strip.Color(0, 255, 0)
#define COLOR_BLUE    strip.Color(0, 0, 255)
#define COLOR_YELLOW  strip.Color(255, 255, 0)
#define COLOR_PURPLE  strip.Color(255, 0, 255)
#define COLOR_CYAN    strip.Color(0, 255, 255)
#define COLOR_WHITE   strip.Color(255, 255, 255)
#define COLOR_ORANGE  strip.Color(255, 165, 0)

// Additional Colors
#define COLOR_PINK    strip.Color(255, 105, 180)
#define COLOR_GOLD    strip.Color(255, 215, 0)
#define COLOR_TEAL    strip.Color(0, 128, 128)
#define COLOR_MAGENTA strip.Color(255, 0, 127)
#define COLOR_LIME    strip.Color(50, 205, 50)
#define COLOR_SKY_BLUE strip.Color(135, 206, 235)
#define COLOR_NAVY    strip.Color(0, 0, 128)
#define COLOR_MAROON  strip.Color(128, 0, 0)
#define COLOR_AQUA    strip.Color(127, 255, 212)
#define COLOR_VIOLET  strip.Color(138, 43, 226)
#define COLOR_CORAL   strip.Color(255, 127, 80)
#define COLOR_TURQUOISE strip.Color(64, 224, 208)
```

These colors can also be used through text-based commands with the `getColorFromString()` function.

## Animations

Below are the available animations that can be performed on the NeoPixel strip:

### 1. **Rainbow**
Creates a rainbow effect where the colors change sequentially across each LED.

```cpp
void rainbow(uint32_t color = 0, int iterations = 1);
```

### 2. **Rainbow Cycle**
The colors cycle through the rainbow, changing in a loop across the LEDs.

```cpp
void rainbowCycle(uint32_t color = 0, int iterations = 1);
```

### 3. **Spinner**
Each LED lights up one by one, then fades out in a spinning motion.

```cpp
void spinner(uint32_t color = COLOR_RED, int iterations = 1);
```

### 4. **Breathe**
LEDs light up and fade out, creating a breathing effect with increasing and decreasing brightness.

```cpp
void breathe(uint32_t color = COLOR_RED, int iterations = 1);
```

### 5. **Meteor Rain**
LEDs light up one by one, simulating a meteor shower with random positions and sizes.

```cpp
void meteorRain(uint32_t color = COLOR_WHITE, int size = 5, int decay = 50);
```

### 6. **Fire Flicker**
Creates a flickering flame effect, where LEDs light up with random brightness values.

```cpp
void fireFlicker(uint32_t color = COLOR_ORANGE);
```

### 7. **Comet**
A comet-like effect where LEDs light up one by one, passing along the strip.

```cpp
void comet(uint32_t color = strip.Color(0, 255, 255), int speed = 50);
```

### 8. **Wave**
A wave effect where each LED gradually fades in and out, moving like a wave.

```cpp
void wave(uint32_t color = 0);
```

### 9. **Pulse**
A pulsing effect where the LEDs gradually fade in and out, mimicking a heartbeat.

```cpp
void pulse(uint32_t color = strip.Color(255, 0, 127));
```

### 10. **Twinkle**
The LEDs randomly light up and fade out, creating a twinkling star effect.

```cpp
void twinkle(uint32_t color = COLOR_WHITE);
```

### 11. **Color Wipe**
LEDs light up one by one in a sweeping motion, then turn off in the same manner.

```cpp
void colorWipe(uint32_t color = COLOR_RED, int speed = 50);
```

### 12. **Random Blink**
LEDs randomly blink on and off, with the possibility of different colors.

```cpp
void randomBlink(uint32_t color = 0);
```

### 13. **Theater Chase**
A theater-style chase effect where LEDs light up in groups, creating a trailing effect.

```cpp
void theaterChase(uint32_t color = strip.Color(127, 127, 127), int wait = 50);
```

### 14. **Snow**
Simulates falling snow by randomly lighting up LEDs.

```cpp
void snow(uint32_t color = COLOR_WHITE);
```
### 15. **Alternating Colors**

Alternates between two colors across the strip.

```cpp
void alternatingColors(uint32_t color1 = COLOR_RED, uint32_t color2 = COLOR_BLUE, int cycles = 10, int wait = 100);
```

- `color1`: First color to alternate with.
- `color2`: Second color to alternate with.
- `cycles`: Number of cycles to repeat.
- `wait`: Delay between each cycle.

---

## Functions

### **getColorFromString**
This function returns the RGB value of a color based on its name.

```cpp
uint32_t getColorFromString(const char* colorName);
```

### **getRGBFromColor**
This function extracts the RGB components from a color value.

```cpp
void getRGBFromColor(uint32_t color, uint8_t &r, uint8_t &g, uint8_t &b);
```

## Setup and Loop Functions

### Setup

```cpp
void setup() {
  Serial.begin(115200);  // Start serial communication
  strip.begin();         // Initialize NeoPixel strip
  strip.show();          // Initially turn off all LEDs
}
```

### Loop

The `loop()` function runs continuously, processing incoming serial commands that trigger animations.

```cpp
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    // Trigger animations based on the command
  }
}
```

## Serial Commands

Various animations can be triggered via serial commands sent to the Arduino. These commands include `SET` and `ANIMATE` to define colors and animations.

Example commands:

- **SET**: Used to set a specific LED to a given color.

  ```plaintext
  SET 0 255 0 0  // Set LED 0 to red
  ```

- **ANIMATE**: Used to start a specific animation.

  ```plaintext
  ANIMATE RAINBOW  // Start the rainbow animation
  ```
## Command Input (via Serial Monitor)

This library allows control via the **Serial Monitor** with the following commands:

1. **SET**
   - Syntax: `SET <index> <r> <g> <b>`
   - Description: Set a specific LED index to a specific RGB color with a fade effect.

2. **ANIMATE**
   - Syntax: `ANIMATE <animation> <color1> <color2> <repeat>`
   - Description: Run an animation with specified colors and repeat count.
