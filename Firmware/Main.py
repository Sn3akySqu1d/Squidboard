import board
import busio
import time
import adafruit_ssd1306
import digitalio
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation

print("Starting code")

i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

encoder_pin_a = digitalio.DigitalInOut(board.GP20)
encoder_pin_a.direction = digitalio.Direction.INPUT
encoder_pin_a.pull = digitalio.Pull.UP

encoder_pin_b = digitalio.DigitalInOut(board.GP21)
encoder_pin_b.direction = digitalio.Direction.INPUT
encoder_pin_b.pull = digitalio.Pull.UP

encoder_button = digitalio.DigitalInOut(board.GP22)
encoder_button.direction = digitalio.Direction.INPUT
encoder_button.pull = digitalio.Pull.UP

keyboard = KMKKeyboard()
keyboard.col_pins = (board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7,
                     board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13,
                     board.GP14, board.GP15)
keyboard.row_pins = (board.GP16, board.GP17, board.GP19, board.GP18, board.GP27)
keyboard.diode_orientation = DiodeOrientation.COL2ROW
keyboard.keymap = [[
    KC.GRAVE, KC.N1, KC.N2, KC.N3, KC.N4, KC.N5, KC.N6, KC.N7,
    KC.N8, KC.N9, KC.N0, KC.MINUS, KC.EQUAL, KC.BACKSPACE,

    KC.TAB, KC.Q, KC.W, KC.E, KC.R, KC.T, KC.Y, KC.U,
    KC.I, KC.O, KC.P, KC.LBRACKET, KC.RBRACKET, KC.BSLASH,

    KC.CAPS_LOCK, KC.A, KC.NO, KC.S, KC.D, KC.F, KC.G, KC.H,
    KC.J, KC.K, KC.L, KC.SEMICOLON, KC.QUOTE, KC.ENTER,

    KC.LSHIFT, KC.NO, KC.NO, KC.Z, KC.X, KC.C, KC.V, KC.B,
    KC.N, KC.M, KC.COMMA, KC.DOT, KC.SLASH, KC.RSHIFT,

    KC.LCONTROL, KC.NO, KC.NO, KC.LGUI, KC.LALT, KC.NO, KC.NO, KC.SPACE,
    KC.NO, KC.NO, KC.RALT, KC.RGUI, KC.APPLICATION, KC.RCONTROL,
]]


