from time import sleep
from modules.personality import Personality


p = Personality()

while True:
    p.cycle()
    print(p.behave())
    # p.output()
    sleep(2)
