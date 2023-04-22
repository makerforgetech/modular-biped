#ifndef CONFIG_H
#define CONFIG_H
/**
 * @file config.h
 * @brief Configuration file for the Arduino sketch.
 * @details This file contains the configuration for the Arduino sketch.
 */

#define SERVO_PIN_OFFSET 2
// Left Leg
#define SERVO1_PIN 9
#define SERVO2_PIN 10
#define SERVO3_PIN 11
// Right Leg
#define SERVO4_PIN 6
#define SERVO5_PIN 7
#define SERVO6_PIN 8
// Neck
#define SERVO7_PIN 2
#define SERVO8_PIN 3
// Sway
#define SERVO9_PIN 4
#define SERV09_PIN 5

#define EASING_TYPE EASE_QUADRATIC_IN_OUT
#define ENABLE_EASE_QUADRATIC
#define SERVO_SPEED_MIN 50
#define SERVO_SPEED_MAX 100

#define DEBUG

#define MAX_EASING_SERVOS 9

// 144, 158, 85, 35, 21, 94, 0, 120, 90, 

// #define S1_REST 160 // Left Leg - Hip
// #define S2_REST 180 // Left Leg - Knee
// #define S3_REST 90  // Left Leg - Ankle
// #define S4_REST 20  // Right Leg - Hip
// #define S5_REST 0   // Right Leg - Knee
// #define S6_REST 90  // Right Leg - Ankle
// #define S7_REST 0   // Neck elevation (unused)
// #define S8_REST 90  // Neck tilt
// #define S9_REST 90  // Neck pan

#define LEG_IK_MIN 140
#define LEG_IK_MAX 170

#define NOVAL 1000


// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: attach() disregards this, set PosRest to be within range of the servo's physical boundaries
int PosMin[MAX_EASING_SERVOS] = {20, 5, 40, 20, 5, 15, 40, 60, 20};
int PosMax[MAX_EASING_SERVOS] = {160, 175, 180, 160, 175, 180, 90, 120, 160};
int PosSleep[MAX_EASING_SERVOS] = {70, PosMin[1], PosMax[2], 110, PosMax[4], PosMin[5], 0, PosMax[7], 90};
//int PrepRestFromSleep[MAX_EASING_SERVOS] = {80, PosMin[1], PosMax[2], 100, PosMax[4], PosMin[5], S7_REST, 80, S9_REST};
//int PrepSleepFromRest[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 80, S9_REST};

// Starting positions
int PosStart[MAX_EASING_SERVOS] = {30, 21, 94, 149, 158, 85, 0, 120, 90};



//int PosRest[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST};
int PosRest[MAX_EASING_SERVOS] = {30, 21, 94, 149, 158, 85, 0, 120, 90};

int PosConfig[MAX_EASING_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90, 90};

// Poses
int PosStand[MAX_EASING_SERVOS] = {110, 110, 110, 70, 70, 70, NOVAL, NOVAL, NOVAL};
int PosLookLeft[MAX_EASING_SERVOS] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 180};
int PosLookRight[MAX_EASING_SERVOS] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 0};
int PosLookRandom[MAX_EASING_SERVOS] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, -1, -1}; // Made random by calling the function moveRandom() if the value is -1
int PosLookUp[MAX_EASING_SERVOS] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 60, 90};
int PosLookDown[MAX_EASING_SERVOS] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, 120, 90};

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
