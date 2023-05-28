/**
 * @file arduino_sketch2.ino
 * @brief Arduino sketch to control a 9 servo robot
 * @details This sketch animates a 9 servo bipedal robot using the ServoEasing library.
 * See the README.md file for more information.
 */

#include <Arduino.h>
#include "ServoEasing.hpp" // Must be here otherwise method fails: setEaseToForAllServosSynchronizeAndStartInterrupt
#include "Config.h"
#include "Order.h"
#include "PiConnect.h"
#include "ServoManager.h"

//#define DEBUG

PiConnect pi;
ServoManager servoManager;

bool isResting = false;
// boot time in millis
unsigned long bootTime;
// wait start time in millis
unsigned long sleepTime;

boolean calibrateRest = true;

void setup()
{
    // Init LED pin
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(11, OUTPUT);   // sets the digital pin as output
    digitalWrite(11, LOW); // sets the digital pin on
    // Init boot time for sleep function
    bootTime = millis();
    // Init serial
    Serial.begin(115200);
    // Init ServoManager
    servoManager.doInit();
    servoManager.setSpeed(SERVO_SPEED_MIN);

    // Seed random number generator
    randomSeed(analogRead(0));

    //allTo90();

    // Move to rest position + calculate IK and store as rest position
    doRest();

    // Custom log message (enable DEBUG in Config.h to see this)
    cLog("Start loop");
}
/**
 * @brief Set all servos to 90 degrees for mechanical calibration. Wait for 20 seconds.
*/
void allTo90() 
{
  cLog("All at 90");
  servoManager.moveServos(PosConfig);
  setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());
  while (ServoEasing::areInterruptsActive())
  {
      blinkLED();
  }
  delay(20000);
 
}
/**
 * @brief Move to rest position. Either using stored values or by calculating using inverse kinematics and storing result for next time.
*/
void doRest()
{
  cLog("Resting");
  isResting = true;
  // Reset to slow speed
  servoManager.setSpeed(SERVO_SPEED_MIN);
  if (calibrateRest == false)
  {
    servoManager.moveServos(PosRest);
  }
  else 
  {
    //Mid value between LEG_IK_MIN and LEG_IK_MAX
    float mid = LEG_IK_MIN + ((LEG_IK_MAX - LEG_IK_MIN) / 2);
    servoManager.moveLegsAndStore(mid, 0, PosRest); // Move legs and store as rest position
    // iterate over PosRest and output values:
    #ifdef DEBUG
    for (int i = 0; i < 9; i++)
    {
        Serial.print(PosRest[i]);
        Serial.print(", ");
    }
    Serial.println();
    #endif
    calibrateRest = false;
  }
  setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());
}

void loop()
{
  
  // This needs to be here rather than in the ServoManager, otherwise it doesn't work.
  while (ServoEasing::areInterruptsActive())
  {
      blinkLED();
  }

  // Check for orders from pi
  getOrdersFromPi();

  // if not sleeping, animate randomly
  // Orders from pi will set sleep time so that the animation does not take precedence
  if (!isSleeping()){
    if (isResting)
    {
      animateRandomly();
      setSleep(random(3000, 5000));
    }
    else {
      doRest();
      setSleep(random(3000, 20000));
    }
    setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());
  }  
}

void setSleep(unsigned long length)
{
    sleepTime = millis() - bootTime + length;
}

boolean isSleeping()
{
    return millis() - bootTime < sleepTime;
}

void animateRandomly()
{
    cLog("Animating");
    isResting = false;
    servoManager.setSpeed(random(SERVO_SPEED_MIN, SERVO_SPEED_MAX));
    
    // Look around randomly and move legs to react
    servoManager.moveServos(PosLookRandom);
    // If head looks down, move legs up, and vice versa
    float headTiltOffset = ServoEasing::ServoEasingNextPositionArray[7] - 90;
    // Attempt to compensate movement of head by adjusting leg height
    // Scale headTiltOffset value between 0 and 180 (inverted) to scale of LEG_IK_MIN and LEG_IK_MAX 
    float legHeight = map(headTiltOffset, 180, 0, LEG_IK_MIN, LEG_IK_MAX); 
    // Move legs to that height
    servoManager.moveLegs(legHeight, 0);
    #ifdef DEBUG
    Serial.print("Moving legs ");
    Serial.print(legHeight);
    Serial.print(" as head tilt was ");
    Serial.println(headTiltOffset);
    #endif  
}

void getOrdersFromPi()
{
  if(Serial.available() == 0) return;
  cLog("Order received: ", false);
  
  // The first byte received is the instruction
  Order order_received = PiConnect::read_order();
  cLog((String) order_received);
  if(order_received == HELLO)
  {
    // If the cards haven't say hello, check the connection
    if(!pi.isConnected())
    {
      pi.setConnected(true);
      PiConnect::write_order(HELLO);
    }
    else
    {
      // If we are already connected do not send "hello" to avoid infinite loop
      PiConnect::write_order(ALREADY_CONNECTED);
    }
  }
  else if(order_received == ALREADY_CONNECTED)
  {
    pi.setConnected(true);
  }
  else
  {
    switch(order_received)
    {
      case SERVO:
      {
        int servo_identifier = PiConnect::read_i8();
        int servo_angle = PiConnect::read_i16();
        #ifdef DEBUG
          PiConnect::write_order(SERVO);
          PiConnect::write_i16(servo_angle);
        #endif
        // sleep animations for 2 seconds to allow pi to control servos
        setSleep(2000);
        servoManager.moveSingleServo(servo_identifier - SERVO_PIN_OFFSET, servo_angle);
        break;
      }
      case PIN:
      {
          int pin = PiConnect::read_i8();
          int value = PiConnect::read_i8();
          pinMode(pin, OUTPUT);
          digitalWrite(pin, value);
          break;
      }
      case READ:
      {
          int pin = PiConnect::read_i8();
          pinMode(pin, INPUT);
          long value = analogRead(pin);
          PiConnect::write_i16(value);
          break;
      }
      // Unknown order
      default:
      {
        PiConnect::write_order(order_received);
        //PiConnect::write_i16(404);
      }
      return;
    }
  }
}
