/**
 * @file arduino_sketch2.ino
 * @brief Arduino sketch to control a 9 servo robot
 * @details This sketch animates a 9 servo bipedal robot using the ServoEasing library.
 * See the README.md file for more information.
 */

#include <Arduino.h>

#define MAX_EASING_SERVOS 9
#include "ServoEasing.hpp"
#include "config.h"

// Left Leg
ServoEasing Servo1;
ServoEasing Servo2;
ServoEasing Servo3;
// Right Leg
ServoEasing Servo4;
ServoEasing Servo5;
ServoEasing Servo6;
// Neck elevation (unused)
ServoEasing Servo7;
// Neck tilt
ServoEasing Servo8;
// Neck pan
ServoEasing Servo9;

#define S1_REST 160 // Left Leg - Hip
#define S2_REST 180 // Left Leg - Knee
#define S3_REST 90 // Left Leg - Ankle
#define S4_REST 20 // Right Leg - Hip
#define S5_REST 0 // Right Leg - Knee
#define S6_REST 90 // Right Leg - Ankle
#define S7_REST 0 // Neck elevation (unused)
#define S8_REST 90 // Neck tilt
#define S9_REST 90 // Neck pan

// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: attach() disregards this, set PosSleep to be within range of the servo's physical boundaries
int PosMin[MAX_EASING_SERVOS] = { 20, 5, 15, 20, 5, 15, 40, 60 ,20 };
int PosMax[MAX_EASING_SERVOS] = { 160, 175, 180, 160, 175, 180, 90, 120, 160 };
int PosSleep[MAX_EASING_SERVOS] = { 70, PosMin[1], PosMax[2], 110, PosMax[4], PosMin[5], S7_REST, PosMax[7], S9_REST };
int PrepRestFromSleep[MAX_EASING_SERVOS] = { 80, PosMin[1], PosMax[2], 100, PosMax[4], PosMin[5], S7_REST, 80, S9_REST };
int PrepSleepFromRest[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 80, S9_REST };

// Starting positions @todo make this pose the legs just above their unpowered position
int PosRest[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST };

// Poses
int PosStand[MAX_EASING_SERVOS] = {110, 110, 110, 70, 70, 70, S7_REST, S8_REST, S9_REST };
int PosLookLeft[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 180 };
int PosLookRight[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 0 };
int PosLookRandom[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, random(60, 120), random(20, 160) }; //@todo make random each call
int PosLookUp[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 60, S9_REST };
int PosLookDown[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 120, S9_REST };

// Array of poses except PosRest and PosSleep (which are used for initialization and reset of position)
int *Poses[] = {PosStand, PosLookLeft, PosLookRight, PosLookUp, PosLookDown, PosLookRandom};

void blinkLED();

uint16_t tSpeed;

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(115200);
    tSpeed = SERVO_SPEED_MIN;

    // Seed random number generator
    randomSeed(analogRead(0));

    Servo1.attach(SERVO1_PIN, PosSleep[0]);
    Servo2.attach(SERVO2_PIN, PosSleep[1]);
    Servo3.attach(SERVO3_PIN, PosSleep[2]);
    Servo4.attach(SERVO4_PIN, PosSleep[3]);
    Servo5.attach(SERVO5_PIN, PosSleep[4]);
    Servo6.attach(SERVO6_PIN, PosSleep[5]);
    Servo7.attach(SERVO7_PIN, PosSleep[6]);
    Servo8.attach(SERVO8_PIN, PosSleep[7]);
    Servo9.attach(SERVO9_PIN, PosSleep[8]);

    // Loop over ServoEasing::ServoEasingArray and attach each servo
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex) {
        // Set easing type to EASING_TYPE
        ServoEasing::ServoEasingArray[tIndex]->setEasingType(EASING_TYPE);
        ServoEasing::ServoEasingArray[tIndex]->setMinMaxConstraint(PosMin[tIndex],PosMax[tIndex]);     
    }
    // Wait for servos to reach start position.
    delay(3000);

    moveServos(PrepRestFromSleep); // Move hips and head to try and balance
    moveServos(PosRest);

    demoAll();

    Serial.println(F("Move to sleep"));
    moveServos(PrepSleepFromRest);
    moveServos(PosSleep);
    delay(5000); // Final delay to allow time to stop if needed
    Serial.println(F("Move to rest ahead of main loop"));
    moveServos(PosRest);
    Serial.println(F("Start loop"));
}

void blinkLED() {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
}

void moveServos(int *Pos) {
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex) {
        ServoEasing::ServoEasingNextPositionArray[tIndex] = Pos[tIndex];
    }
    setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    while (ServoEasing::areInterruptsActive()) {
        blinkLED();
    }
}

void demoAll() {
    Serial.println(F("Demo all poses at minimum speed"));
    setSpeed(SERVO_SPEED_MIN);
    // Cycle through all poses and move all servos to them
    for (uint8_t tPoseIndex = 0; tPoseIndex < sizeof(Poses) / sizeof(Poses[0]); ++tPoseIndex) {
        Serial.print(F("Pose: "));
        Serial.println(tPoseIndex);
        moveServos(Poses[tPoseIndex]);
        delay(1000);
        Serial.println(F("Rest"));
        moveServos(PosRest);
        delay(2000);
    }
    
}

void setSpeed(uint16_t pSpeed) {
    tSpeed = pSpeed;
    setSpeedForAllServos(tSpeed);
    Serial.print(F("Speed set: "));
    Serial.println(tSpeed);
}

void loop() {
    // Set tSpeed to between SERVO_SPEED_MIN and SERVO_SPEED_MAX
    setSpeed(random(SERVO_SPEED_MIN, SERVO_SPEED_MAX));
    // Radomly select a pose and move to it (not stand)
    uint8_t tPoseIndex = random(1, sizeof(Poses) / sizeof(Poses[0]));

    Serial.print(F("Pose: "));
    Serial.println(tPoseIndex);
    moveServos(Poses[tPoseIndex]);

    // Wait between 1 and 5 seconds
    delay(random(1000, 5000));
    
    // Reset to slow speed
    setSpeed(SERVO_SPEED_MIN);

    // Move back to resting pose
    Serial.println(F("Rest"));
    moveServos(PosRest);

    // Wait between 5 and 30 seconds
    delay(random(5000, 30000));

}
