#pragma once
#include "IServoManager.h"

namespace ModularBiped {
    class Animation {
        bool isResting;
        unsigned long bootTime; // boot time in millis
        unsigned long sleepTime; // wait start time in millis
        IServoManager* servoManager; // Pointer to IServoManager

        public:
            Animation(IServoManager* servoManager)
            {
                this->sleepTime = 0;
                this->bootTime = millis();      
                this->isResting = false;
                this->servoManager = servoManager;
            }

            void animateRandomly(bool enabled)
            {
                if (enabled == false)
                    return;

                // if not sleeping, animate randomly
                // Orders from serial will set sleep time so that the animation does not take precedence
                if (!this->isSleeping())
                {
                    if (this->isResting)
                    {
                        cLog("Animating Randomly");
                        servoManager->moveServos(Config::PosLookRandom);
                    }
                    else
                    {
                        this->isResting = true;
                        setSleep(random(1000, 5000));
                    }
                }
            }

        private:
            void setSleep(unsigned long length)
            {
                sleepTime = millis() - bootTime + length;
            }

            bool isSleeping()
            {
                return millis() - bootTime < sleepTime;
            }
    };
}