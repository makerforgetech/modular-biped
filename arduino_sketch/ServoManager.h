#pragma once

#include "ServoEasing.hpp"
#include "InverseKinematics.h"
#ifdef MPU6050_ENABLED
    #include "Mpu6050.h"
#endif
#include "IServoManager.h"

namespace ModularBiped {
    class ServoManager : public IServoManager
    {
    public:
        double currentX, currentY;
        boolean calibrateRest;

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
        #ifdef MPU6050_ENABLED
            Mpu6050 tilt;
        #endif        

        void doInit()
        {
            initInputs();
            this->calibrateRest = false;

            #ifdef MPU6050_ENABLED
                tilt.doInit();
            #endif

            // IMPORTANT: Communication from Pi uses index, these must be attached in the same order as they are referenced in the pi config
            this->ServoLLH.attach(Config::PIN_SLLH, Config::StartingPos[0]);
            this->ServoLLK.attach(Config::PIN_SLLK, Config::StartingPos[1]);
            this->ServoLLA.attach(Config::PIN_SLLA, Config::StartingPos[2]);
            this->ServoRLH.attach(Config::PIN_SRLH, Config::StartingPos[3]);
            this->ServoRLK.attach(Config::PIN_SRLK, Config::StartingPos[4]);
            this->ServoRLA.attach(Config::PIN_SRLA, Config::StartingPos[5]);
            this->ServoNT.attach(Config::PIN_SNT, Config::StartingPos[6]);
            this->ServoNP.attach(Config::PIN_SNP, Config::StartingPos[7]);

            // Initialise IK with min and max angles and leg section lengths
            ik.doInit(Config::PosMin[3], Config::PosMax[3], Config::PosMin[4], Config::PosMax[4], Config::PosMin[5], Config::PosMax[5], Config::LEG_LENGTH_THIGH, Config::LEG_LENGTH_SHIN, Config::LEG_LENGTH_FOOT);

            // Loop over ServoEasing::ServoEasingArray and attach each servo
            for (uint8_t tIndex = 0; tIndex < Config::SERVO_COUNT; ++tIndex)
            {
                // Set easing type to EASING_TYPE
                ServoEasing::ServoEasingArray[tIndex]->setEasingType(EASING_TYPE);
                ServoEasing::ServoEasingArray[tIndex]->setMinMaxConstraint(Config::PosMin[tIndex], Config::PosMax[tIndex]);
            }

            setSpeed(Config::SERVO_SPEED_MIN);

            #ifdef SERVO_CALIBRATION_ENABLED
            calibrate(); // Must be in servoMode 2
            #endif

            // Wait for servos to reach start position.
            delay(3000);
            cLog("Servos initialised");

            if (Config::servoMode == 2)
            {
                moveServos(Config::PosStand); // Stand once
            }

        }

        void initInputs()
        {
            #ifdef SERVO_MODE_PIN_ENABLED
                pinMode(Config::servoModePin, INPUT); // sets the digital pin as input
                int servoModeVal = analogRead(Config::servoModePin);
                for (int i = 0; i < 5; i++)
                {
                    if (servoModeVal < Config::servoModeThresholds[i])
                    {
                        Config::servoMode = i;
                        break;
                    }
                }
                // Serial.print("Servo mode: ");
                // Serial.println(servoMode);
                #ifdef SERVO_MODE_OVERRIDE
                Config::servoMode = SERVO_MODE_OVERRIDE; // Define and set in Config.h if appropriate
                // Serial.print("Servo mode override: ");
                // Serial.println(servoMode);
                #endif
                
                Config::StartingPos = Config::servoModePoses[Config::servoMode];
            #endif

            #ifdef RESTRAIN_PIN_ENABLED
                pinMode(Config::restrainPin, INPUT_PULLUP); // sets the digital pin as input
                if (digitalRead(Config::restrainPin) == LOW) // Check once on startup
                {
                    Config::restrainingBolt = true;
                    Config::StartingPos = Config::PosStart; // Override starting position @todo remove once selector is installed
                }
            #endif
        }

        void servoLoop()
        {
            #ifdef MPU6050_ENABLED
            hipAdjust();
            #endif
            handlePendingMovement();
        }

        void handlePendingMovement()
        {
            setEaseToForAllServosSynchronizeAndStartInterrupt(getSpeed());
            while (ServoEasing::areInterruptsActive())
            {
                blinkLED();
            }
        }

        

