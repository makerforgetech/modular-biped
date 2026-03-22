import os
import time
from PIL import Image, ImageDraw, ImageFont
from modules.display.lib.waveshare import OLED_0in91
from modules.base_module import BaseModule

class WaveshareOLED(BaseModule):
    def __init__(self, **kwargs):
        self.picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
        try:
            self.disp = OLED_0in91.OLED_0in91()
            print("0.91inch OLED Module")
            self.disp.Init()
            self.clear_display()
            self.background = None
            self.set_background('WHITE')
            self.show_image(self.background)
            self.time_on_boot = kwargs.get('time_on_boot', False)
            if kwargs.get('test_on_boot'):
                self.draw_demo()
        except Exception as e:
            print(f"Failed to initialize OLED display: {e}")
            self.disp = None
            
    def setup_messaging(self):
        if self.time_on_boot:
            self.subscribe('system/loop/1', self.draw_time)
        self.subscribe('system/exit', self.exit)
        self.subscribe('display/body/text', self.show_text)

    def clear_display(self):
        if self.disp:
            self.disp.clear()

    def set_background(self, color=None):
        if color is not None and self.disp:
            self.background = Image.new('1', (self.disp.width, self.disp.height), color)

    def show_image(self, image):
        if self.disp and image is not None:
            self.disp.ShowImage(self.disp.getbuffer(image))
            
    def show_text(self, text, font_size=12):
        if not self.disp:
            return
        image = Image.new('1', (self.disp.width, self.disp.height), "WHITE")
        draw = ImageDraw.Draw(image)
        font_path = os.path.join(self.picdir, 'Font.ttc')
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            self.log(f"Font load error: {e}", level='error')
            font = None
        if font:
            w, h = draw.textsize(text, font=font)
            x = (self.disp.width - w) // 2
            y = (self.disp.height - h) // 2
            draw.text((x, y), text, font=font, fill=0)
        self.show_image(image)

    def draw_time(self):
        now = time.strftime("%H:%M:%S")
        self.show_text(now, font_size=26)

    def draw_demo(self):
        if not self.disp:
            return
        # Draw lines and text
        image1 = Image.new('1', (self.disp.width, self.disp.height), "WHITE")
        draw = ImageDraw.Draw(image1)
        font_path = os.path.join(self.picdir, 'Font.ttc')
        try:
            font1 = ImageFont.truetype(font_path, 12)
            font2 = ImageFont.truetype(font_path, 18)
        except Exception as e:
            self.log(f"Font load error: {e}", level='error')
            font1 = font2 = None
        draw.line([(0,0),(127,0)], fill=0)
        draw.line([(0,0),(0,31)], fill=0)
        draw.line([(0,31),(127,31)], fill=0)
        draw.line([(127,0),(127,31)], fill=0)
        if font1:
            draw.text((20,0), 'Waveshare ', font=font1, fill=0)
        if font2:
            draw.text((20,12), u'微雪电子 ', font=font2, fill=0)
        image1 = image1.rotate(0)
        self.show_image(image1)
        time.sleep(3)
        # # Draw bitmap image
        # Himage2 = Image.new('1', (self.disp.width, self.disp.height), 255)
        # bmp_path = os.path.join(self.picdir, '0in91.bmp')
        # try:
        #     bmp = Image.open(bmp_path)
        #     Himage2.paste(bmp, (0,0))
        # except Exception as e:
        #     self.log(f"Bitmap load error: {e}")
        # Himage2 = Himage2.rotate(0)
        # self.show_image(Himage2)
        # time.sleep(3)
        # self.clear_display()

    def exit(self):
        self.show_text("Goodbye!", font_size=14)
        time.sleep(2)
        self.set_background('WHITE')
        self.show_image(self.background)
        if self.disp:
            self.disp.module_exit()
            self.disp = None