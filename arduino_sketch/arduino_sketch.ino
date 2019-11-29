#include <Servo.h> 
 
Servo lowerNeck;                 
Servo upperNeck;
Servo rotate;
 
void setup() 
{ 
  Serial.begin(9600);
  lowerNeck.attach(3); 
  upperNeck.attach(4);
  rotate.attach(5);
  
  lowerNeck.write(0);
  upperNeck.write(100);
  rotate.write(90);
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
//    Serial.print(val1);
//    Serial.print('.');
//    Serial.print(val2);
//    Serial.print('.');
//    Serial.println(rotation);
    lowerNeck.write(val1);
    upperNeck.write(val2);
    rotate.write(rotation);
  }
} 

