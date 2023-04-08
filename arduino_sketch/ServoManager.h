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

InverseKinematics ik;


class ServoManager
{
    public:
    void doInit()
    {
        Servo1.attach(SERVO1_PIN, PosRest[0]);
        Servo2.attach(SERVO2_PIN, PosRest[1]);
        Servo3.attach(SERVO3_PIN, PosRest[2]);
        Servo4.attach(SERVO4_PIN, PosRest[3]);
        Servo5.attach(SERVO5_PIN, PosRest[4]);
        Servo6.attach(SERVO6_PIN, PosRest[5]);
        Servo7.attach(SERVO7_PIN, PosRest[6]);
        Servo8.attach(SERVO8_PIN, PosRest[7]);
        Servo9.attach(SERVO9_PIN, PosRest[8]);

        ik.doInit(PosMin[3], PosMax[3], PosMin[4], PosMax[4], PosMin[5], PosMax[5], 94.0, 94.0, 28.0);

        // Loop over ServoEasing::ServoEasingArray and attach each servo
        for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex)
        {
            // Set easing type to EASING_TYPE
            ServoEasing::ServoEasingArray[tIndex]->setEasingType(EASING_TYPE);
            ServoEasing::ServoEasingArray[tIndex]->setMinMaxConstraint(PosMin[tIndex], PosMax[tIndex]);
        }
        // Wait for servos to reach start position.
        delay(3000); 
        cLog("Servos initialised");
    }

    void moveServos(int *Pos)
    {
        for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex)
        {
            if (Pos[tIndex] == NOVAL) {
              //Serial.println("NOVAL FOUND");
              continue;
            }
            if (Pos[tIndex] != -1)
                moveSingleServo(tIndex, Pos[tIndex]);
            else 
                moveSingleServo(tIndex, moveRandom(tIndex)); // If scripted value is -1, generate random position based on range of currently indexed servo
        }
        //setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed); 
    }
    
    // @todo just make this pass an array in to moveServos.
    void moveSingleServo(uint8_t pServoIndex, int pPos)
    {
        ServoEasing::ServoEasingNextPositionArray[pServoIndex] = pPos;
        //setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    }

    void moveLegsAndStore(int x, int y, int *store)
    {
        moveLegs(x, y);
        for (uint8_t tIndex = 0; tIndex < MAX_EASING_SERVOS; ++tIndex)
        {
            store[tIndex] = ServoEasing::ServoEasingNextPositionArray[tIndex];
        }
    }

    // function moveLegs that returns an int array
    void moveLegs(int x, int y)
    {
        float hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR;
        // solve left leg
        ik.inverseKinematics2D(x, y, hipAngleR, kneeAngleR, ankleAngleR);
        // solve other leg
        ik.calculateOtherLeg(hipAngleR, kneeAngleR, ankleAngleR, hipAngleL, kneeAngleL, ankleAngleL);
        // Assign angles and move servos
        int thisMove[MAX_EASING_SERVOS] = {hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR, NOVAL, NOVAL, NOVAL};
        moveServos(thisMove);
    }

    void demoAll()
    {
        setSpeed(SERVO_SPEED_MIN);
        // Cycle through all poses and move all servos to them
        for (uint8_t tPoseIndex = 0; tPoseIndex < sizeof(Poses) / sizeof(Poses[0]); ++tPoseIndex)
        {
            moveServos(Poses[tPoseIndex]);
            delay(1000);
            moveServos(PosRest);
            delay(2000);
        }
    }

    void setSpeed(uint16_t pSpeed)
    {
        tSpeed = pSpeed;
        setSpeedForAllServos(tSpeed);
//        cLog(F("Speed set: "));
//        cLog((String) tSpeed);
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
            #ifdef IK_DEBUG
            Serial.println("No solution");
            #endif
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
