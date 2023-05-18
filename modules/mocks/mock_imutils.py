import sys
from unittest.mock import Mock

class MockImUtils:
    def video(self):
        return Mock()

module = type(sys)('imutils')
module.video = Mock()
module.video.FPS = Mock()
module.video.FPS.return_value = Mock()
module.video.FPS.start.return_value = Mock()
module.video.FPS.stop.return_value = Mock()
sys.modules['imutils'] = module