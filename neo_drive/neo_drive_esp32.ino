#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

#define LED_PIN    D5
#define LED_COUNT  23

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

// Color definitions - expanded with more options
#define COLOR_RED     strip.Color(255, 0, 0)
#define COLOR_GREEN   strip.Color(0, 255, 0)
#define COLOR_BLUE    strip.Color(0, 0, 255)
#define COLOR_YELLOW  strip.Color(255, 255, 0)
#define COLOR_PURPLE  strip.Color(255, 0, 255)
#define COLOR_CYAN    strip.Color(0, 255, 255)
#define COLOR_WHITE   strip.Color(255, 255, 255)
#define COLOR_ORANGE  strip.Color(255, 165, 0)
// New color definitions
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

// Color conversion function - updated with new colors
uint32_t getColorFromString(const char* colorName) {
  if (strcmp(colorName, "RED") == 0) return COLOR_RED;
  else if (strcmp(colorName, "GREEN") == 0) return COLOR_GREEN;
  else if (strcmp(colorName, "BLUE") == 0) return COLOR_BLUE;
  else if (strcmp(colorName, "YELLOW") == 0) return COLOR_YELLOW;
  else if (strcmp(colorName, "PURPLE") == 0) return COLOR_PURPLE;
  else if (strcmp(colorName, "CYAN") == 0) return COLOR_CYAN;
  else if (strcmp(colorName, "WHITE") == 0) return COLOR_WHITE;
  else if (strcmp(colorName, "ORANGE") == 0) return COLOR_ORANGE;
  // Added new colors
  else if (strcmp(colorName, "PINK") == 0) return COLOR_PINK;
  else if (strcmp(colorName, "GOLD") == 0) return COLOR_GOLD;
  else if (strcmp(colorName, "TEAL") == 0) return COLOR_TEAL;
  else if (strcmp(colorName, "MAGENTA") == 0) return COLOR_MAGENTA;
  else if (strcmp(colorName, "LIME") == 0) return COLOR_LIME;
  else if (strcmp(colorName, "SKY_BLUE") == 0) return COLOR_SKY_BLUE;
  else if (strcmp(colorName, "NAVY") == 0) return COLOR_NAVY;
  else if (strcmp(colorName, "MAROON") == 0) return COLOR_MAROON;
  else if (strcmp(colorName, "AQUA") == 0) return COLOR_AQUA;
  else if (strcmp(colorName, "VIOLET") == 0) return COLOR_VIOLET;
  else if (strcmp(colorName, "CORAL") == 0) return COLOR_CORAL;
  else if (strcmp(colorName, "TURQUOISE") == 0) return COLOR_TURQUOISE;
  return COLOR_WHITE; // Default color
}

// Extract RGB components from a uint32_t color
void getRGBFromColor(uint32_t color, uint8_t &r, uint8_t &g, uint8_t &b) {
  r = (color >> 16) & 0xFF;
  g = (color >> 8) & 0xFF;
  b = color & 0xFF;
}

uint32_t wheel(byte pos, uint32_t color = 0) {
  if (color != 0) {
    uint8_t r, g, b;
    getRGBFromColor(color, r, g, b);
    
    // Create a hue variation based on position but using the specified color
    uint8_t intensity = 255 - ((pos * 255) / 255);
    uint8_t maxChannel = max(r, max(g, b));
    float ratio = pos / 255.0;
    
    if (maxChannel == r) {
      return strip.Color(r, (uint8_t)(g * ratio), 0);
    } else if (maxChannel == g) {
      return strip.Color((uint8_t)(r * ratio), g, 0);
    } else {
      return strip.Color(0, (uint8_t)(g * ratio), b);
    }
  }
  
  // Original rainbow wheel
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

// Update animation functions to handle repeat count
void rainbow(uint32_t color = 0, int iterations = 1) {
  for (int j = 0; j < 256 * iterations; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, wheel((i + j) & 255, color));
    }
    strip.show();
    delay(20);
  }
}

void rainbowCycle(uint32_t color = 0, int iterations = 1) {
  for (int j = 0; j < 256 * iterations; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      int pos = ((i * 256 / LED_COUNT) + j) & 255;
      strip.setPixelColor(i, wheel(pos, color));
    }
    strip.show();
    delay(20);
  }
}

void spinner(uint32_t color = COLOR_RED, int iterations = 1) {
  for (int iter = 0; iter < iterations; iter++) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.clear();
      strip.setPixelColor(i, color);
      strip.show();
      delay(100);
    }
  }
}

