import sys
from unittest.mock import Mock

# class Pub:
#     def sendMessage(val):
#         return val

module = type(sys)('modules.arduinoserial')
module.ArduinoSerial = Mock()
sys.modules['modules.arduinoserial'] = module