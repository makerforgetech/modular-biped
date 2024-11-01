import datetime
from time import sleep
tstep = datetime.datetime.now()


while True:
    dif = datetime.datetime.now() - tstep
    print(dif.total_seconds())
    tstep = datetime.datetime.now()
    sleep(1)