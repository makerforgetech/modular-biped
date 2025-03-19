#pragma once
#include "IServoManager.h"

namespace ModularBiped {
    // Define the orders that can be sent and received
    enum Order {
        HELLO = 0,
        SERVO = 1,
        SERVO_RELATIVE = 2,
        ALREADY_CONNECTED = 3,
        ERROR = 4,
        RECEIVED = 5,
        STOP = 6,
        LED = 7,
        PIN = 8,
        READ = 9
    };
    typedef enum Order Order;

    class SerialConnection
    {
        bool serialConnected;
        // boot time in millis
        unsigned long bootTime;
        // wait start time in millis
        unsigned long sleepTime;
        bool ordersReceived;
        IServoManager* servoManager; // Pointer to IServoManager


        public:
            SerialConnection(IServoManager* servoManager)
                : servoManager(servoManager), serialConnected(false), bootTime(millis()), sleepTime(0), ordersReceived(false) {}

            boolean getOrdersReceived()
            {
              return this->ordersReceived;
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

            void getAllOrdersFromSerial()
            {
                // Check for orders from serial
                bool receiving = true;
                while(receiving) 
                {
                    receiving = getOrdersFromSerial();
                    if (receiving) {
                        delay(50); // Wait a short time for any other orders
                    }
                }
            }

            boolean getOrdersFromSerial()
            {
                if (Serial.available() == 0)
                {
                    //SerialConnection::write_order(ERROR);
                    return false;
                }

                cLog("Order received: ", false);

                // The first byte received is the instruction
                Order order_received = SerialConnection::read_order();
                cLog((String)order_received);
                if (order_received == HELLO)
                {
                    // If the cards haven't say hello, check the connection
                    if (!this->isConnected())
                    {
                    this->setConnected(true);
                    SerialConnection::write_order(HELLO);
                    }
                    else
                    {
                    // If we are already connected do not send "hello" to avoid infinite loop
                    SerialConnection::write_order(ALREADY_CONNECTED);
                    }
                }
                else if (order_received == ALREADY_CONNECTED)
                {
                    this->setConnected(true);
                }
                else
                {
                    switch (order_received)
                    {
                    case SERVO:
                    case SERVO_RELATIVE:
                    {
                        int servo_identifier = SerialConnection::read_i8();
                        int servo_angle_percent = SerialConnection::read_i16();
                #ifdef DEBUG
                        SerialConnection::write_order(SERVO);
                        SerialConnection::write_i8(servo_identifier);
                        SerialConnection::write_i16(servo_angle_percent);
                #endif
                        // Use the injected servoManager instance
                        servoManager->moveSingleServoByPercentage(servo_identifier, servo_angle_percent, order_received == SERVO_RELATIVE);
                        this->ordersReceived = true;
                        return true;
                    }
                    case PIN:
                    {
                        int pin = SerialConnection::read_i8();
                        int value = SerialConnection::read_i8();
                        pinMode(pin, OUTPUT);
                        digitalWrite(pin, value);
                        break;
                    }
                    case READ:
                    {
                        int pin = SerialConnection::read_i8();
                        pinMode(pin, INPUT);
                        long value = analogRead(pin);
                        SerialConnection::write_i16(value);
                        break;
                    }
                    // Unknown order
                    default:
                    {
                        SerialConnection::write_order(order_received);
                        // SerialConnection::write_i16(404);
                    }
                    }
                }
                return false;
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
                while ((Serial.available() < num_bytes) && (millis() - startTime < timeout)){
                    delay(1);
                }
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
};