#ifndef INVERSE_KINEMATICS_H
#define INVERSE_KINEMATICS_H

//#define IK_DEBUG


/**
 * @file inverse_kinematics.h
 * @brief Inverse kinematics library for biped robots
 * @details This library provides inverse kinematics for a biped robot with 3 degrees of freedom.
 */ 
class InverseKinematics
{
    // constructor
    public:
        double hipAdjustment = HIP_ADJUSTMENT; // Angle to adjust hip, will be modified for balance
        void doInit(float hipMinAngle, float hipMaxAngle, float kneeMinAngle, float kneeMaxAngle, float ankleMinAngle, float ankleMaxAngle, float thighLength, float shinLength, float footLength)
        {
            this->hipMinAngle = hipMinAngle;
            this->hipMaxAngle = hipMaxAngle;
            this->kneeMinAngle = kneeMinAngle;
            this->kneeMaxAngle = kneeMaxAngle;
            this->ankleMinAngle = ankleMinAngle;
            this->ankleMaxAngle = ankleMaxAngle;
            this->thighLength = thighLength;
            this->shinLength = shinLength;
            this->footLength = footLength; // Not currently used
        }

        void hipAdjust(float angle)
        {
            this->hipAdjustment = angle;
        }

        /**
         * @brief Calculate the inverse kinematics for a bipedal leg on a 2d plane
         * @param x The x coordinate of the point
         * @param y The y coordinate of the point (not in use)
         * @param hipAngle The angle of the hip servo (pointer)
         * @param kneeAngle The angle of the knee servo (pointer)
         * @param ankleAngle The angle of the ankle servo (pointer)
         * 
        */
        boolean inverseKinematics2D(float x, float y, float &hipAngle, float &kneeAngle, float &ankleAngle)
        {
            float a = this->thighLength;
            float b = this->shinLength;
            float c = x;
            // Law of cosines to sides A+ B
            //γ = acos((a² + b² − c²)/(2ab))
            float hip = acos((sq(a) + sq(c) - sq(b)) / (2*a*c));
            // Calculate knee from hip
            float knee = PI - (hip * 2) ;
            // Calculate remaining angle (ankle)
            float ankle = d2r(180) - knee - hip;

            // if IK_DEBUG is defined, print debug info
            #ifdef IK_DEBUG
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
            Serial.print(r2d(ankle));
            Serial.print(" = ");
            Serial.println(r2d(hip + knee + ankle));
            #endif

            // return false if angles are not numbers
            if (isnan(hip) || isnan(knee) || isnan(ankle))
            {
                return false;
            }

            // Convert the angles from radians to degrees
            // Adjust to compensate for servo's actual position
            hipAngle = r2d(d2r(180) - (hip + d2r(hipAdjustment))); // Inverse and offset by 90 degrees
            kneeAngle = r2d(knee - d2r(KNEE_ADJUSTMENT)); // Offset 90 to compensate
            ankleAngle = r2d(ankle + d2r(ANKLE_ADJUSTMENT)); // Offset 70 to compensate

            // if IK_DEBUG is defined, print debug info
            #ifdef IK_DEBUG
            Serial.print(hipAngle);
            Serial.print(" - ");
            Serial.print(kneeAngle);
            Serial.print(" - ");
            Serial.println(ankleAngle);
            #endif

            return anglesWithinLimits(hipAngle, kneeAngle, ankleAngle);

        }

        /**
         * @brief Check if the angles are within the limits of the servos
         * @param hipAngle The angle of the hip servo
         * @param kneeAngle The angle of the knee servo
         * @param ankleAngle The angle of the ankle servo
         * @return True if the angles are within the limits, false otherwise
        */
        boolean anglesWithinLimits(float hipAngle, float kneeAngle, float ankleAngle)
        {
            if (hipAngle < this->hipMinAngle || hipAngle > this->hipMaxAngle || 
                kneeAngle < this->kneeMinAngle || kneeAngle > this->kneeMaxAngle ||
                ankleAngle < this->ankleMinAngle || ankleAngle > this->ankleMaxAngle)
            {
                return false;
            }
            return true;
        }

        /** 
         * @brief Calculate the angles for the other leg assuming it is identical but mirrored
         * @param lHip The angle of the hip servo of the left leg
         * @param lKnee The angle of the knee servo of the left leg
         * @param lAnkle The angle of the ankle servo of the left leg
         * @param rHip The angle of the hip servo of the right leg (pointer)
         * @param rKnee The angle of the knee servo of the right leg (pointer)
         * @param rAnkle The angle of the ankle servo of the right leg (pointer)
        */
        void calculateOtherLeg(float lHip, float lKnee, float lAnkle, float &rHip, float &rKnee, float &rAnkle)
        {
            rHip = 180 - lHip;
            rKnee = 180 - lKnee;
            rAnkle = 180 - lAnkle;
        }


        /**
         * @brief Convert radians to degrees
        */
        float r2d(float rad)
        {
            return (rad * 180 / PI);
        }

        /**
         * @brief Convert degrees to radians
        */
        float d2r(float deg)
        {
            return (deg * PI / 180);
        }

    private:
        float hipMinAngle;
        float hipMaxAngle;
        float kneeMinAngle;
        float kneeMaxAngle;
        float ankleMinAngle;
        float ankleMaxAngle;
        float thighLength;
        float shinLength;
        float footLength;
};


#endif
