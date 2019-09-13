import sys


class MockVideoCapture():
    def release(self):
        return 'release'
    def isOpened(self):
        return True
    def read(self):
        return ('read', 'read2')


class MockCascade():
    def detectMultiScale(self, gray, **kwargs):
        return [(1, 2, 3, 4)]


class MockFrame():
    def copy(self):
        return []

class MockCV2:
    COLOR_BGR2GRAY = 'GRAY'
    THRESH_BINARY = 'BINARY'
    RETR_EXTERNAL = 'RETR_EXTERNAL'
    CHAIN_APPROX_SIMPLE = 'CHAIN_APPROX_SIMPLE'


    def VideoCapture(mode):
        return MockVideoCapture()

    def destroyAllWindows():
        return 'destroyAllWindows'

    def cvtColor(frame, COLOR_BGR2GRAY):
        return 'cvtColor'

    def GaussianBlur(gray, something, soemthingelse):
        return 'GaussianBlur'

    def CascadeClassifier(path):
        return MockCascade()

    def absdiff(one, two):
        return one

    def threshold(one, two, three, four):
        return [one, MockFrame()]

    def dilate(one, two, **kwargs):
        return one

    def findContours(one, two, three):
        return (one, two, three)

    def contourArea(contourArea):
        return 1000

# module = type(sys)('cv2')
# module.VideoCapture = MockCV2.VideoCapture
# module.destroyAllWindows = MockCV2.destroyAllWindows
# module.cvtColor = MockCV2.cvtColor

sys.modules['cv2'] = MockCV2