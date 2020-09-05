from modules.personality import Personality
import datetime

def test_init():
    personality = Personality()
    assert personality.happiness == 50
    assert personality.contentment == 50
    assert personality.attention == 50
    assert personality.wakefulness == 100
    assert not personality.do_output

    assert personality.last_behave.replace(microsecond=0) == datetime.datetime.now().replace(microsecond=0)
    assert personality.last_output.replace(microsecond=0) == datetime.datetime.now().replace(microsecond=0)


def test_cycle():
    personality = Personality()
    personality.cycle()
    assert 30 < personality.attention < 70
    assert 47 < personality.happiness < 53
    assert 46 < personality.wakefulness
    assert 46 < personality.contentment

