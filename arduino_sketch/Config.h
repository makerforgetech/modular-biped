#pragma once
/**
 * @file config.h
 * @brief Configuration file for the Arduino sketch.
 * @details This file contains the configuration for the Arduino sketch.
 */
namespace ModularBiped {
    namespace Config {
        // Left Leg
        constexpr int PIN_SLLH = 9;  // Servo left leg hip
        constexpr int PIN_SLLK = 10; // Servo left leg knee
        constexpr int PIN_SLLA = 11; // Servo left leg ankle

        // Right Leg
        constexpr int PIN_SRLH = 6;  // Servo right leg hip
        constexpr int PIN_SRLK = 7;  // Servo right leg knee
        constexpr int PIN_SRLA = 8;  // Servo right leg ankle

        // Neck
        constexpr int PIN_SNT = 2; // Servo neck tilt
        constexpr int PIN_SNP = 3; // Servo neck pan

        // Sway (currently unused)
        constexpr int PIN_SLLHP = 4; // Servo left leg hip pivot
        constexpr int PIN_SRLHP = 5; // Servo right leg hip pivot

        // Leg dimensions
        constexpr double LEG_LENGTH_SHIN = 94.0;  // Length of shin
        constexpr double LEG_LENGTH_THIGH = 94.0; // Length of thigh
        constexpr double LEG_LENGTH_FOOT = 28.0;  // Length of foot

        // Servo adjustments
        constexpr int HIP_ADJUSTMENT = 120; // Starting angle of hip relative to IK model
        constexpr int KNEE_ADJUSTMENT = 90;
        constexpr int ANKLE_ADJUSTMENT = 85;

        // Servo easing configuration
        #define EASING_TYPE EASE_QUADRATIC_IN_OUT
        constexpr int SERVO_SPEED_MIN = 30; // Minimum servo speed
        constexpr int SERVO_SPEED_MAX = 80; // Maximum servo speed

        // Servo count
        constexpr int SERVO_COUNT = 8; // Number of servos to be controlled by ServoEasing

        // Inverse kinematics limits
        constexpr int LEG_IK_MIN = 75;  // Minimum solvable height of leg between hip and ankle
        constexpr int LEG_IK_MAX = 180; // Maximum solvable height of leg between hip and ankle

        // Special values
        constexpr int NOVAL = 1000;

        // Feature flags
        #define MPU6050_ENABLED // Enable MPU6050
        // #define MPU6050_DEBUG // Debug in serial plotter
        // #define DEBUG // Main debug via cLog method

        // #define SERVO_MODE_PIN_ENABLED // Enable behavior related to servoModePin
        // #define SERVO_MODE_OVERRIDE 3 // Override input from pin and set specific mode for debugging
        #define RESTRAIN_PIN_ENABLED // Enable behavior related to restrainPin

        // Uncomment to enable servo calibration
        // #define SERVO_CALIBRATION_ENABLED // Enable servo calibration (see ServoManager::calibrate())
        // #define SERVO_CALIBRATION_SYMMETRICAL // Calculate and apply equivalent changes on the other leg.

        // Servo position arrays
        int PosMin[SERVO_COUNT] = {0, 0, 5, 0, 0, 20, 60, 30};
        int PosMax[SERVO_COUNT] = {180, 180, 165, 180, 180, 180, 120, 150};
        int PosSleep[SERVO_COUNT] = {40, 60, 95, 140, 120, 85, PosMax[7], 90};
        int PosStart[SERVO_COUNT] = {60, 0, 165, 120, 180, 20, 90, 90};
        int PosBackpack[SERVO_COUNT] = {30, 5, 90, 130, 120, 160, 90, 90}; // Position legs to support when mounted to backpack
        int PosStraight[SERVO_COUNT] = {45, 90, 165, 135, 90, 20, 90, 90}; // Straighten legs and point feet to fit in backpack upright
        int PosRest[SERVO_COUNT] = {60, 0, 165, 120, 180, 20, 90, 90};
        int PosConfig[SERVO_COUNT] = {90, 90, 90, 90, 90, 90, 90, 90};

        // Poses
        int PosStand[SERVO_COUNT] = {45, 70, 80, 135, 110, 100, NOVAL, NOVAL};
        int PosLookLeft[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 180};
        int PosLookRight[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 0};
        int PosLookRandom[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, -1, -1}; // Made random by calling the function moveRandom() if the value is -1
        int PosLookUp[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 60, 90};
        int PosLookDown[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 120, 90};

        // Array of poses except PosRest and PosSleep (used for initialization and reset of position)
        int *Poses[] = {PosStand, PosLookLeft, PosLookRight, PosLookUp, PosLookDown, PosLookRandom};

        int *StartingPos = PosStart;
        int servoMode = 2; // Default to standing pose

        #ifdef SERVO_MODE_PIN_ENABLED
        constexpr int servoModePin = PIN_A1;
        // Define 5 threshold values between 0 and 1024 for the 5 leg modes
        constexpr int servoModeThresholds[5] = {205, 410, 615, 820, 1024};
        String servoModeNames[] = {"Disabled", "Sit", "Stand", "BackPack", "Straight"};
        int *servoModePoses[] = {PosStart, PosStart, PosStart, PosBackpack, PosStraight};
        #endif

        constexpr int restrainPin = 12;
        bool restrainingBolt = false; // Needed in either case as it is checked by ServoManager
    }

  static void blinkLED()
  {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(100);
      digitalWrite(LED_BUILTIN, LOW);
      delay(100);
  }
  
  /**
  * Custom logging function to avoid having to wrap every Serial.println() in #ifdef DEBUG
  */
  static void cLog(String message, boolean newline = true)
  {
      #ifdef DEBUG
      if (newline)
      {
          Serial.println(message);
      }
      else
      {
          Serial.print(message);
      }
      #endif
  }
}
