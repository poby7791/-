import tkinter as tk
import time
import serial
import threading
import serial.tools.list_ports

# CONFIGURATION
player_name = ['key1', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7']
MAX_PLAYERS = 7
SEGMENT_THICKNESS = 30
SEGMENT_LENGTH_H = 120
SEGMENT_LENGTH_V = 180
SEGMENT_COLOR_COUNTDOWN = 'red'
SEGMENT_COLOR_TIMER = 'lime'
SEGMENT_COLOR_OFF = 'black'
BACKGROUND_COLOR = 'black'
DIGIT_SPACING = 30
MARGIN = 40
DIGIT_COUNT = 4  # M:SS.T

class SevenSegmentDigit:
    def __init__(self, canvas, x_offset, y_offset):
        self.canvas = canvas
        self.x = x_offset
        self.y = y_offset
        self.segments = {}
        self.create_segments()

    def create_segments(self):
        t = SEGMENT_THICKNESS
        lh = SEGMENT_LENGTH_H
        lv = SEGMENT_LENGTH_V
        x = self.x
        y = self.y
        gap = t // 3

        self.segments['A'] = self.draw_horiz_segment(x + t, y, lh)
        self.segments['B'] = self.draw_vert_segment(x + t + lh, y + gap + 10, lv)
        self.segments['C'] = self.draw_vert_segment(x + t + lh, y + lv + gap * 2 + 10, lv)
        self.segments['D'] = self.draw_horiz_segment(x + t, y + lv * 2 + gap * 3, lh)
        self.segments['E'] = self.draw_vert_segment(x, y + lv + gap * 2 + 10, lv)
        self.segments['F'] = self.draw_vert_segment(x, y + gap + 10, lv)
        self.segments['G'] = self.draw_horiz_segment(x + t, y + lv + gap, lh)

    def draw_horiz_segment(self, x, y, length):
        t = SEGMENT_THICKNESS
        return self.canvas.create_polygon([
            x, y + t // 2,
            x + t // 2, y,
            x + length - t // 2, y,
            x + length, y + t // 2,
            x + length - t // 2, y + t,
            x + t // 2, y + t
        ], fill=SEGMENT_COLOR_OFF, outline='')

    def draw_vert_segment(self, x, y, length):
        t = SEGMENT_THICKNESS
        return self.canvas.create_polygon([
            x + t // 2, y,
            x + t, y + t // 2,
            x + t, y + length - t // 2,
            x + t // 2, y + length,
            x, y + length - t // 2,
            x, y + t // 2
        ], fill=SEGMENT_COLOR_OFF, outline='')

    def display(self, value, color):
        segment_map = {
            0: 'ABCDEF',
            1: 'BC',
            2: 'ABGED',
            3: 'ABCDG',
            4: 'FGBC',
            5: 'AFGCD',
            6: 'AFEDCG',
            7: 'ABC',
            8: 'ABCDEFG',
            9: 'ABCDFG'
        }
        active = segment_map.get(value, '')
        for seg, item in self.segments.items():
            self.canvas.itemconfig(item, fill=color if seg in active else SEGMENT_COLOR_OFF)

    def clear(self):
        for item in self.segments.values():
            self.canvas.itemconfig(item, fill=SEGMENT_COLOR_OFF)

class TimeAuctionGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Time Auction Game")
        self.players_needed = None
        self.colon_id = None
        self.dot_id = None

        self.serial_port = None
        self.serial_thread = None
        self.connect_to_arduino()

        self.show_intro_screen()

    def find_arduino_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
                return port.device
        return None

    def connect_to_arduino(self):
        try:
            port_name = self.find_arduino_port()
            if port_name:
                self.serial_port = serial.Serial(port_name, 9600, timeout=1)
                self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
                self.serial_thread.start()
                print(f"✅ Arduino connected on {port_name}")
            else:
                print("⚠️ Arduino not detected.")
        except serial.SerialException:
            print("❌ Arduino connection failed.")

    def read_serial_data(self):
        while True:
            if self.serial_port and self.serial_port.in_waiting > 0:
                data = self.serial_port.readline().decode().strip()
                if data in '1234567':
                    fake_event = type('Event', (object,), {'char': data})()
                    self.root.after(0, lambda e=fake_event: self.on_key_press(e))
                elif data.startswith('R') and data[1:] in '1234567':
                    fake_event = type('Event', (object,), {'char': data[1]})()
                    self.root.after(0, lambda e=fake_event: self.on_key_release(e))

    def bind_events(self):
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

    def show_intro_screen(self):
        self.intro_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        self.intro_frame.pack(pady=100)

        tk.Label(self.intro_frame, text="Select number of players", fg='white', bg=BACKGROUND_COLOR,
                 font=('Arial', 16)).pack(pady=10)

        for i in range(2, MAX_PLAYERS + 1):
            btn = tk.Button(self.intro_frame, text=str(i), width=4, height=2, font=('Arial', 14),
                            command=lambda n=i: self.start_with_players(n))
            btn.pack(side='left', padx=10)

    def start_with_players(self, num):
        self.players_needed = num
        self.intro_frame.destroy()
        self.init_ui()

    def init_ui(self):
        self.players = set()
        self.released = {}
        self.key_map = {}
        self.running = False
        self.timer_started = False
        self.countdown_seconds = 5
        self.timer_value = 0.0
        self.timer_job = None

        if hasattr(self, 'canvas'):
            self.canvas.destroy()
            self.status.destroy()

        segment_unit = SEGMENT_LENGTH_H + SEGMENT_THICKNESS * 2 + DIGIT_SPACING
        canvas_width = MARGIN * 2 + DIGIT_COUNT * segment_unit + 40
        canvas_height = MARGIN * 2 + SEGMENT_THICKNESS * 3 + SEGMENT_LENGTH_V * 2 + 100

        self.canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height, bg=BACKGROUND_COLOR)
        self.canvas.pack()

        self.digits = []
        for i in range(DIGIT_COUNT):
            extra_spacing = 5 if i == 1 else 0
            dx = MARGIN + i * segment_unit + extra_spacing
            digit = SevenSegmentDigit(self.canvas, dx, MARGIN)
            self.digits.append(digit)

        colon_x = MARGIN + 1 * segment_unit - segment_unit // 3 + 15
        colon_y = MARGIN + SEGMENT_LENGTH_V
        self.colon_id = self.canvas.create_text(colon_x+40, colon_y+195, text=".", fill='lime', font=('Consolas', 130))

        dot_x = MARGIN + 3 * segment_unit - segment_unit // 3
        dot_y = MARGIN + SEGMENT_LENGTH_V * 2
        self.dot_id = self.canvas.create_text(dot_x+55, dot_y+15, text=".", fill='lime', font=('Consolas', 130))

        self.canvas.itemconfig(self.colon_id, state='hidden')
        self.canvas.itemconfig(self.dot_id, state='hidden')

        self.status = tk.Label(self.root, text="Players joined: 0 / " + str(self.players_needed))
        self.status.pack(pady=10)

        self.bind_events()
        self.root.after(100, self.poll_players)

    def display_time_mmss(self, seconds, color):
        total = min(int(seconds * 10), 5999)
        minutes = total // 600
        secs = (total % 600) // 10
        tenths = total % 10
        digits = [minutes % 10, secs // 10, secs % 10, tenths]
        for i, val in enumerate(digits):
            self.digits[i].display(val, color)

    def clear_display(self):
        for digit in self.digits:
            digit.clear()

    def poll_players(self):
        self.status.config(text=f"Players joined: {len(self.players)} / {self.players_needed}")
        if not self.running and len(self.players) == self.players_needed:
            self.running = True
            self.countdown_value = self.countdown_seconds
            self.canvas.itemconfig(self.colon_id, state='hidden')
            self.canvas.itemconfig(self.dot_id, state='hidden')
            self.countdown_tick()
        else:
            self.root.after(100, self.poll_players)

    def countdown_tick(self):
        self.clear_display()
        if self.countdown_value > 0:
            self.digits[1].display(self.countdown_value, SEGMENT_COLOR_COUNTDOWN)
            self.countdown_value -= 1
            self.root.after(1000, self.countdown_tick)
        else:
            self.clear_display()
            self.start_timer()

    def start_timer(self):
        self.timer_started = True
        self.canvas.itemconfig(self.colon_id, state='normal')
        self.canvas.itemconfig(self.dot_id, state='normal')
        self.timer_start_time = time.perf_counter()
        self.update_timer()

    def update_timer(self):
        if len(self.released) == self.players_needed:
            self.end_game()
            return
        self.timer_value = time.perf_counter() - self.timer_start_time
        self.display_time_mmss(self.timer_value, SEGMENT_COLOR_TIMER)
        self.timer_job = self.root.after(100, self.update_timer)

    def end_game(self):
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
        self.display_time_mmss(self.timer_value, SEGMENT_COLOR_TIMER)
        self.show_results()

    def show_results(self):
        result_win = tk.Toplevel(self.root)
        result_win.title("Results")
        tk.Label(result_win, text="Results", font=("Arial", 14)).pack(pady=10)
        for i, key in enumerate(sorted(self.key_map.keys()), 1):
            time_val = self.released.get(key)
            text = f"{player_name[int(key)-1]}: "
            if time_val is not None:
                total = int(time_val * 10)
                minutes = total // 600
                seconds = (total % 600) // 10
                tenths = total % 10
                text += f"{minutes}m {seconds:02d}.{tenths}s"
            else:
                text += "Opt Out"
            tk.Label(result_win, text=text, font=("Arial", 12)).pack(anchor='w', padx=20)

        tk.Button(result_win, text="Restart (Same Players)", font=("Arial", 12),
                  command=lambda: self.restart_game(result_win, keep_players=True)).pack(pady=5)
        tk.Button(result_win, text="Restart (New Players)", font=("Arial", 12),
                  command=lambda: self.restart_game(result_win, keep_players=False)).pack(pady=5)
        tk.Button(result_win, text="Restart (-1 Player)", font=("Arial", 12),
                  state=tk.DISABLED if self.players_needed <= 2 else tk.NORMAL,
                  command=lambda: self.restart_game(result_win, keep_players='minus1')).pack(pady=5)

    def restart_game(self, result_window, keep_players=True):
        result_window.destroy()
        if keep_players == 'minus1':
            self.players_needed -= 1
            self.init_ui()
        elif not keep_players:
            for widget in self.root.winfo_children():
                widget.destroy()
            self.players_needed = None
            self.show_intro_screen()
        else:
            self.init_ui()

    def on_key_press(self, event):
        k = event.char
        if not k.isdigit() or k == '0':
            return
        if k not in self.key_map and len(self.key_map) < self.players_needed:
            self.key_map[k] = len(self.key_map) + 1
        if k in self.key_map:
            self.players.add(k)

    def on_key_release(self, event):
        k = event.char
        if k in self.key_map and k not in self.released:
            if self.timer_started:
                elapsed = time.perf_counter() - self.timer_start_time
                self.released[k] = elapsed
            else:
                self.released[k] = None
                self.players.discard(k)

# Run the game
if __name__ == "__main__":
    root = tk.Tk()
    app = TimeAuctionGame(root)
    root.mainloop()
