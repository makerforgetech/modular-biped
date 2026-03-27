from .bus_servo_base import BusServoBase

class BusServoFactory:
    @staticmethod
    def create(backend, model, servo_id, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        if backend == 'waveshare':
            from .waveshare_backend import WaveshareBusServo
            return WaveshareBusServo(servo_id, model, port, baudrate, range, range_degrees, **kwargs)
        elif backend == 'rustypot':
            from .rustypot_backend import RustypotBusServo
            return RustypotBusServo(servo_id, model, port, baudrate, range, range_degrees, **kwargs)
        elif backend == 'simulation':
            from .simulation_backend import SimulationBusServo
            return SimulationBusServo(servo_id, model, port, baudrate, range, range_degrees, **kwargs)
        else:
            raise ValueError(f"Unknown backend: {backend}")
