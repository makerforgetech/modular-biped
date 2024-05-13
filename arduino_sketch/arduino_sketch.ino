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
#ifdef MPU6050_ENABLED
#include "Mpu6050.h"
#endif

// #define DEBUG

PiConnect pi;
ServoManager servoManager;
#ifdef MPU6050_ENABLED
Mpu6050 tilt;
#endif

bool isResting = false;
// boot time in millis
unsigned long bootTime;
// wait start time in millis
unsigned long sleepTime;

boolean calibrateRest = false;

bool shouldMove = false;

bool piControl = false;

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


  pinMode(backpackPin, INPUT_PULLUP); // sets the digital pin as input
  if (digitalRead(backpackPin) == LOW) // Check once on startup
  {
    Serial.println("Backpack detected");
    backpack = true;
  }

  pinMode(restrainPin, INPUT_PULLUP); // sets the digital pin as input
  if (digitalRead(restrainPin) == LOW) // Check once on startup
  {
    Serial.println("Restraint detected");
    restrainingBolt = true;
  }

  // Init ServoManager
  servoManager.doInit();
  servoManager.setSpeed(SERVO_SPEED_MIN);

  #ifdef MPU6050_ENABLED
  tilt.doInit();
  #endif

  // Seed random number generator
  randomSeed(analogRead(0));

  // allTo90();

  // Move to rest position + calculate IK and store as rest position
  // doRest();

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

  // Reset to slow speed
  servoManager.setSpeed(SERVO_SPEED_MIN);
  if (calibrateRest == false)
  {
    servoManager.moveServos(PosRest);
  }
  else
  {
    // Mid value between LEG_IK_MIN and LEG_IK_MAX
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
  shouldMove = true;
  // setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());
}

void stationarySteps() {
  int left[SERVO_COUNT] = {PosMin[0], PosMin[1], PosMin[2], PosMax[3], PosMax[4], PosMax[5]};
  int right[SERVO_COUNT] = {PosMax[0], PosMax[1], PosMax[2], PosMin[3], PosMin[4], PosMin[5]};
  uint16_t speed = SERVO_SPEED_MIN; // 20 - 60 recommended
  unsigned long delayTime = 200;
  servoManager.setSpeed(speed);
  boolean moveLeft = true;
  while (true)
  {
    if (moveLeft)
      servoManager.moveServos(left);
    else
      servoManager.moveServos(right);

    setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());

    while (ServoEasing::areInterruptsActive())
    {
      blinkLED();
    }

    delay(delayTime);
  }
}

#ifdef MPU6050_ENABLED
void hipAdjust()
{
  tilt.read();
  //Serial.println(tilt.getPitch());
  servoManager.hipAdjust(tilt.getPitch());
  setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());
}
#endif

void loop()
{
  #ifdef SERVO_CALIBRATION_ENABLED
    servoManager.calibrate();
  #endif

  #ifdef MPU6050_ENABLED
  hipAdjust();
  #endif
  //  This needs to be here rather than in the ServoManager, otherwise it doesn't work.
  while (ServoEasing::areInterruptsActive())
  {
    blinkLED();
  }

  // Check for orders from pi
  bool receiving = getOrdersFromPi();
  while(receiving) 
  {
    piControl = true;
    delay(50); // Wait a short time for any other orders
    receiving = getOrdersFromPi();
    shouldMove = !receiving; // Only move when there are no other orders
  }
  
  // Once all orders received (or animating without orders)
  if (shouldMove)
  {
    setEaseToForAllServosSynchronizeAndStartInterrupt(servoManager.getSpeed());
    shouldMove = false;
  }

  // if not sleeping, animate randomly
  // Orders from pi will set sleep time so that the animation does not take precedence
  if (!isSleeping())
  {
    if (isResting && piControl == false) // Only do this if the Pi is not in control (i.e. switched off)
    {
      #ifdef ANIMATE_ENABLED
      animateRandomly();
      #endif
    }
    else
    {
      // doRest();
      isResting = true;
      setSleep(random(1000, 5000));
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
  cLog("Animating");
  isResting = false;
  servoManager.setSpeed(SERVO_SPEED_MIN);

  // Look around randomly and move legs to react
  servoManager.moveServos(PosLookRandom);
  // If head looks down, move legs up, and vice versa
  float headTiltOffset = ServoEasing::ServoEasingNextPositionArray[7] - 90;
  // Attempt to compensate movement of head by adjusting leg height
  // Scale headTiltOffset value between 0 and 180 (inverted) to scale of LEG_IK_MIN and LEG_IK_MAX
  float legHeight = map(headTiltOffset, 180, 0, LEG_IK_MIN, LEG_IK_MAX);
  // Move legs to that height
  // servoManager.moveLegs(LEG_IK_MAX, 0);
  servoManager.moveServos(PosStand);
  shouldMove = true;
#ifdef DEBUG
  Serial.print("Moving legs ");
  Serial.print(legHeight);
  Serial.print(" as head tilt was ");
  Serial.println(headTiltOffset);
#endif
}

boolean getOrdersFromPi()
{
  if (Serial.available() == 0)
    //PiConnect::write_order(ERROR);
    return false;
  cLog("Order received: ", false);

  // The first byte received is the instruction
  Order order_received = PiConnect::read_order();
  cLog((String)order_received);
  if (order_received == HELLO)
  {
    // If the cards haven't say hello, check the connection
    if (!pi.isConnected())
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
  else if (order_received == ALREADY_CONNECTED)
  {
    pi.setConnected(true);
  }
  else
  {
    switch (order_received)
    {
      case SERVO:
      case SERVO_RELATIVE:
      {
        int servo_identifier = PiConnect::read_i8();
        int servo_angle_percent = PiConnect::read_i16();
  #ifdef DEBUG
        PiConnect::write_order(SERVO);
        PiConnect::write_i8(servo_identifier);
        PiConnect::write_i16(servo_angle_percent);
  #endif
        // sleep animations for 2 seconds to allow pi to control servos
        setSleep(2000);
        servoManager.moveSingleServoByPercentage(servo_identifier, servo_angle_percent, order_received == SERVO_RELATIVE);
        return true;
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
        // PiConnect::write_i16(404);
      }
    }
  }
  return false;
}
