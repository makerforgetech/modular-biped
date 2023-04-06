/**
 * @file arduino_sketch2.ino
 * @brief Arduino sketch to control a 9 servo robot
 * @details This sketch animates a 9 servo bipedal robot using the ServoEasing library.
 * See the README.md file for more information.
 */

#include <Arduino.h>

#define MAX_EASING_SERVOS 9
#include "ServoEasing.hpp"
#include "config.h"
#include "order.h"
#include "InverseK.h"

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

#define S1_REST 160 // Left Leg - Hip
#define S2_REST 180 // Left Leg - Knee
#define S3_REST 90  // Left Leg - Ankle
#define S4_REST 20  // Right Leg - Hip
#define S5_REST 0   // Right Leg - Knee
#define S6_REST 90  // Right Leg - Ankle
#define S7_REST 0   // Neck elevation (unused)
#define S8_REST 90  // Neck tilt
#define S9_REST 90  // Neck pan

// Arrays to store servo min / max positions to avoid mechanical issues due
// NOTE: attach() disregards this, set PosSleep to be within range of the servo's physical boundaries
int PosMin[MAX_EASING_SERVOS] = {20, 5, 40, 20, 5, 15, 40, 60, 20};
int PosMax[MAX_EASING_SERVOS] = {160, 175, 180, 160, 175, 180, 90, 120, 160};
int PosSleep[MAX_EASING_SERVOS] = {70, PosMin[1], PosMax[2], 110, PosMax[4], PosMin[5], S7_REST, PosMax[7], S9_REST};
int PrepRestFromSleep[MAX_EASING_SERVOS] = {80, PosMin[1], PosMax[2], 100, PosMax[4], PosMin[5], S7_REST, 80, S9_REST};
int PrepSleepFromRest[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 80, S9_REST};

// Starting positions @todo make this pose the legs just above their unpowered position
int PosRest[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, S9_REST};

// Poses
int PosStand[MAX_EASING_SERVOS] = {110, 110, 110, 70, 70, 70, S7_REST, S8_REST, S9_REST};
int PosLookLeft[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 180};
int PosLookRight[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, S8_REST, 0};
int PosLookRandom[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, -1, -1}; // Made random by calling the function moveRandom() if the value is -1
int PosLookUp[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 60, S9_REST};
int PosLookDown[MAX_EASING_SERVOS] = {S1_REST, S2_REST, S3_REST, S4_REST, S5_REST, S6_REST, S7_REST, 120, S9_REST};

// Array of poses except PosRest and PosSleep (which are used for initialization and reset of position)
int *Poses[] = {PosStand, PosLookLeft, PosLookRight, PosLookUp, PosLookDown, PosLookRandom};

void blinkLED();

uint16_t tSpeed;

bool serialConnected = false;
// boot time in millis
unsigned long bootTime = millis();
// wait start time in millis
unsigned long sleepTime = 0;
bool isResting = false;

void setup()
{
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(11, OUTPUT);   // sets the digital pin as output
    digitalWrite(11, LOW); // sets the digital pin on
    Serial.begin(115200);
    tSpeed = SERVO_SPEED_MIN;

    // Seed random number generator
    randomSeed(analogRead(0));

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
    

    // moveServos(PrepRestFromSleep); // Move hips and head to try and balance
    // moveServos(PosRest);

    // //testInverseK();
    // //demoAll();

    // Serial.println(F("Move to sleep"));
    // moveServos(PrepSleepFromRest);
    // moveServos(PosSleep);
    // delay(5000); // Final delay to allow time to stop if needed
    //Serial.println(F("Move to rest ahead of main loop"));
    doRest();
    //Serial.println(F("Start loop"));
}
void doRest()
{
  isResting = true;
  moveServos(PrepRestFromSleep); // Move hips and head to try and balance
  moveServos(PosRest);
}

long moveRandom(int index)
{
    return random(PosMin[index], PosMax[index]);
}

// Quick conversion from the Braccio angle system to radians
float b2a(float b)
{
    return b / 180.0 * PI - HALF_PI;
}

// Quick conversion from radians to the Braccio angle system
float a2b(float a)
{
    return (a + HALF_PI) * 180 / PI;
}

