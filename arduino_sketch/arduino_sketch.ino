

/**
 * @file arduino_sketch.ino
 * @brief Arduino sketch to control a bipedal robot
 * @details This sketch animates a bipedal robot using the ServoEasing library.
 * 
 * Config.h should be used to configure implementation specific values.
 * See the README.md file for more information.
 */

#include "Dependencies.h"

using namespace ModularBiped;

ServoManager servoManager;
SerialConnection bipedSerial(&servoManager);
Animation animator(&servoManager);

void setup()
{
  // Init LED pin
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Init serial
  Serial.begin(115200);

  // Init ServoManager
  servoManager.doInit();

  // Seed random number generator
  randomSeed(analogRead(0));

  // Custom log message (enable DEBUG in Config.h to see this)
  cLog("Start loop");
}

void loop()
{
  bipedSerial.getAllOrdersFromSerial();
  servoManager.servoLoop(); // Handle pending movement and adjust hips
  animator.animateRandomly(!bipedSerial.getOrdersReceived()); // Only if serial control is not active

  //  This needs to be here rather than in the ServoManager, otherwise it doesn't work. @TODO confirm
  // while (ServoEasing::areInterruptsActive())
  // {
  //   blinkLED();
  // }
}