        void moveServos(int *Pos)
        {
            for (uint8_t tIndex = 0; tIndex < Config::SERVO_COUNT; ++tIndex)
            {
                if (Pos[tIndex] == Config::NOVAL)
                {
                    // Serial.println("NOVAL FOUND");
                    continue;
                }
                if (Pos[tIndex] != -1)
                    moveSingleServo(tIndex, Pos[tIndex], false);
                else
                    moveSingleServo(tIndex, moveRandom(tIndex), false); // If scripted value is -1, generate random position based on range of currently indexed servo
            }
            // setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
        }

        void moveSingleServoByPercentage(uint8_t pServoIndex, int pPercent, boolean isRelative) {
            // Serial.print("PosMin: ");
            // Serial.print(PosMin[pServoIndex]);
            // Serial.print(" PosMax: ");
            // Serial.print(PosMax[pServoIndex]);
            // Serial.print(" Relative pos change in %: ");
            // Serial.print(pPercent);
            int realChange = map(abs(pPercent), 0, 100, Config::PosMin[pServoIndex], Config::PosMax[pServoIndex]);
            // Serial.print(" in degrees: ");
            // Serial.print(realChange);
            if (isRelative) {
                realChange = realChange - Config::PosMin[pServoIndex]; // Account for min value ONLY if relative
            }
            if (pPercent < 0)
            {
                realChange = -realChange;
            }
            // SerialConnection::write_i16(realChange);
            moveSingleServo(pServoIndex, realChange, isRelative);
        }

        void moveSingleServo(uint8_t pServoIndex, int pPos, boolean isRelative)
        {
            if (((Config::servoMode != 2 || Config::restrainingBolt == true) && pServoIndex < 6) || Config::servoMode == 0)
            {
                // Serial.println("Restrained mode, skipping some / all servos");
            }
            else if (isRelative)
            {
                ServoEasing::ServoEasingNextPositionArray[pServoIndex] = ServoEasing::ServoEasingNextPositionArray[pServoIndex] + pPos;
            }
            else
            {
                ServoEasing::ServoEasingNextPositionArray[pServoIndex] = pPos;
            }
            // Return actual value to Pi
            SerialConnection::write_i16(ServoEasing::ServoEasingNextPositionArray[pServoIndex]);
        }

        void moveLegsAndStore(int x, int y, int *store)
        {
            moveLegs(x, y);
            for (uint8_t tIndex = 0; tIndex < Config::SERVO_COUNT; ++tIndex)
            {
                store[tIndex] = ServoEasing::ServoEasingNextPositionArray[tIndex];
            }
        }

        // function moveLegs that returns an int array
        void moveLegs(int x, int y)
        {
            float hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR;
            currentX = x;
            currentY = y;
            // solve left leg
            ik.inverseKinematics2D(x, y, hipAngleL, kneeAngleL, ankleAngleL);
            // solve other leg
            ik.calculateOtherLeg(hipAngleL, kneeAngleL, ankleAngleL, hipAngleR, kneeAngleR, ankleAngleR);
            // Assign angles and move servos (cast float to int)
            int thisMove[Config::SERVO_COUNT] = {(int)hipAngleL, (int)kneeAngleL, (int)ankleAngleL, (int)hipAngleR, (int)kneeAngleR, (int)ankleAngleR, Config::NOVAL, Config::NOVAL};
            moveServos(thisMove);
        }