void breathe(uint32_t color = COLOR_RED, int iterations = 1) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  for (int iter = 0; iter < iterations; iter++) {
    for (int brightness = 0; brightness <= 255; brightness += 5) {
      for (int i = 0; i < LED_COUNT; i++) {
        strip.setPixelColor(i, strip.Color((r * brightness) / 255, 
                                           (g * brightness) / 255, 
                                           (b * brightness) / 255));
      }
      strip.show();
      delay(20);
    }
    for (int brightness = 255; brightness >= 0; brightness -= 5) {
      for (int i = 0; i < LED_COUNT; i++) {
        strip.setPixelColor(i, strip.Color((r * brightness) / 255, 
                                           (g * brightness) / 255, 
                                           (b * brightness) / 255));
      }
      strip.show();
      delay(20);
    }
  }
}

void meteorRain(uint32_t color = COLOR_WHITE, int size = 5, int decay = 50) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
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

void fireFlicker(uint32_t color = COLOR_ORANGE) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  for (int i = 0; i < LED_COUNT; i++) {
    int flicker = random(50, 255);
    float ratio = flicker / 255.0;
    strip.setPixelColor(i, strip.Color(r * ratio, g * ratio, b * ratio));
  }
  strip.show();
  delay(random(50, 150));
}

void comet(uint32_t color = strip.Color(0, 255, 255), int speed = 50) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  for (int i = 0; i < LED_COUNT; i++) {
    strip.clear();
    strip.setPixelColor(i, strip.Color(r, g, b));
    if (i > 0) strip.setPixelColor(i - 1, strip.Color(r / 2, g / 2, b / 2));
    strip.show();
    delay(speed);
  }
}

void wave(uint32_t color = 0) {
  for (int j = 0; j < 256; j += 5) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, wheel((i * 256 / LED_COUNT + j) & 255, color));
    }
    strip.show();
    delay(50);
  }
}

void pulse(uint32_t color = strip.Color(255, 0, 127)) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  for (int brightness = 0; brightness < 255; brightness += 10) {
    float ratio = brightness / 255.0;
    strip.fill(strip.Color(r * ratio, g * ratio, b * ratio));
    strip.show();
    delay(50);
  }
}

void twinkle(uint32_t color = COLOR_WHITE) {
  for (int i = 0; i < 5; i++) {
    int index = random(LED_COUNT);
    strip.setPixelColor(index, color);
    strip.show();
    delay(100);
    strip.setPixelColor(index, strip.Color(0, 0, 0));
    strip.show();
  }
}

void colorWipe(uint32_t color = COLOR_RED, int speed = 50) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  for (int i = 0; i < LED_COUNT; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
    strip.show();
    delay(speed);
  }
}

void randomBlink(uint32_t color = 0) {
  if (color == 0) {
    // Original random colors mode
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, strip.Color(random(255), random(255), random(255)));
    }
  } else {
    uint8_t r, g, b;
    getRGBFromColor(color, r, g, b);
    // Use variations of the given color
    for (int i = 0; i < LED_COUNT; i++) {
      int variation = random(-30, 30);
      strip.setPixelColor(i, strip.Color(
        constrain(r + variation, 0, 255),
        constrain(g + variation, 0, 255),
        constrain(b + variation, 0, 255)
      ));
    }
  }
  strip.show();
  delay(100);
}

void theaterChase(uint32_t color = strip.Color(127, 127, 127), int wait = 50) {
  for (int j = 0; j < 5; j++) {  // do 5 cycles of chasing
    for (int q = 0; q < 3; q++) {
      for (int i = 0; i < strip.numPixels(); i += 3) {
        strip.setPixelColor(i + q, color);  // turn every third pixel on
      }
      strip.show();
      delay(wait);
      
      for (int i = 0; i < strip.numPixels(); i += 3) {
        strip.setPixelColor(i + q, 0);  // turn every third pixel off
      }
    }
  }
}

void snow(uint32_t color = COLOR_WHITE) {
  strip.clear();
  
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  for (int i = 0; i < 10; i++) { // Create 10 random snowflakes
    int snowflake = random(LED_COUNT);
    int intensity = random(100, 255);
    float ratio = intensity / 255.0;
    strip.setPixelColor(snowflake, strip.Color(r * ratio, g * ratio, b * ratio));
  }
  strip.show();
  delay(200);
}

// Updated alternatingColors with better multi-color support
void alternatingColors(uint32_t color1 = COLOR_RED, uint32_t color2 = COLOR_BLUE, int cycles = 10, int wait = 100) {
  for (int j = 0; j < cycles; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      strip.setPixelColor(i, (i + j) % 2 == 0 ? color1 : color2);
    }
    strip.show();
    delay(wait);
  }
}

