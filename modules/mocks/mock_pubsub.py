import sys
from unittest.mock import Mock

# class Pub:
#     def sendMessage(val):
#         return val

module = type(sys)('pubsub')
module.pub = Mock()
module.pub.sendMessage.return_value = Mock()
module.pub.subscribe.return_value = Mock()
sys.modules['pubsub'] = module