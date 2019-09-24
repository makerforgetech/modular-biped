import curses


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

    def __del__(self):
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()

    def input(self):
        char = self.screen.getch()
        return char

    def handle_input(self):
        key = self.input()
        if self.mappings is not None:
            if key in self.mappings:
                method_info = self.mappings.get(key)
                if method_info[1] is not None:
                    method_info[0](method_info[1])
                else:
                    method_info[0]()
        return key
