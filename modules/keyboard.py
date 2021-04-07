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
            print('sit')
        elif key == ord('2'):
            pub.sendMessage("animate", action="stand")
            print('stand')
        elif key == ord('3'):
            pub.sendMessage("animate", action="wake")
            print('neck up')
        elif key == ord('4'):
            pub.sendMessage("animate", action="sleep")
            print('neck down')
        elif key == ord('5'):
            pub.sendMessage("animate", action="head_shake")
        elif key == ord('6'):
            pub.sendMessage("animate", action="head_nod")

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
