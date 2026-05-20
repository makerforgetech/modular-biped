from PIL import Image, ImageDraw
from modules.display.tft_display import TFTDisplay
import time
import threading

class TFTDisplayEye(TFTDisplay):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure colors are stored as tuples
        self.colors = {
            key: tuple(map(int, value.strip('()').split(',')))
            for key, value in kwargs.get('colors', {}).items()
        }
        self.center = (self.disp.width // 2, self.disp.height // 2) # Default center of the display
        self.radius = 50
        self.pos = self.center
        self._target_center = self.center
        self._eye_thread = threading.Thread(target=self._eye_loop, daemon=True)
        self._eye_thread.start()
        self._move_eye_timer = None
        if kwargs.get('test_on_boot'):
            threading.Thread(target=self.init_eye, daemon=True).start()
    
    def _eye_loop(self):
        # Proportional movement: move a fraction of the remaining distance each frame
        delay = 0.0005  # Faster update for smoother, more responsive movement
        min_dist = 1  # Minimum distance to snap to target
        while True:
            cx, cy = self.center
            tx, ty = self._target_center
            dx = tx - cx
            dy = ty - cy
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist > min_dist:
                # Move 50% of the way toward the target each frame
                new_cx = int(round(cx + dx * 0.5))
                new_cy = int(round(cy + dy * 0.5))
                self.center = (new_cx, new_cy)
                self.img = self.draw_halo(
                    ring_radius=self.radius,
                    ring_thickness=10,
                    color=self.colors['blue']
                )
            else:
                self.center = self._target_center
            time.sleep(delay)

    def setup_messaging(self):
        # call parent setup_messaging
        super().setup_messaging()
        self.subscribe('eye', self.eye)
        self.subscribe('eye/look', self.set_look_target)
        self.subscribe('eye/blink', self.blink_threaded)
        self.subscribe('eye/move', self.move_eye_threaded)
        

    def set_look_target(self, coordinates=None):
        if coordinates is None:
            coordinates = (self.disp.width // 2, self.disp.height // 2)
        self._target_center = coordinates

    def move_eye(self, axis, delta):
        self.log(f"Moving eye axis={axis} delta={delta}")
        delta_x = delta if axis == 'x' else self._target_center[0]
        delta_y = delta if axis == 'y' else self._target_center[1]
        new_x = round(max(0, min(self.disp.width, delta_x)))
        new_y = round(max(0, min(self.disp.height, delta_y)))
        self._target_center = (new_x, new_y)
        self.log(f"New target center: {self._target_center}")
        # # Cancel previous timer if running
        # if self._move_eye_timer and self._move_eye_timer.is_alive():
        #     self._move_eye_timer.cancel()
        # # Start/reset timer to return to center after 1 second
        # def return_to_center():
        #     self._target_center = (self.disp.width // 2, self.disp.height // 2)
        # self._move_eye_timer = threading.Timer(1.0, return_to_center)
        # self._move_eye_timer.start()

    def move_eye_threaded(self, axis, delta):
        self.move_eye(axis, delta)

    def blink_threaded(self):
        threading.Thread(target=self.blink, daemon=True).start()

    def init_eye(self):
        self.draw_image('makerforge_bl.png')
        time.sleep(2)
        img = None
        # Increase radius from 0 to 70 in steps of 5
        for x in range(0, self.radius, 5):
            img = self.draw_halo(
                ring_radius=x,
                color=self.colors['blue'],
                glow_spread=10
            )
        # increase glow spread from 10 to 30 in steps of 5
        for x in range(10, 30, 2):
            img = self.draw_halo(
                color=self.colors['blue'],
                glow_spread=x
            )
        self.img = self.eye('blue')
        # time.sleep(3)
        # self.blink()
        print("TFT display test completed")

    def eye(self, color):
        # print(f"Eye color: {color}")
        # If color doesn't exist, throw exception
        if color not in self.colors:
            raise ValueError(f"Color '{color}' not found in available colors.")
        # Access the color as a tuple
        return self.draw_halo(
            ring_radius=self.radius,
            ring_thickness=10,
            color=self.colors[color]
        )
    
    # look() is now handled by the background thread using _target_center

    def draw_halo(self, color, ring_radius=50, ring_thickness=10, glow_layers=12, glow_spread=30):
        disp = self.disp
        center = self.center
        glow_image = Image.new("RGBA", (disp.width, disp.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow_image)

        for i in range(glow_layers):
            spread = int(i * glow_spread / glow_layers)
            alpha = int(255 * (1 - i / glow_layers) ** 2 * 0.5)
            glow_color = (color[0], color[1], color[2], alpha)

            outer_radius = ring_radius + ring_thickness // 2 + spread
            inner_radius = ring_radius - ring_thickness // 2 - spread

            outer_bbox = [
                center[0] - outer_radius,
                center[1] - outer_radius,
                center[0] + outer_radius,
                center[1] + outer_radius
            ]
            draw.ellipse(outer_bbox, outline=glow_color, width=3)

            if inner_radius > 0:
                inner_bbox = [
                    center[0] - inner_radius,
                    center[1] - inner_radius,
                    center[0] + inner_radius,
                    center[1] + inner_radius
                ]
                draw.ellipse(inner_bbox, outline=glow_color, width=3)

        ring_bbox = [
            center[0] - ring_radius - 2,
            center[1] - ring_radius - 2,
            center[0] + ring_radius + 2,
            center[1] + ring_radius + 2
        ]
        draw.ellipse(ring_bbox, outline=(color[0], color[1], color[2], 255), width=ring_thickness)

        final_image = self.background.copy()
        final_image.paste(glow_image, (0, 0), glow_image)
        self.show_image(final_image)
        return final_image
