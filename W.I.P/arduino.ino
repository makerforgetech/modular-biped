void hipAdjust(double pitch)
{
    double threshold = 5.0; // Do not move if less than this
    if (pitch < threshold && pitch > -threshold)
    {
        return;
    }
    
    // Update model's position in Processing using Serial communication
    Serial.print("MODEL ");
    Serial.println(pitch);
    
    ik.hipAdjust(ik.hipAdjustment + pitch);
    moveSingleServo(0, pitch, true);
    moveSingleServo(3, -pitch, true);
}
