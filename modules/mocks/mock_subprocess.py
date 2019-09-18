import sys


# disable the real sleep command for faster unit tests
def call(val, **kwargs):
    return True

module = type(sys)('subprocess')
module.call = call
sys.modules['subprocess'] = module