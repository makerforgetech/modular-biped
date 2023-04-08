#ifndef PI_CONNECT_H
#define PI_CONNECT_H

#include "Order.h"

class PiConnect
{
    bool serialConnected;
    // boot time in millis
    unsigned long bootTime;
    // wait start time in millis
    unsigned long sleepTime;


    public:
        PiConnect()
        {
            this->serialConnected = false;
            this->bootTime = millis();
            this->sleepTime = 0;
        }
        boolean isConnected()
        {
            return this->serialConnected;
        }
        void setConnected(boolean connected)
        {
            cLog(F("Serial connected: "), false);
            cLog((String) connected);
            this->serialConnected = connected;
        }
        static boolean checkForConnection()
        {
            cLog(F("Checking for connection"));
            write_order(HELLO);
            wait_for_bytes(1, 1000);
        }

        static Order read_order()
        {
            cLog("Reading order");
            return (Order) Serial.read();
        }

        static void wait_for_bytes(int num_bytes, unsigned long timeout)
        {
            unsigned long startTime = millis();
            //Wait for incoming bytes or exit if timeout
            while ((Serial.available() < num_bytes) && (millis() - startTime < timeout)){}
        }

        // NOTE : Serial.readBytes is SLOW
        // this one is much faster, but has no timeout
        static void read_signed_bytes(int8_t* buffer, size_t n)
        {
            size_t i = 0;
            int c;
            while (i < n)
            {
                c = Serial.read();
                if (c < 0) break;
                *buffer++ = (int8_t) c; // buffer[i] = (int8_t)c;
                i++;
            }
        }

        static int8_t read_i8()
        {
            wait_for_bytes(1, 100); // Wait for 1 byte with a timeout of 100 ms
            return (int8_t) Serial.read();
        }

        static int16_t read_i16()
        {
            int8_t buffer[2];
            wait_for_bytes(2, 100); // Wait for 2 bytes with a timeout of 100 ms
            read_signed_bytes(buffer, 2);
            return (((int16_t) buffer[0]) & 0xff) | (((int16_t) buffer[1]) << 8 & 0xff00);
        }

        static int32_t read_i32()
        {
            int8_t buffer[4];
            wait_for_bytes(4, 200); // Wait for 4 bytes with a timeout of 200 ms
            read_signed_bytes(buffer, 4);
            return (((int32_t) buffer[0]) & 0xff) | (((int32_t) buffer[1]) << 8 & 0xff00) | (((int32_t) buffer[2]) << 16 & 0xff0000) | (((int32_t) buffer[3]) << 24 & 0xff000000);
        }

        static void write_order(enum Order myOrder)
        {
            uint8_t* Order = (uint8_t*) &myOrder;
            Serial.write(Order, sizeof(uint8_t));
        }

        static void write_i8(int8_t num)
        {
            Serial.write(num);
        }

        static void write_i16(int16_t num)
        {
            int8_t buffer[2] = {(int8_t) (num & 0xff), (int8_t) (num >> 8)};
            Serial.write((uint8_t*)&buffer, 2*sizeof(int8_t));
        }

        static void write_i32(int32_t num)
        {
            int8_t buffer[4] = {(int8_t) (num & 0xff), (int8_t) (num >> 8 & 0xff), (int8_t) (num >> 16 & 0xff), (int8_t) (num >> 24 & 0xff)};
            Serial.write((uint8_t*)&buffer, 4*sizeof(int8_t));
        }

};
#endif
