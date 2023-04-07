#ifndef CONFIG_H
#define CONFIG_H
/**
 * @file config.h
 * @brief Configuration file for the Arduino sketch.
 * @details This file contains the configuration for the Arduino sketch.
 */

#define SERVO_PIN_OFFSET 2
#define SERVO1_PIN 5
#define SERVO2_PIN 6
#define SERVO3_PIN 7
#define SERVO4_PIN 8
#define SERVO5_PIN 9
#define SERVO6_PIN 10
#define SERVO7_PIN 2
#define SERVO8_PIN 3
#define SERVO9_PIN 4

#define EASING_TYPE EASE_QUADRATIC_IN_OUT
#define ENABLE_EASE_QUADRATIC
#define SERVO_SPEED_MIN 50
#define SERVO_SPEED_MAX 100

// If DEBUG is set to true, the arduino will send back all the received messages
#define DEBUG false

#define MAX_EASING_SERVOS 9

#define S1_REST 160 // Left Leg - Hip
#define S2_REST 180 // Left Leg - Knee
#define S3_REST 90  // Left Leg - Ankle
#define S4_REST 20  // Right Leg - Hip
#define S5_REST 0   // Right Leg - Knee
#define S6_REST 90  // Right Leg - Ankle
#define S7_REST 0   // Neck elevation (unused)
#define S8_REST 90  // Neck tilt
#define S9_REST 90  // Neck pan

// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: attach() disregards this, set PosSleep to be within range of the servo's physical boundaries
int PosMin[MAX_EASING_SERVOS] = {20, 5, 40, 20, 5, 15, 40, 60, 20};
int PosMax[MAX_EASING_SERVOS] = {160, 175, 180, 160, 175, 180, 90, 120, 160};
int PosSleep[MAX_EASING_SERVOS] = {70, PosMin[1], PosMax[2], 110, PosMax[4], PosMin[5], S7_REST, PosMax[7], S9_REST};
int PrepRestFromSleep[MAX_EASING_SERVOS] = {80, PosMin[1], PosMax[2], 100, PosMax[4], PosMin[5], S7_REST, 80, S9_REST};
int PrepSleepFromRest[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 80, S9_REST};

// Starting positions @todo make this pose the legs just above their unpowered position
int PosRest[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST};

// Poses
int PosStand[MAX_EASING_SERVOS] = {110, 110, 110, 70, 70, 70, S7_REST, S8_REST, S9_REST};
int PosLookLeft[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 180};
int PosLookRight[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 0};
int PosLookRandom[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, -1, -1}; // Made random by calling the function moveRandom() if the value is -1
int PosLookUp[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 60, S9_REST};
int PosLookDown[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 120, S9_REST};

// Array of poses except PosRest and PosSleep (which are used for initialization and reset of position)
int *Poses[] = {PosStand, PosLookLeft, PosLookRight, PosLookUp, PosLookDown, PosLookRandom};

void blinkLED()
{
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
}

#endif
