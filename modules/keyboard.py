import curses
from pubsub import pub

class Keyboard:
    KEY_UP = 259
    KEY_DOWN = 258
    KEY_LEFT = 260
    KEY_RIGHT = 261
    KEY_SPACE = 32
    KEY_RETURN = 10
    KEY_BACKSPACE = 263

    def __init__(self, **kwargs):
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)
        self.mappings = kwargs.get('mappings', None)
        pub.subscribe(self.loop, 'loop')
        self.animations = {'a': 'sleep', 's': 'wake', 'd': 'look_up', 'f': 'look_down', 'g': 'head_shake', 'h': 'head_nod', 'j': 'neck_forward', 'k': 'head_right', 'l': 'head_left',
                           'z': 'sit', 'x': 'stand', 'c': 'raised', 'v': 'tiptoes', 'p': 'speak'}

    def __del__(self):
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()

    def loop(self):
        # Manual keyboard input for puppeteering
        key = self.handle_input()
        if key == ord('q'):
            pub.sendMessage("exit")
        elif key == ord('1'):
            pub.sendMessage("animate", action="sit")
            pub.sendMessage("animate", action="sleep")
            print('sit and sleep')
        elif key == ord('1'):
            pub.sendMessage("animate", action="wake")
            pub.sendMessage("animate", action="stand")
            print('stand and wake')
        elif chr(key) in self.animations:
            print(key)
            print(chr(key))
            an = self.animations[chr(key)]
            print(an)
            pub.sendMessage("animate", action=an)
        else:
            print(key)

    def input(self):
        char = self.screen.getch()
        return char

    def handle_input(self):
        key = self.input()
        if self.mappings is not None:
            if key in self.mappings:
                method_info = self.mappings.get(key)
                print('method')
                print(method_info[0])
                print('param')
                print(method_info[1])
                print('end')
                if method_info[1] is not None:
                    method_info[0](method_info[1])
                else:
                    method_info[0]()
        return key
