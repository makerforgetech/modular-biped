import sys


# disable the real sleep command for faster unit tests
def sleep(val):
    return val

module = type(sys)('time')
module.sleep = sleep
sys.modules['time'] = module