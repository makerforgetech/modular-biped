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

    Serial.println("Test 2d Inverse Kinematics");
    // Set all servos to 90 degrees
//    int centerAll[MAX_EASING_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90, 90};
//    Serial.println("All at 90");
//    moveServos(centerAll);
//    delay(2000);


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

float r2d(float rad)
{
  return (rad * 180 / PI);
}

float d2r(float deg)
{
  return (deg * PI / 180);
}

// calculate inverse kinematics for a leg with 3 degrees of freedom along a 2d plane
boolean inverseKinematics2D(float x, float y, float &hipAngle, float &kneeAngle, float &ankleAngle)
{
    float L1 = 94.0; // hip to knee
    float L2 = 94.0; // knee to ankle
    float L3 = 28.0; // ankle to foot

    float hipMinAngle = 20.0; // PosMin[3]
    float hipMaxAngle = 160.0;  // PosMax[3]

    float kneeMinAngle = 5.0; // PosMin[4]
    float kneeMaxAngle = 175.0; // PosMax[4]

    float ankleMinAngle = 40.0; // PosMin[5]
    float ankleMaxAngle = 180.0; // PosMax[5]

    float a = L1;
    float b = L2;
    float c = x;
    // Law of cosines to sides A+ B
    //γ = acos((a² + b² − c²)/(2ab))
    float hip = acos((sq(a) + sq(c) - sq(b)) / (2*a*c));
    // Law of cosines to sides A+ B
    float knee = PI - (hip * 2) ;//acos((sq(a) + sq(b) - sq(c)) / (2*a*c));
    // compute remaining angle
    float ankle = d2r(180) - knee - hip;

    Serial.print(hip);
    Serial.print(" + ");
    Serial.print(knee);
    Serial.print(" + ");
    Serial.print(ankle);
    Serial.print(" = ");
    Serial.println(hip + knee + ankle);

    Serial.print(r2d(hip));
    Serial.print(" - ");
    Serial.print(r2d(knee));
    Serial.print(" - ");
    Serial.println(r2d(ankle));
    Serial.println(" = ");
    Serial.println(r2d(hip + knee + ankle));

    // return false if angles are not numbers
    if (isnan(hip) || isnan(knee) || isnan(ankle))
    {
        return false;
    }

    float rad90 = d2r(90);
    float rad180 = d2r(180);
    float rad60 = d2r(60);

    // Convert the angles to the Braccio angle system
    hipAngle = r2d(rad180 - (hip + d2r(110))); // Inverse and offset
    kneeAngle = r2d(knee - rad90); // Offset 90 to compensate
    ankleAngle = r2d(ankle + rad60); // Offset 60 to compensate

    Serial.print(hipAngle);
    Serial.print(" - ");
    Serial.print(kneeAngle);
    Serial.print(" - ");
    Serial.println(ankleAngle);

    // Check if the angles are within the limits
    if (hipAngle < hipMinAngle || hipAngle > hipMaxAngle || kneeAngle < kneeMinAngle || kneeAngle > kneeMaxAngle || ankleAngle < ankleMinAngle || ankleAngle > ankleMaxAngle)
    {
        return false;
    }

    return true;

}

void calculateOtherLeg(float lHip, float lKnee, float lAnkle, float &rHip, float &rKnee, float &rAnkle)
{
    rHip = 180 - lHip;
    rKnee = 180 - lKnee;
    rAnkle = 180 - lAnkle;
}

void test2dInverseK()
{
    
    float hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR;
    int thisMove[MAX_EASING_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90, 90};

    int y = 0;
    // Iterate over all X and Y positions between 0 and 200 and move the leg to that position
    //for (int y = 0; y < 200; y += 10)
    //{
        for (int x = 140; x <= 180; x += 40)
        {
            if (!inverseKinematics2D(x, y, hipAngleL, kneeAngleL, ankleAngleL)) 
            {
                Serial.println("No solution");
                continue;
            }

            calculateOtherLeg(hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR);

            Serial.print("X: ");
            Serial.print(x);
            Serial.print(" Y: ");
            Serial.println(y);
            Serial.print(" - L Hip: ");
            Serial.print(hipAngleL);
            Serial.print(" Knee: ");
            Serial.print(kneeAngleL);
            Serial.print(" Ankle: ");
            Serial.println(ankleAngleL);
            Serial.print(" - R Hip: ");
            Serial.print(hipAngleR);
            Serial.print(" Knee: ");
            Serial.print(kneeAngleR);
            Serial.print(" Ankle: ");
            Serial.println(ankleAngleR);

            thisMove[0] = hipAngleR;
            thisMove[1] = kneeAngleR;
            thisMove[2] = ankleAngleR;
            thisMove[3] = hipAngleL;
            thisMove[4] = kneeAngleL;
            thisMove[5] = ankleAngleL;
            moveServos(thisMove);
            //delay(2000);
        }
    //}
    delay(1000);
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


void setSpeed(uint16_t pSpeed)
{
    tSpeed = pSpeed;
    setSpeedForAllServos(tSpeed);
    Serial.print(F("Speed set: "));
    Serial.println(tSpeed);
}

void loop()
{
    test2dInverseK();
}
