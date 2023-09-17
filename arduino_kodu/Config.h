#ifndef CONFIG_H
#define CONFIG_H
/**
 * @file config.h
 * @brief Configuration file for the Arduino sketch.
 * @details This file contains the configuration for the Arduino sketch.
 */

#define SERVO_PIN_OFFSET 2 // Legacy, used to identify pin from pi communication
// Left Leg
#define PIN_SLLH 9 // Servo left leg hip
#define PIN_SLLK 10 // Servo left leg knee
#define PIN_SLLA 11 // Servo left leg ankle
// Right Leg
#define PIN_SRLH 6 // Servo right leg hip
#define PIN_SRLK 7 // Servo right leg knee
#define PIN_SRLA 8 // Servo right leg ankle
// Neck
#define PIN_SNT 2 // Servo neck tilt
#define PIN_SNP 3 // Servo neck pan
// Sway
#define PIN_SLLHP 4 // Servo left leg hip piovot (unused)
#define PIN_SRLHP 5 // Servo right leg hip pivot (unused)

#define LEG_LENGTH_SHIN 94.0 // Length of shin
#define LEG_LENGTH_THIGH 94.0 // Length of thigh
#define LEG_LENGTH_FOOT 28.0 // Length of foot

#define EASING_TYPE EASE_QUADRATIC_IN_OUT
#define ENABLE_EASE_QUADRATIC
#define SERVO_SPEED_MIN 20
#define SERVO_SPEED_MAX 80

//#define DEBUG

#define SERVO_COUNT 8 // Number of servos to be controlled by ServoEasing

#define LEG_IK_MIN 140 // Min solvable height of leg between hip and ankle
#define LEG_IK_MAX 170 // Max solvable height of leg between hip and ankle

#define NOVAL 1000

#define MPU6050_ENABLED // Enable MPU6050
//#define MPU6050_DEBUG // Debug in serial plotter


// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: attach() disregards this, set PosRest to be within range of the servo's physical boundaries
int PosMin[SERVO_COUNT] = {20, 5, 40, 20, 5, 15, 60, 20};
int PosMax[SERVO_COUNT] = {160, 175, 180, 160, 175, 180, 120, 160};
int PosSleep[SERVO_COUNT] = {70, PosMin[1], PosMax[2], 110, PosMax[4], PosMin[5], PosMax[7], 90};
//int PrepRestFromSleep[SERVO_COUNT] = {80, PosMin[1], PosMax[2], 100, PosMax[4], PosMin[5], S7_REST, 80, S9_REST};
//int PrepSleepFromRest[SERVO_COUNT] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 80, S9_REST};

// Starting positions
int PosStart[SERVO_COUNT] = {30, 21, 94, 149, 158, 85, 90, 90};



//int PosRest[SERVO_COUNT] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST};
int PosRest[SERVO_COUNT] = {30, 21, 94, 149, 158, 85, 90, 90};

int PosConfig[SERVO_COUNT] = {90, 90, 90, 90, 90, 90, 90, 90};

// Poses
int PosStand[SERVO_COUNT] = {110, 110, 110, 70, 70, 70, NOVAL, NOVAL};
int PosLookLeft[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 180};
int PosLookRight[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL,  NOVAL, NOVAL, 0};
int PosLookRandom[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, -1, -1}; // Made random by calling the function moveRandom() if the value is -1
int PosLookUp[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 60, 90};
int PosLookDown[SERVO_COUNT] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 120, 90};

// Array of poses except PosRest and PosSleep (which are used for initialization and reset of position)
int *Poses[] = {PosStand, PosLookLeft, PosLookRight, PosLookUp, PosLookDown, PosLookRandom};

void blinkLED()
{
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
}

/**
 * Custom logging function to avoid having to wrap every Serial.println() in #ifdef DEBUG
*/
void cLog(String message, boolean newline = true)
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

#endif
