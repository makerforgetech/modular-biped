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
#include "InverseK.h"

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
#define S3_REST 90  // Left Leg - Ankle
#define S4_REST 20  // Right Leg - Hip
#define S5_REST 0   // Right Leg - Knee
#define S6_REST 90  // Right Leg - Ankle
#define S7_REST 0   // Neck elevation (unused)
#define S8_REST 90  // Neck tilt
#define S9_REST 90  // Neck pan

// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: attach() disregards this, set PosSleep to be within range of the servo's physical boundaries
int PosMin[MAX_EASING_SERVOS] = {20, 5, 15, 20, 5, 15, 40, 60, 20};
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

void blinkLED();

uint16_t tSpeed;

void setup()
{
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(11, OUTPUT);   // sets the digital pin as output
    digitalWrite(11, LOW); // sets the digital pin on
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
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex)
    {
        // Set easing type to EASING_TYPE
        ServoEasing::ServoEasingArray[tIndex]->setEasingType(EASING_TYPE);
        ServoEasing::ServoEasingArray[tIndex]->setMinMaxConstraint(PosMin[tIndex], PosMax[tIndex]);
    }
    // Wait for servos to reach start position.
    delay(3000);


    moveServos(PrepRestFromSleep); // Move hips and head to try and balance
    moveServos(PosRest);

    testInverseK();
    demoAll();

    Serial.println(F("Move to sleep"));
    moveServos(PrepSleepFromRest);
    moveServos(PosSleep);
    delay(5000); // Final delay to allow time to stop if needed
    Serial.println(F("Move to rest ahead of main loop"));
    moveServos(PosRest);
    Serial.println(F("Start loop"));
}

long moveRandom(int index)
{
    return random(PosMin[index], PosMax[index]);
}

// Quick conversion from the Braccio angle system to radians
float b2a(float b)
{
    return b / 180.0 * PI - HALF_PI;
}

// Quick conversion from radians to the Braccio angle system
float a2b(float a)
{
    return (a + HALF_PI) * 180 / PI;
}

void testInverseK()
{
    Serial.println("Test Inverse Kinematics");
    // Set all servos to 90 degrees
    int centerAll[MAX_EASING_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90, 90};
    Serial.println("All at 90");
    moveServos(centerAll);
    delay(10000);

    // Create links(length, min angle, max angle)
    Link dummy, hipL, kneeL, ankleL, dummy2, hipR, kneeR, ankleR;
    dummy.init(0, 0, 0); // Needed as the library needs 4 links
    hipL.init(94, b2a(20), b2a(160));
    kneeL.init(94, b2a(15), b2a(90));
    ankleL.init(28, b2a(40), b2a(180));

    dummy2.init(0, 0, 0);
    hipR.init(94, b2a(20), b2a(160));
    kneeR.init(94, b2a(90), b2a(175));
    ankleR.init(28, b2a(40), b2a(180));

    InverseK.attach(dummy, hipL, kneeL, ankleL);

    InverseK2.attach(dummy2, hipR, kneeR, ankleR);

    // Variables to populate when finding solution
    float d, hl, kl, al, d2, hr, kr, ar;

    // Iterate over all values from 100 to 300 in steps of 10
    // Expected outcome: @todo cache these values
    // 130,-,36.36,174.64,162.00
    // 140,-,41.77,165.33,165.90
    // 150,-,47.66,154.88,170.46
    // 160,134.68,20.69,40.63,54.37,142.63,176.00
    // 170,129.46,29.70,40.83,50.54,171.66,40.79
    // 180,123.51,40.22,40.26,55.36,161.84,45.79
    // 190,116.93,51.82,41.24,60.86,150.69,51.45
    // 200,108.02,67.89,41.09,67.51,137.25,58.24
    // 210,97.85,84.12,53.03,76.85,118.44,67.71
    for (int i = 100; i < 300; i += 10)
    {
        int solved = 0;
        Serial.print(i);
        Serial.print(',');
        if (InverseK.solve(0, 0, i, d, hl, kl, al))
        {
            solved ++;
            Serial.print(a2b(hl));
            Serial.print(',');
            Serial.print(a2b(kl));
            Serial.print(',');
            Serial.print(a2b(al));
            Serial.print(',');
        }
        else
        {
            Serial.print("-");
            Serial.print(',');
        }
        if (InverseK2.solve(0, 0, i, d2, hr, kr, ar))
        {
            solved ++;
            Serial.print(a2b(hr));
            Serial.print(',');
            Serial.print(a2b(kr));
            Serial.print(',');
            Serial.println(a2b(ar));
        }
        else
        {
            Serial.println("-");
        }
        // If both legs are solved, move to that position and wait 10 seconds
        if (solved == 2)
        {
            int thisMove[MAX_EASING_SERVOS] = {a2b(hl), a2b(kl), a2b(al), a2b(hr), a2b(kr), a2b(ar), 90, 90, 90};
            moveServos(thisMove);
            delay(2000);
        }
    }
}

void blinkLED()
{
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
}

void moveServos(int *Pos)
{
    for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex)
    {
        if (Pos[tIndex] != -1)
            ServoEasing::ServoEasingNextPositionArray[tIndex] = Pos[tIndex];
        else 
            ServoEasing::ServoEasingNextPositionArray[tIndex] = moveRandom(tIndex); // If scripted value is -1, generate random position based on range of currently indexed servo
    }
    setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    while (ServoEasing::areInterruptsActive())
    {
        blinkLED();
    }
}

void demoAll()
{
    Serial.println(F("Demo all poses at minimum speed"));
    setSpeed(SERVO_SPEED_MIN);
    // Cycle through all poses and move all servos to them
    for (uint8_t tPoseIndex = 0; tPoseIndex < sizeof(Poses) / sizeof(Poses[0]); ++tPoseIndex)
    {
        Serial.print(F("Pose: "));
        Serial.println(tPoseIndex);
        moveServos(Poses[tPoseIndex]);
        delay(1000);
        Serial.println(F("Rest"));
        moveServos(PosRest);
        delay(2000);
    }
}

void setSpeed(uint16_t pSpeed)
{
    tSpeed = pSpeed;
    setSpeedForAllServos(tSpeed);
    Serial.print(F("Speed set: "));
    Serial.println(tSpeed);
}

void loop()
{
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
