
#include <Servo.h> 
#include <FastLED.h>
 
Servo lowerNeck;                 
Servo upperNeck;
Servo rotate;

#define LED_COUNT 9

CRGB leds[LED_COUNT];
 
void setup() 
{ 
  Serial.begin(9600);
  lowerNeck.attach(3); 
  upperNeck.attach(4);
  rotate.attach(5);
  
  lowerNeck.write(0);
  upperNeck.write(100);
  rotate.write(90);
  
  FastLED.addLeds<WS2812, 13, GRB>(leds, LED_COUNT);
  
  for (int i = 0; i < LED_COUNT; i++){
    
    leds[i] = CRGB(0,0,5);
  }
  FastLED.show();
  delay(1000);
  for (int i = 0; i < LED_COUNT; i++){
    
    leds[i] = CRGB(0,0,0);
  }
  for (int i = 5; i < LED_COUNT; i++){
    leds[i] = CRGB(5,5,5);
  }
  leds[1] = CRGB(0,5,0);
  FastLED.show();
} 
 
 
void loop() 
{ 
  
  if (Serial.available() >0) {
    // Get serial values as comma separated string e.g. '90,90,90'
    int val1 = Serial.readStringUntil(',').toInt();
    Serial.read();
    int val2 = Serial.readStringUntil(',').toInt();
    Serial.read();
    int rotation = Serial.readString().toInt();
    Serial.print(val1);
    Serial.print('.');
    Serial.print(val2);
    Serial.print('.');
    Serial.println(rotation);
    lowerNeck.write(val1);
    upperNeck.write(val2);
    rotate.write(rotation);
  }
} 