class OledMenu:
    def __init__(self, kb):
        self.keyboard = kb
        self.menu_items = ["Animation", "Timer", "Session Time", "Pomodoro Mode"]
        self.selected_index = 0
        self.current_screen = "menu"

        self.timer_setting = 60
        self.timer_running = False
        self.timer_start_time = None
        self.timer_state = "set"
        self.timer_options = ["Start Timer", "Back"]
        self.timer_option_index = 0

        self.session_start = time.monotonic()

        self.pomodoro_state = "idle"
        self.pomodoro_start = None
        self.pomodoro_count = 0
        self.animation_frames = [
        ["  o   o   o  ", " /|\\ /|\\ /|\\ ", " / \\ / \\ / \\ "],
        [" \\o/ o   o/ ", "  |  /|\\ |\\  ", " / \\ / \\ / \\ "],
        ["  o/ \\o/ \\o ", " /|   |   |\\ ", " / \\ / \\ / \\ "],
        [" \\o   o   o/", "  |\\ /|\\ /|  ", " / \\ / \\ / \\ "],
        ]



        self.animation_frame = 0
        self._last_anim_time = time.monotonic()

        self.last_a = encoder_pin_a.value
        self.last_b = encoder_pin_b.value
        self.button_last = encoder_button.value
        self.encoder_delta = 0
        self.button_pressed = False

    def during_bootup(self, sandbox): pass
    def before_hid_send(self, sandbox): pass
    def after_hid_send(self, sandbox): pass
    def before_matrix_scan(self, sandbox): pass
    def deinit(self, sandbox): pass

    def after_matrix_scan(self, sandbox):
        now = time.monotonic()

        a = encoder_pin_a.value
        b = encoder_pin_b.value
        if a != self.last_a:
            if b != a:
                self.encoder_delta += 1
        self.last_a = a
        self.last_b = b

        button = encoder_button.value
        if not button and self.button_last:
            self.button_pressed = True
        self.button_last = button

        if self.current_screen == "menu":
            if self.encoder_delta > 0:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.encoder_delta = 0
            if self.button_pressed:
                self.button_pressed = False
                selected = self.menu_items[self.selected_index]
                self.current_screen = selected.lower().replace(" ", "_")
                if self.current_screen == "timer":
                    self.timer_state = "set"
                elif self.current_screen == "pomodoro_mode":
                    self.pomodoro_state = "work"
                    self.pomodoro_start = now

        elif self.current_screen == "timer":
            if self.timer_state == "set":
                if self.encoder_delta > 0:
                    self.timer_setting += 10
                    self.encoder_delta = 0
                if self.button_pressed:
                    self.button_pressed = False
                    self.timer_state = "start_or_back"
            elif self.timer_state == "start_or_back":
                if self.encoder_delta > 0:
                    self.timer_option_index = (self.timer_option_index + 1) % len(self.timer_options)
                    self.encoder_delta = 0
                if self.button_pressed:
                    self.button_pressed = False
                    if self.timer_option_index == 0:
                        self.timer_running = True
                        self.timer_start_time = now
                        self.timer_state = "running"
                    else:
                        self.current_screen = "menu"
            elif self.timer_state == "running":
                if self.button_pressed:
                    self.button_pressed = False
                    self.timer_running = False
                    self.timer_state = "set"
                    self.current_screen = "menu"

        elif self.current_screen == "pomodoro_mode":
            if self.button_pressed:
                self.button_pressed = False
                self.pomodoro_state = "idle"
                self.current_screen = "menu"
            else:
                elapsed = int(now - self.pomodoro_start)
                if self.pomodoro_state == "work" and elapsed >= 25 * 60:
                    self.pomodoro_state = "break"
                    self.pomodoro_start = now
                elif self.pomodoro_state == "break" and elapsed >= 5 * 60:
                    self.pomodoro_state = "work"
                    self.pomodoro_start = now
                    self.pomodoro_count += 1

        elif self.current_screen in ["animation", "session_time"]:
            if self.button_pressed:
                self.button_pressed = False
                self.current_screen = "menu"

        oled.fill(0)

        if self.current_screen == "menu":
            oled.text("Main Menu:", 0, 0, 1)
            for i, item in enumerate(self.menu_items):
                prefix = ">" if i == self.selected_index else " "
                oled.text(f"{prefix} {item}", 0, 12 + i * 12, 1)

        elif self.current_screen == "animation":
            frame = self.animation_frames[self.animation_frame]
            for i, line in enumerate(frame):
                oled.text(line, 0, i * 12, 1)
            if now - self._last_anim_time > 0.4:
                self.animation_frame = (self.animation_frame + 1) % len(self.animation_frames)
                self._last_anim_time = now
            oled.text("Press to return", 0, 56, 1)

        elif self.current_screen == "timer":
            if self.timer_state == "set":
                oled.text("Set Timer (sec):", 0, 0, 1)
                oled.text(f"{self.timer_setting}", 0, 24, 1)
                oled.text("Press to confirm", 0, 56, 1)
            elif self.timer_state == "start_or_back":
                oled.text("Timer Options:", 0, 0, 1)
                for i, item in enumerate(self.timer_options):
                    prefix = ">" if i == self.timer_option_index else " "
                    oled.text(f"{prefix} {item}", 0, 12 + i * 12, 1)
            elif self.timer_state == "running":
                elapsed = int(now - self.timer_start_time)
                remaining = self.timer_setting - elapsed
                if remaining <= 0:
                    oled.text("Time's up!", 0, 24, 1)
                    self.timer_running = False
                    self.timer_state = "set"
                    self.current_screen = "menu"
                else:
                    oled.text("Timer Running:", 0, 0, 1)
                    oled.text(f"{remaining} sec", 0, 24, 1)
                    oled.text("Press to cancel", 0, 56, 1)

        elif self.current_screen == "session_time":
            elapsed = int(now - self.session_start)
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            oled.text("Session Time:", 0, 0, 1)
            oled.text(f"{h:02}:{m:02}:{s:02}", 0, 24, 1)
            oled.text("Press to return", 0, 56, 1)

        elif self.current_screen == "pomodoro_mode":
            oled.text("Pomodoro Mode:", 0, 0, 1)
            state = "Work" if self.pomodoro_state == "work" else "Break"
            oled.text(f"{state} time", 0, 16, 1)
            elapsed = int(now - self.pomodoro_start)
            total = 25 * 60 if self.pomodoro_state == "work" else 5 * 60
            remaining = total - elapsed
            if remaining < 0:
                remaining = 0
            m, s = divmod(remaining, 60)
            oled.text(f"{m:02}:{s:02}", 0, 32, 1)
            oled.text(f"Pomodoros: {self.pomodoro_count}", 0, 48, 1)
            oled.text("Press to return", 0, 56, 1)

        oled.show()
        self.encoder_delta = 0


oled_menu = OledMenu(keyboard)
keyboard.extensions.append(oled_menu)

print("Starting keyboard loop")
keyboard.go()