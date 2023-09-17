#ifndef ORDER_H
#define ORDER_H

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

#endif
