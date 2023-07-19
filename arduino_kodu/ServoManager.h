#ifndef ServoManager_h
#define ServoManager_h


#include "Config.h"

#include "InverseKinematics.h"


// Left Leg
ServoEasing ServoLLH; // Hip
ServoEasing ServoLLK; // Knee
ServoEasing ServoLLA; // Ankle
// Right Leg
ServoEasing ServoRLH; // Hip
ServoEasing ServoRLK; // Knee
ServoEasing ServoRLA; // Ankle
// Neck tilt
ServoEasing ServoNT;
// Neck pan
ServoEasing ServoNP;

InverseKinematics ik;

class ServoManager
{
    public:
    void doInit()
    {

        // IMPORTANT: Communication from Pi uses index, these must be attached in the same order as they are referenced in the pi config
        ServoLLH.attach(PIN_SLLH, PosStart[0]);
        ServoLLK.attach(PIN_SLLK, PosStart[1]);
        ServoLLA.attach(PIN_SLLA, PosStart[2]);
        ServoRLH.attach(PIN_SRLH, PosStart[3]);
        ServoRLK.attach(PIN_SRLK, PosStart[4]);
        ServoRLA.attach(PIN_SRLA, PosStart[5]);
        ServoNT.attach(PIN_SNT, PosStart[6]);
        ServoNP.attach(PIN_SNP, PosStart[7]);
        
        // Initialise IK with min and max angles and leg section lengths
        ik.doInit(PosMin[3], PosMax[3], PosMin[4], PosMax[4], PosMin[5], PosMax[5], LEG_LENGTH_THIGH, LEG_LENGTH_SHIN, LEG_LENGTH_FOOT);

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
                moveSingleServo(tIndex, Pos[tIndex], false);
            else 
                moveSingleServo(tIndex, moveRandom(tIndex), false); // If scripted value is -1, generate random position based on range of currently indexed servo
        }
        //setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed); 
    }
    
    // @todo just make this pass an array in to moveServos.
    void moveSingleServo(uint8_t pServoIndex, int pPos, boolean isRelative)
    {
        if (isRelative)
        {
            // Assuming pPos is a percentage, map to PosMin and PosMax and add to current position
            int realChange = map(abs(pPos), 0, 100, PosMin[pServoIndex], PosMax[pServoIndex]);
            if (pPos < 0)
            {
                realChange = -realChange;
            }
            ServoEasing::ServoEasingNextPositionArray[pServoIndex] = ServoEasing::ServoEasingNextPositionArray[pServoIndex] + realChange;
        }
        else
        {
            ServoEasing::ServoEasingNextPositionArray[pServoIndex] = pPos;
        }
        setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
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
        ik.inverseKinematics2D(x, y, hipAngleL, kneeAngleL, ankleAngleL);
        // solve other leg
        ik.calculateOtherLeg(hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR);
        // Assign angles and move servos
        int thisMove[MAX_EASING_SERVOS] = {hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR, NOVAL, NOVAL};
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
        int thisMove[MAX_EASING_SERVOS] = {NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL, NOVAL};

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