// New multi-color gradient function
void multiColorGradient(uint32_t colors[], int colorCount, int iterations = 5) {
  for (int iter = 0; iter < iterations; iter++) {
    for (int j = 0; j < 256; j += 5) {
      for (int i = 0; i < LED_COUNT; i++) {
        // Determine which segment of colors this LED falls into
        int segment = (i * colorCount) / LED_COUNT;
        int pos = (i * colorCount * 256 / LED_COUNT) % 256;
        
        uint32_t color1 = colors[segment % colorCount];
        uint32_t color2 = colors[(segment + 1) % colorCount];
        
        uint8_t r1, g1, b1, r2, g2, b2;
        getRGBFromColor(color1, r1, g1, b1);
        getRGBFromColor(color2, r2, g2, b2);
        
        // Calculate position in gradient between these two colors
        float ratio = pos / 255.0;
        
        uint8_t r = r1 + (r2 - r1) * ratio;
        uint8_t g = g1 + (g2 - g1) * ratio;
        uint8_t b = b1 + (b2 - b1) * ratio;
        
        strip.setPixelColor(i, strip.Color(r, g, b));
      }
      strip.show();
      delay(30);
    }
  }
}

// New rainbow function with multiple colors that blends between them
void multiColorWave(uint32_t colors[], int colorCount, int iterations = 5) {
  for (int iter = 0; iter < iterations; iter++) {
    for (int j = 0; j < 256; j += 5) {
      for (int i = 0; i < LED_COUNT; i++) {
        // Calculate position in color cycle
        int pos = (i * 256 / LED_COUNT + j) % 256;
        int segment = (pos * colorCount) / 256;
        int segPos = (pos * colorCount) % 256;
        
        uint32_t color1 = colors[segment % colorCount];
        uint32_t color2 = colors[(segment + 1) % colorCount];
        
        uint8_t r1, g1, b1, r2, g2, b2;
        getRGBFromColor(color1, r1, g1, b1);
        getRGBFromColor(color2, r2, g2, b2);
        
        // Calculate position in gradient between these two colors
        float ratio = segPos / 255.0;
        
        uint8_t r = r1 + (r2 - r1) * ratio;
        uint8_t g = g1 + (g2 - g1) * ratio;
        uint8_t b = b1 + (b2 - b1) * ratio;
        
        strip.setPixelColor(i, strip.Color(r, g, b));
      }
      strip.show();
      delay(30);
    }
  }
}

void gradientFade(int cycles = 5, uint32_t color = 0) {
  for (int j = 0; j < cycles; j++) {
    for (int i = 0; i < LED_COUNT; i++) {
      int pos = map(i, 0, LED_COUNT - 1, 0, 255);
      strip.setPixelColor(i, wheel((pos + j) % 256, color));
    }
    strip.show();
    delay(30);
  }
}

void bouncingBall(uint32_t color = COLOR_RED) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  float gravity = 0.1;
  int startHeight = 1;
  float height = startHeight;
  float velocity = 0;
  float dampening = 0.90;
  
  for (int i = 0; i < 60; i++) {
    // Apply physics
    velocity += gravity;
    height -= velocity;
    if (height < 0) {
      height = 0;
      velocity = -velocity * dampening;
    }
    
    // Convert height to LED position
    int position = map(height * 100, 0, startHeight * 100, 0, LED_COUNT - 1);
    
    strip.clear();
    if (position >= 0 && position < LED_COUNT) {
      strip.setPixelColor(position, strip.Color(r, g, b));
    }
    strip.show();
    delay(30);
  }
}

void runningLights(uint32_t color = COLOR_RED, int wait = 50) {
  uint8_t r, g, b;
  getRGBFromColor(color, r, g, b);
  
  int position = 0;
  
  for (int i = 0; i < LED_COUNT * 2; i++) {
    position++;
    
    for (int j = 0; j < LED_COUNT; j++) {
      // Calculate sine wave for a running light effect
      int sinValue = sin(j + position) * 127 + 128;
      float ratio = sinValue / 255.0;
      
      strip.setPixelColor(j, strip.Color(
        r * ratio,
        g * ratio,
        b * ratio
      ));
    }
    
    strip.show();
    delay(wait);
  }
}

