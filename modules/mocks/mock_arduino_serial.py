import sys
from unittest.mock import Mock

# class Pub:
#     def sendMessage(val):
#         return val

module = type(sys)('pubsub')
module.pub = Mock()
sys.modules['pubsub'] = module