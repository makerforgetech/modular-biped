from unittest import TestCase
from modules.animate import Animate


class AnimateTest(TestCase):
    def test_init(self):
        path = '../../animations'
        animate = Animate(path=path)
        assert animate.path == path + '/'
