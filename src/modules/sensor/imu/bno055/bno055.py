# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_bno055
from pubsub import pub
from modules.base_module import BaseModule

# BNO055 Register addresses
BNO055_OPR_MODE_ADDR = 0x3D
BNO055_EULER_H_LSB_ADDR = 0x1A
BNO055_ACCEL_DATA_X_LSB_ADDR = 0x08

class BNO055(BaseModule):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'bno055')
        self.address = kwargs.get('address', 0x28)
        self.line_offset = kwargs.get('line_offset', 0) # for console output formatting (move up X lines)
        self.test_on_boot = kwargs.get('test_on_boot', False)
        self.data = None
        try:
            i2c = board.I2C()  # uses board.SCL and board.SDA
            self.sensor = adafruit_bno055.BNO055_I2C(i2c, address=self.address)
        except Exception as e:
            raise RuntimeError(f"BNO055: Error initializing sensor: {e}")
        
        self.last_val = 0xFFFF
        if self.test_on_boot:
            while True:
                self.read_data()
                time.sleep(1)

    def get_euler(self):
        return self.sensor.euler
    
    def _get_data(self):
        data = {
            'temperature': self.sensor.temperature,
            'acceleration': self.sensor.acceleration,
            'magnetic': self.sensor.magnetic,
            'gyro': self.sensor.gyro,
            'euler': self.sensor.euler,
            'quaternion': self.sensor.quaternion,
            'linear_acceleration': self.sensor.linear_acceleration,
            'gravity': self.sensor.gravity
        }
        return data
        
    def publish_changed_data(self):
        new_data = self._get_data()
        # print(f"X:{new_data['euler'][1]}") # Print pitch for debugging balance
        ## Example Data: {'temperature': 19, 'acceleration': (0.17, -9.74, -0.99), 'magnetic': (12.1875, 63.75, 32.25), 'gyro': (0.001090830782496456, 0.002181661564992912, -0.002181661564992912), 'euler': (359.9375, 0.9375, 95.75), 'quaternion': (0.67059326171875, -0.74169921875, -0.01263427734375, 0.0), 'linear_acceleration': (0.01, 0.02, 0.03), 'gravity': (0.16, -9.75, -0.98)}
        # Check that data has changed significantly before sending update (to avoid flooding with minor fluctuations)
        # Define per-key thresholds
        thresholds = {
            'temperature': 0.5,
            'acceleration': 0.3,
            'magnetic': 3.0,
            'gyro': 0.1,
            'euler': 1.0,
            'quaternion': 0.1,
            'linear_acceleration': 0.1,
            'gravity': 0.3
        }

        def has_significant_change(new, old, threshold):
            if isinstance(new, (tuple, list)) and isinstance(old, (tuple, list)):
                return any(abs(a - b) > threshold for a, b in zip(new, old))
            try:
                return abs(new - old) > threshold
            except Exception:
                return new != old

        changed_key = None
        changed_new = None
        changed_old = None
        if self.data is None:
            changed_key = 'initial'
        else:
            for key in new_data:
                threshold = thresholds.get(key, 0.5)
                if has_significant_change(new_data[key], self.data[key], threshold):
                    changed_key = key
                    changed_new = new_data[key]
                    changed_old = self.data[key]
                    break

        if self.data is None or changed_key is not None:
            self.data = new_data
            
            if changed_key == 'initial':
                # self.log(f"Publishing new data (initial): {self.data}")
                self.publish(f'imu/{self.name}/data', data=self.data)
                return True
            elif changed_key is not None:
                if 'euler' in new_data:
                    euler = new_data['euler']
                    pitch = euler[1]
                    print(f"S:{pitch}")
                # self.log(f"Publishing new data: {self.data} (change detected in '{changed_key}': {changed_old} -> {changed_new}, threshold={thresholds.get(changed_key, 0.5)})")
                self.publish(f'imu/{self.name}/data', data={changed_key: changed_new})
                return True
        return False

    def read_data(self):
        print(f"Name: {self.name}")
        print(f"Temperature: {self.sensor.temperature} degrees C")
        print(f"Accelerometer (m/s^2): {self.sensor.acceleration}")
        print(f"Magnetometer (microteslas): {self.sensor.magnetic}")
        print(f"Gyroscope (rad/sec): {self.sensor.gyro}")
        print(f"Euler angle: {self.sensor.euler}")
        print(f"Quaternion: {self.sensor.quaternion}")
        print(f"Linear acceleration (m/s^2): {self.sensor.linear_acceleration}")
        print(f"Gravity (m/s^2): {self.sensor.gravity}")
        print()
