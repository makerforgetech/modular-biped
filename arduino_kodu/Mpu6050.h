#ifndef MPU6050_H
#define MPU6050_H

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
boolean mpuReady = false;

uint8_t address;
double pitch,roll;

class Mpu6050
{
    public:
    
    void doInit(uint8_t addr = 0x68)
    {
        address = addr;
        // Try to initialize
        if (!mpu.begin(address)) {
            cLog("Failed to find MPU6050 chip");
            return;
        }

        mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
        mpu.setGyroRange(MPU6050_RANGE_250_DEG);
        mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
        mpuReady = true;
        
        cLog("MPU6050 initialised");
    }

    double getPitch()
    {
        return pitch;
    }

    double getRoll()
    {
        return roll;
    }

    void read()
    {
        if (mpuReady) {
            sensors_event_t a, g, temp;
            mpu.getEvent(&a, &g, &temp);

            pitch = atan2(a.acceleration.x, sqrt(a.acceleration.y * a.acceleration.y + a.acceleration.z * a.acceleration.z)) * 180 / PI;
            roll = atan2(a.acceleration.y, sqrt(a.acceleration.x * a.acceleration.x + a.acceleration.z * a.acceleration.z)) * 180 / PI;
        }
    }

    void debug()
    {
        if (mpuReady) {
            Serial.print("0x");
            Serial.print(address, HEX);
            Serial.print("Pitch:");
            Serial.print(pitch);
            Serial.print(",");
            Serial.print("0x");
            Serial.print(address, HEX);
            Serial.print("Roll:");
            Serial.println(roll);
        }
        delay(10);
    }   
};


#endif
