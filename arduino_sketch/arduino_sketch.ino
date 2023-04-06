/**
 * @file arduino_sketch2.ino
 * @brief Arduino sketch to control a 9 servo robot
 * @details This sketch animates a 9 servo bipedal robot using the ServoEasing library.
 * See the README.md file for more information.
 */

#include <Arduino.h>
#include "Config.h"
#include "Order.h"
#include "PiConnect.h"
#include "ServoManager.h"

PiConnect pi;
ServoManager servoManager;

bool isResting = false;
// boot time in millis
unsigned long bootTime;
// wait start time in millis
unsigned long sleepTime;

void setup()
{
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(11, OUTPUT);   // sets the digital pin as output
    digitalWrite(11, LOW); // sets the digital pin on
    Serial.begin(115200);
    servoManager.setSpeed(SERVO_SPEED_MIN);

    // Seed random number generator
    randomSeed(analogRead(0));

    servoManager.moveServos(PrepRestFromSleep); // Move hips and head to try and balance
    doRest();
    //Serial.println(F("Start loop"));
}
void doRest()
{
  isResting = true;
  servoManager.moveServos(PosRest);
}

void loop()
{
    // Check for serial connection and connect, or wait for orders if connected
    if (pi.isConnected() == false)
      PiConnect::checkForConnection(); // Say hello and wait for response
    
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
    // Set tSpeed to between SERVO_SPEED_MIN and SERVO_SPEED_MAX
    servoManager.setSpeed(random(SERVO_SPEED_MIN, SERVO_SPEED_MAX));
    // Radomly select a pose and move to it (not stand)
    // uint8_t tPoseIndex = random(1, sizeof(Poses) / sizeof(Poses[0]));

    //Serial.print(F("Pose: "));
    //Serial.println(tPoseIndex);
    //moveServos(Poses[tPoseIndex]);
    servoManager.moveServos(PosLookRandom);

    // Reset to slow speed
    servoManager.setSpeed(SERVO_SPEED_MIN);

}

void getOrdersFromPi()
{
  if(Serial.available() == 0) return;
  // The first byte received is the instruction
  Order order_received = PiConnect::read_order();

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
        if(DEBUG)
        {
          PiConnect::write_order(SERVO);
          PiConnect::write_i16(servo_angle);
        }
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
        PiConnect::write_order(ERROR);
        PiConnect::write_i16(404);
      }
      return;
    }
  }
}

