#pragma once

class IServoManager {
public:
    virtual void moveSingleServoByPercentage(uint8_t pServoIndex, int pPercent, boolean isRelative) = 0;
    virtual void moveServos(int *Pos) = 0;
};