void testInverseK()
{
    Serial.println("Test Inverse Kinematics");
    // Set all servos to 90 degrees
    int centerAll[MAX_EASING_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90, 90};
    Serial.println("All at 90");
    moveServos(centerAll);
    delay(10000);

    // Create links(length, min angle, max angle)
    Link dummy, hipL, kneeL, ankleL, dummy2, hipR, kneeR, ankleR;
    dummy.init(0, 0, 0); // Needed as the library needs 4 links
    hipL.init(94, b2a(20), b2a(160));
    kneeL.init(94, b2a(15), b2a(90));
    ankleL.init(28, b2a(40), b2a(180));

    dummy2.init(0, 0, 0);
    hipR.init(94, b2a(20), b2a(160));
    kneeR.init(94, b2a(90), b2a(175));
    ankleR.init(28, b2a(40), b2a(180));

    InverseK.attach(dummy, hipL, kneeL, ankleL);

    InverseK2.attach(dummy2, hipR, kneeR, ankleR);

    // Variables to populate when finding solution
    float d, hl, kl, al, d2, hr, kr, ar;

    // Iterate over all values from 100 to 300 in steps of 10
    // Expected outcome: @todo cache these values
    // 130,-,36.36,174.64,162.00
    // 140,-,41.77,165.33,165.90
    // 150,-,47.66,154.88,170.46
    // 160,134.68,20.69,40.63,54.37,142.63,176.00
    // 170,129.46,29.70,40.83,50.54,171.66,40.79
    // 180,123.51,40.22,40.26,55.36,161.84,45.79
    // 190,116.93,51.82,41.24,60.86,150.69,51.45
    // 200,108.02,67.89,41.09,67.51,137.25,58.24
    // 210,97.85,84.12,53.03,76.85,118.44,67.71
    for (int i = 100; i < 300; i += 10)
    {
        int solved = 0;
        Serial.print(i);
        Serial.print(',');
        if (InverseK.solve(0, 0, i, d, hl, kl, al))
        {
            solved ++;
            Serial.print(a2b(hl));
            Serial.print(',');
            Serial.print(a2b(kl));
            Serial.print(',');
            Serial.print(a2b(al));
            Serial.print(',');
        }
        else
        {
            Serial.print("-");
            Serial.print(',');
        }
        if (InverseK2.solve(0, 0, i, d2, hr, kr, ar))
        {
            solved ++;
            Serial.print(a2b(hr));
            Serial.print(',');
            Serial.print(a2b(kr));
            Serial.print(',');
            Serial.println(a2b(ar));
        }
        else
        {
            Serial.println("-");
        }
        // If both legs are solved, move to that position and wait 10 seconds
        if (solved == 2)
        {
            int thisMove[MAX_EASING_SERVOS] = {a2b(hl), a2b(kl), a2b(al), a2b(hr), a2b(kr), a2b(ar), 90, 90, 90};
            moveServos(thisMove);
            delay(2000);
        }
    }
}

