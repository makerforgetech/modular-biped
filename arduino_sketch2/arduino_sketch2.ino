#include <Arduino.h>

#define MAX_EASING_SERVOS 9
#include "ServoEasing.hpp"
#include "PinDefinitionsAndMore.h"


ServoEasing Servo1;
ServoEasing Servo2;
ServoEasing Servo3;
ServoEasing Servo4;
ServoEasing Servo5;
ServoEasing Servo6;
ServoEasing Servo7;
ServoEasing Servo8;
ServoEasing Servo9;

#define S1_REST 160
#define S2_REST 180
#define S3_REST 90
#define S4_REST 20
#define S5_REST 0
#define S6_REST 90
#define S7_REST 40
#define S8_REST 140
#define S9_REST 90

// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: PosStart disregards this, set the PosStart to be within range of the servo's physical boundaries
int PosMin[MAX_EASING_SERVOS] = { 20, 5, 15, 20, 5, 15, 20, 20 ,20 };
int PosMax[MAX_EASING_SERVOS] = { 160, 175, 180, 160, 175, 180, 160, 160, 160 };

// Starting positions @todo make this pose the legs just above their unpowered position
int PosStart[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST };

// Poses
int PosStand[MAX_EASING_SERVOS] = { 90, 90, 110, 90, 90, 70, S7_REST, S8_REST, S9_REST };
int PosSit[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST };
int PosHeadForward[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, 180, 0, S9_REST };
int PosLookLeft[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 180 };
int PosLookRight[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 0 };
int PosHeadBack[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, 0, 180, S9_REST };
int PosLookDown[MAX_EASING_SERVOS] = { S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, 180, 70, S9_REST };

// Array of poses except PosSit
int *Poses[] = { PosStand, PosHeadForward, PosLookLeft, PosLookRight, PosHeadBack, PosLookDown };

void blinkLED();

uint16_t tSpeed;

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(115200);
    tSpeed = SERVO_SPEED_MIN;

    // Seed random number generator
    randomSeed(analogRead(0));


    Servo1.attach(SERVO1_PIN, PosStart[0]);
    Servo2.attach(SERVO2_PIN, PosStart[1]);
    Servo3.attach(SERVO3_PIN, PosStart[2]);
    Servo4.attach(SERVO4_PIN, PosStart[3]);
    Servo5.attach(SERVO5_PIN, PosStart[4]);
    Servo6.attach(SERVO6_PIN, PosStart[5]);
    Servo7.attach(SERVO7_PIN, PosStart[6]);
    Servo8.attach(SERVO8_PIN, PosStart[7]);
    Servo9.attach(SERVO9_PIN, PosStart[8]);

    // Loop over ServoEasing::ServoEasingArray and attach each servo
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex) {
        // Set easing type to EASING_TYPE
        ServoEasing::ServoEasingArray[tIndex]->setEasingType(EASING_TYPE);
        ServoEasing::ServoEasingArray[tIndex]->setMinMaxConstraint(PosMin[tIndex],PosMax[tIndex]);     
    }
    // Wait for servos to reach start position.
    delay(3000);
    Serial.println(F("Start loop"));
}

void blinkLED() {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
}

void loop() {
    // Set tSpeed to between SERVO_SPEED_MIN and SERVO_SPEED_MAX
    tSpeed = random(SERVO_SPEED_MIN, SERVO_SPEED_MAX);
    setSpeedForAllServos(tSpeed);
    Serial.println(tSpeed);

    // Radomly select a pose and move to it
    uint8_t tPoseIndex = random(0, sizeof(Poses) / sizeof(Poses[0]));
    Serial.print(F("Pose: "));
    Serial.println(tPoseIndex);
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex) {
        ServoEasing::ServoEasingNextPositionArray[tIndex] = Poses[tPoseIndex][tIndex];
    }
    setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    /*
     * Now you can run your program while the servos are moving.
     * Just let the LED blink until servos stop.
     * Since all servos stops at the same time I have to check only one
     */
    while (ServoEasing::areInterruptsActive()) {
        blinkLED();
    }

    // Wait between 1 and 10 seconds
    delay(random(1000, 10000));

    tSpeed = SERVO_SPEED_MIN;

    // Move back to resting pose
    Serial.println(F("Rest"));
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex) {
        ServoEasing::ServoEasingNextPositionArray[tIndex] = PosSit[tIndex];
    }
    setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    while (ServoEasing::areInterruptsActive()) {
        blinkLED();
    }

    // Wait between 5 and 30 seconds
    delay(random(5000, 30000));

}
