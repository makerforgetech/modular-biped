#ifndef PARAMETERS_H
#define PARAMETERS_H

#define SERIAL_BAUD 115200  // Baudrate

#define LED_PIN 13

#define SERVO_NECK_L 3
#define SERVO_NECK_L_INIT 0

#define SERVO_NECK_H 4
#define SERVO_NECK_H_INIT 100

#define SERVO_HEAD 5
#define SERVO_HEAD_INIT 90

#define MOTOR_PIN 3
#define DIRECTION_PIN 4
#define SERVOMOTOR_PIN 6
#define INITIAL_THETA 110  // Initial angle of the servomotor
// Min and max values for motors
#define THETA_MIN 60
#define THETA_MAX 150
#define SPEED_MAX 100

// If DEBUG is set to true, the arduino will send back all the received messages
#define DEBUG false

#endif
