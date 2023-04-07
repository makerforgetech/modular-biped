#ifndef ServoManager_h
#define ServoManager_h


#include "Config.h"

#include "InverseKinematics.h"


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

InverseKinematics ik(PosMin[3], PosMax[3], PosMin[4], PosMax[4], PosMin[5], PosMax[5], 94.0, 94.0, 28.0);


class ServoManager
{
    public:
    void doInit()
    {
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
        Serial.println("Servos initialised");
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
        //setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed); 
    }
    void moveSingleServo(uint8_t pServoIndex, int pPos)
    {
        ServoEasing::ServoEasingNextPositionArray[pServoIndex] = pPos;
        //setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    }

    void demoAll()
    {
        //Serial.println(F("Demo all poses at minimum speed"));
        setSpeed(SERVO_SPEED_MIN);
        // Cycle through all poses and move all servos to them
        for (uint8_t tPoseIndex = 0; tPoseIndex < sizeof(Poses) / sizeof(Poses[0]); ++tPoseIndex)
        {
            //Serial.print(F("Pose: "));
            //Serial.println(tPoseIndex);
            moveServos(Poses[tPoseIndex]);
            delay(1000);
            //Serial.println(F("Rest"));
            moveServos(PosRest);
            delay(2000);
        }
    }

    void setSpeed(uint16_t pSpeed)
    {
        tSpeed = pSpeed;
        setSpeedForAllServos(tSpeed);
        //Serial.print(F("Speed set: "));
        //Serial.println(tSpeed);
    }

    uint16_t getSpeed()
    {
      return tSpeed;
    }

    private:
    uint16_t tSpeed;
    

    long moveRandom(int index)
    {
        return random(PosMin[index], PosMax[index]);
    }

    void solve2dInverseK(int x)
    {
        float hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR;
        int thisMove[MAX_EASING_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90, 90};

        // Solve inverse kinematics for left leg
        if (!ik.inverseKinematics2D(x, 0, hipAngleL, kneeAngleL, ankleAngleL)) 
        {
            Serial.println("No solution");
            return;
        }

        // Solve right leg, assuming identical but mirrored
        ik.calculateOtherLeg(hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR);

        #ifdef IK_DEBUG
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
        #endif

        // Define new positions and move servos
        thisMove[0] = hipAngleR;
        thisMove[1] = kneeAngleR;
        thisMove[2] = ankleAngleR;
        thisMove[3] = hipAngleL;
        thisMove[4] = kneeAngleL;
        thisMove[5] = ankleAngleL;
        moveServos(thisMove);
        delay(1000);
    }
};
#endif