void stackedBars(int wait = 50, uint32_t color = 0) {
  // Fill up
  for (int h = 0; h < LED_COUNT; h++) {
    for (int i = 0; i <= h; i++) {
      if (color == 0) {
        strip.setPixelColor(i, wheel(map(i, 0, LED_COUNT - 1, 0, 255)));
      } else {
        strip.setPixelColor(i, color);
      }
    }
    strip.show();
    delay(wait);
  }
  
  // Empty
  for (int h = LED_COUNT - 1; h >= 0; h--) {
    for (int i = h; i < LED_COUNT; i++) {
      strip.setPixelColor(i, 0);
    }
    strip.show();
    delay(wait);
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
    // Enhanced ANIMATE command handling with color arguments and repeat count
    else if (cmd.startsWith("ANIMATE")) {
      char anim[20];
      char color1[20] = "";
      char color2[20] = "";
      int repeat = 1; // Default repeat count
      
      // Parse the command with varying number of arguments
      char* cmdParts[5]; // animation name, up to 2 colors, repeat count
      int argCount = 0;
      
      // Tokenize the command string
      char cmdBuffer[100];
      cmd.toCharArray(cmdBuffer, sizeof(cmdBuffer));
      char* token = strtok(cmdBuffer, " ");
      
      while (token != NULL && argCount < 5) {
        cmdParts[argCount++] = token;
        token = strtok(NULL, " ");
      }
      
      // First part should be "ANIMATE"
      if (argCount > 1) {
        strcpy(anim, cmdParts[1]);
        
        // Check for color1
        if (argCount > 2) {
          // Try to parse as a number (repeat count)
          if (isDigit(cmdParts[2][0])) {
            repeat = atoi(cmdParts[2]);
          } else {
            // It's a color
            strcpy(color1, cmdParts[2]);
            
            // Check for color2 or repeat count
            if (argCount > 3) {
              // Try to parse as a number (repeat count)
              if (isDigit(cmdParts[3][0])) {
                repeat = atoi(cmdParts[3]);
              } else {
                // It's a second color
                strcpy(color2, cmdParts[3]);
                
                // Check for repeat count after two colors
                if (argCount > 4) {
                  repeat = atoi(cmdParts[4]);
                }
              }
            }
          }
        }
        
        // Get color values if provided
        uint32_t color1Value = 0; // 0 means default/rainbow
        uint32_t color2Value = 0;
        
        if (strlen(color1) > 0) {
          color1Value = getColorFromString(color1);
        }
        
        if (strlen(color2) > 0) {
          color2Value = getColorFromString(color2);
        }
        
        // Cap repeat count to reasonable limits
        if (repeat < 1) repeat = 1;
        if (repeat > 10) repeat = 10;
        
        // Run the appropriate animation with the specified color and repeat count
        if (strcmp(anim, "RAINBOW") == 0) rainbow(color1Value, repeat);
        else if (strcmp(anim, "RAINBOW_CYCLE") == 0) rainbowCycle(color1Value, repeat);
        else if (strcmp(anim, "SPINNER") == 0) spinner(color1Value, repeat);
        else if (strcmp(anim, "BREATHE") == 0) breathe(color1Value, repeat);
        else if (strcmp(anim, "METEOR") == 0) meteorRain(color1Value);
        else if (strcmp(anim, "FIRE") == 0) fireFlicker(color1Value);
        else if (strcmp(anim, "COMET") == 0) comet(color1Value);
        else if (strcmp(anim, "WAVE") == 0) wave(color1Value);
        else if (strcmp(anim, "PULSE") == 0) pulse(color1Value);
        else if (strcmp(anim, "TWINKLE") == 0) twinkle(color1Value);
        else if (strcmp(anim, "COLOR_WIPE") == 0) colorWipe(color1Value);
        else if (strcmp(anim, "RANDOM_BLINK") == 0) randomBlink(color1Value);
        else if (strcmp(anim, "THEATER_CHASE") == 0) theaterChase(color1Value);
        else if (strcmp(anim, "SNOW") == 0) snow(color1Value);
        else if (strcmp(anim, "ALTERNATING") == 0) {
          // For alternating, we need two colors - if only one provided, use the specified color and blue
          if (color2Value == 0) color2Value = COLOR_BLUE;
          alternatingColors(color1Value, color2Value);
        }
        else if (strcmp(anim, "GRADIENT") == 0) gradientFade(5, color1Value);
        else if (strcmp(anim, "BOUNCING_BALL") == 0) bouncingBall(color1Value);
        else if (strcmp(anim, "RUNNING_LIGHTS") == 0) runningLights(color1Value);
        else if (strcmp(anim, "STACKED_BARS") == 0) stackedBars(50, color1Value);
      }
    }
  }
}
