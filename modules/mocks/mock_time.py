import sys
from unittest.mock import Mock

module = type(sys)('time')
module.sleep = Mock()
module.localtime = Mock()
# sys.modules['time'] = module