void blinkLED()
{
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
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
    setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    while (ServoEasing::areInterruptsActive())
    {
        blinkLED();
    }
}
void moveSingleServo(uint8_t pServoIndex, int pPos)
{
    ServoEasing::ServoEasingNextPositionArray[pServoIndex] = pPos;
    setEaseToForAllServosSynchronizeAndStartInterrupt(tSpeed);
    while (ServoEasing::areInterruptsActive())
    {
        blinkLED();
    }
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

void loop()
{
    // Check for serial connection and connect, or wait for orders if connected
    if (serialConnected == false)
      checkForConnection();
    else 
      checkSerial();

    // if not sleeping, animate randomly
    // Orders from pi will set sleep time so that the animation does not take precedence
    if (!isSleeping()){
      if (isResting)
      {
        animateRandomly();
        setSleep(random(3000, 5000));
      }
      else {
        moveServos(PosRest);
        isResting = true;
        setSleep(random(3000, 20000));
      }
    }  
}

void setSleep(unsigned long length)
{
    sleepTime = millis() - bootTime + length;
}

boolean isSleeping()
{
    return millis() - bootTime < sleepTime;
}

void animateRandomly()
{
    // Set tSpeed to between SERVO_SPEED_MIN and SERVO_SPEED_MAX
    setSpeed(random(SERVO_SPEED_MIN, SERVO_SPEED_MAX));
    // Radomly select a pose and move to it (not stand)
    // uint8_t tPoseIndex = random(1, sizeof(Poses) / sizeof(Poses[0]));

    //Serial.print(F("Pose: "));
    //Serial.println(tPoseIndex);
    //moveServos(Poses[tPoseIndex]);
    moveServos(PosLookRandom);

    // Wait between 1 and 5 seconds
    setSleep(random(1000, 5000));

    // Reset to slow speed
    setSpeed(SERVO_SPEED_MIN);

}

void checkSerial()
{
  if(Serial.available() > 0)
  {
    // The first byte received is the instruction
    Order order_received = read_order();

    if(order_received == HELLO)
    {
      // If the cards haven't say hello, check the connection
      if(!serialConnected)
      {
        serialConnected = true;
        write_order(HELLO);
      }
      else
      {
        // If we are already connected do not send "hello" to avoid infinite loop
        write_order(ALREADY_CONNECTED);
      }
    }
    else if(order_received == ALREADY_CONNECTED)
    {
      serialConnected = true;
    }
    else
    {
      switch(order_received)
      {
        case SERVO:
        {
          int servo_identifier = read_i8();
          int servo_angle = read_i16();
          if(DEBUG)
          {
            write_order(SERVO);
            write_i16(servo_angle);
          }
          // sleep animations for 2 seconds to allow pi to control servos
          setSleep(2000);
          moveSingleServo(servo_identifier - SERVO_PIN_OFFSET, servo_angle);
          break;
        }
        case PIN:
        {
            int pin = read_i8();
            int value = read_i8();
            pinMode(pin, OUTPUT);
            digitalWrite(pin, value);
            break;
        }
        case READ:
        {
            int pin = read_i8();
            pinMode(pin, INPUT);
            long value = analogRead(pin);
            write_i16(value);
            break;
        }
        // Unknown order
        default:
        {
          write_order(ERROR);
          write_i16(404);
        }
        return;
      }
    }
    //write_order(RECEIVED); // Confirm the receipt
  }
}

void checkForConnection()
{
    write_order(HELLO);
    wait_for_bytes(1, 1000);
}


Order read_order()
{
	return (Order) Serial.read();
}

void wait_for_bytes(int num_bytes, unsigned long timeout)
{
	unsigned long startTime = millis();
	//Wait for incoming bytes or exit if timeout
	while ((Serial.available() < num_bytes) && (millis() - startTime < timeout)){}
}

// NOTE : Serial.readBytes is SLOW
// this one is much faster, but has no timeout
void read_signed_bytes(int8_t* buffer, size_t n)
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

int8_t read_i8()
{
	wait_for_bytes(1, 100); // Wait for 1 byte with a timeout of 100 ms
  return (int8_t) Serial.read();
}

int16_t read_i16()
{
  int8_t buffer[2];
	wait_for_bytes(2, 100); // Wait for 2 bytes with a timeout of 100 ms
	read_signed_bytes(buffer, 2);
  return (((int16_t) buffer[0]) & 0xff) | (((int16_t) buffer[1]) << 8 & 0xff00);
}

int32_t read_i32()
{
  int8_t buffer[4];
	wait_for_bytes(4, 200); // Wait for 4 bytes with a timeout of 200 ms
	read_signed_bytes(buffer, 4);
  return (((int32_t) buffer[0]) & 0xff) | (((int32_t) buffer[1]) << 8 & 0xff00) | (((int32_t) buffer[2]) << 16 & 0xff0000) | (((int32_t) buffer[3]) << 24 & 0xff000000);
}

void write_order(enum Order myOrder)
{
  uint8_t* Order = (uint8_t*) &myOrder;
  Serial.write(Order, sizeof(uint8_t));
}

void write_i8(int8_t num)
{
  Serial.write(num);
}

void write_i16(int16_t num)
{
	int8_t buffer[2] = {(int8_t) (num & 0xff), (int8_t) (num >> 8)};
  Serial.write((uint8_t*)&buffer, 2*sizeof(int8_t));
}

void write_i32(int32_t num)
{
	int8_t buffer[4] = {(int8_t) (num & 0xff), (int8_t) (num >> 8 & 0xff), (int8_t) (num >> 16 & 0xff), (int8_t) (num >> 24 & 0xff)};
  Serial.write((uint8_t*)&buffer, 4*sizeof(int8_t));
}