        void demoAll()
        {
            setSpeed(Config::SERVO_SPEED_MIN);
            // Cycle through all poses and move all servos to them
            for (uint8_t tPoseIndex = 0; tPoseIndex < sizeof(Config::Poses) / sizeof(Config::Poses[0]); ++tPoseIndex)
            {
                moveServos(Config::Poses[tPoseIndex]);
                delay(1000);
                moveServos(Config::PosRest);
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

        /**
        * Manual servo calibration
        * 
        * Move servos to 90 degree position (mid range).
        * 
        * Iterate over each servo and allow the position to be entered manually.
        * Store in an array. If user enters '', move to the next servo.
        * 
        * Following calibration of all servos, output the arrays to the serial monitor 
        * and loop through the process again.
        * 
        * Output instructions in the serial monitor to guide the user through the process.
        */
        void calibrate() {
            Serial.println("Calibration Mode Activated.");
            Serial.println("WARNING: All min/max constraints removed, be careful!");
            // Array for storing positions
            int positions[Config::SERVO_COUNT] = {Config::PosConfig[0], Config::PosConfig[1], Config::PosConfig[2], Config::PosConfig[3], Config::PosConfig[4], Config::PosConfig[5], Config::PosConfig[6], Config::PosConfig[7]};
            moveServos(positions);
            while(true) {
                for (int i = 0; i < Config::SERVO_COUNT; i++)
                {
                    ServoEasing::ServoEasingArray[i]->setMinMaxConstraint(0, 180); // Remove min/max constraints 

                    Serial.print("Calibrating servo ");
                    Serial.println(i);
                    Serial.print("Starting position: ");
                    Serial.println(positions[i]);
                    Serial.println("Enter position (0-180) or 'n' to move to next servo");
                    while (Serial.available() == 0)
                    {
                        delay(100); // Wait for input
                    }
                    String input = Serial.readString();
                    // If input is a digit, move to that position
                    while (isDigit(input.charAt(0)))
                    {
                        int pos = input.toInt();
                        Serial.print("Moving to ");
                        Serial.println(pos);
                        // Store position in array
                        positions[i] = pos;
                        moveSingleServo(i, pos, false);
                        #ifdef SERVO_CALIBRATION_SYMMETRICAL
                        // Calculate and move equivelent servo in other leg
                        int otherPos = i+3;
                        if (otherPos > 5) otherPos = i-3;
                        moveSingleServo(otherPos, 180-pos, false);
                        #endif
                        setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
                        while (ServoEasing::areInterruptsActive())
                        {
                            blinkLED();
                        }
                        while (Serial.available() == 0)
                        {
                            delay(100);
                        }
                        input = Serial.readString();

                    }
                    Serial.println("Moving to next servo");
                }
                Serial.println("New positions:");
                // output all servo positions
                for (int i = 0; i < Config::SERVO_COUNT; i++)
                {
                    Serial.print(positions[i]);
                    Serial.print(", ");
                }
                Serial.println();
            }
        }

        /**
    * @brief Set all servos to 90 degrees for mechanical calibration. Wait for 20 seconds.
    */
    void allTo90()
    {
    cLog("All at 90");
    moveServos(Config::PosConfig);
    handlePendingMovement();
    delay(20000);
    }

    /**
    * @brief Move to rest position. Either using stored values or by calculating using inverse kinematics and storing result for next time.
    */
    void doRest()
    {
    cLog("Resting");

    // Reset to slow speed
    setSpeed(Config::SERVO_SPEED_MIN);
    if (calibrateRest == false)
    {
        moveServos(Config::PosRest);
    }
    else
    {
        // Mid value between LEG_IK_MIN and LEG_IK_MAX
        float mid = Config::LEG_IK_MIN + ((Config::LEG_IK_MAX - Config::LEG_IK_MIN) / 2);
        moveLegsAndStore(mid, 0, Config::PosRest); // Move legs and store as rest position
    // iterate over PosRest and output values:
    #ifdef DEBUG
        for (int i = 0; i < 9; i++)
        {
        Serial.print(Config::PosRest[i]);
        Serial.print(", ");
        }
        Serial.println();
    #endif
        calibrateRest = false;
    }
    // setEaseToForAllServosSynchronizeAndStartInterrupt(getSpeed());
    }

    void stationarySteps() {
    int left[Config::SERVO_COUNT] = {Config::PosMin[0], Config::PosMin[1], Config::PosMin[2], Config::PosMax[3], Config::PosMax[4], Config::PosMax[5]};
    int right[Config::SERVO_COUNT] = {Config::PosMax[0], Config::PosMax[1], Config::PosMax[2], Config::PosMin[3], Config::PosMin[4], Config::PosMin[5]};
    uint16_t speed = Config::SERVO_SPEED_MIN; // 20 - 60 recommended
    unsigned long delayTime = 200;
    setSpeed(speed);
    boolean moveLeft = true;
    while (true)
    {
        if (moveLeft)
        moveServos(left);
        else
        moveServos(right);

        handlePendingMovement();

        delay(delayTime);
    }
    }

    #ifdef MPU6050_ENABLED
    void hipAdjust()
    {
        tilt.read();
        double pitch = tilt.getPitch();
        double startingOffset = 3.5;
        double threshold = 5.0; // Do not move if less than this
        #ifdef MPU6050_DEBUG
        Serial.print("Pitch:");
        Serial.print(pitch);
        Serial.print(" TH:");
        Serial.print(threshold+startingOffset);
        Serial.print(" TL:");
        Serial.println(-threshold+startingOffset);
        #endif
        if (pitch < threshold+startingOffset && pitch > -threshold+startingOffset)
        {
            return;
        }

        if (abs(pitch) > threshold) { 
            pitch = pitch*0.5;
        }
        ik.hipAdjust(ik.hipAdjustment - pitch);
        moveSingleServo(0, pitch, true);
        moveSingleServo(3, -pitch, true);
    }
    #endif

    private:
        uint16_t tSpeed;

        long moveRandom(int index)
        {
            int middle = (Config::PosMin[index] + Config::PosMax[index]) / 2;
            int range = 15; // Reduce range of motion to avoid extreme movement
            return random(middle - range, middle + range);
        }
    };
};