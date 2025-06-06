import serial
import serial.tools.list_ports
import time
import tkinter as tk
import threading

BUTTON_COUNT = 7

def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    return None

class ButtonMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Button Monitor")
        self.button_states = {str(i): False for i in range(1, BUTTON_COUNT + 1)}
        self.labels = {}

        self.create_ui()
        threading.Thread(target=self.serial_thread, daemon=True).start()

    def create_ui(self):
        font_header = ('Arial', 18, 'bold')
        font_cell = ('Arial', 18)

        for i in range(BUTTON_COUNT):
            tk.Label(
                self.root,
                text=f"DP {i+1}",
                font=font_header,
                borderwidth=3,
                relief="ridge",
                width=10,
                height=3,
                padx=5,
                pady=10
            ).grid(row=0, column=i, padx=4, pady=4)

        for i in range(BUTTON_COUNT):
            lbl = tk.Label(
                self.root,
                font=font_cell,
                borderwidth=3,
                relief="groove",
                width=10,
                height=3,
                bg='lightgray',
                padx=5,
                pady=10
            )
            lbl.grid(row=1, column=i, padx=4, pady=4)
            self.labels[str(i+1)] = lbl

    def update_button_state(self, btn, pressed):
        lbl = self.labels[btn]
        if pressed:
            lbl.config(bg='lime')
        else:
            lbl.config(bg='lightgray')

    def serial_thread(self):
        try:
            print("⏳ 아두이노 포트 자동 검색 중...")
            port_name = find_arduino_port()
            if not port_name:
                print("❌ 아두이노 포트를 찾을 수 없습니다.")
                return

            ser = serial.Serial(port_name, 9600, timeout=1)
            time.sleep(2)
            print(f"✅ 아두이노 연결 완료 ({port_name})")

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        continue

                    if line.startswith('R') and line[1:] in self.button_states:
                        btn = line[1:]
                        if self.button_states[btn]:
                            self.button_states[btn] = False
                            self.root.after(0, self.update_button_state, btn, False)

                    elif line in self.button_states:
                        btn = line
                        if not self.button_states[btn]:
                            self.button_states[btn] = True
                            self.root.after(0, self.update_button_state, btn, True)

        except serial.SerialException as e:
            print(f"❌ 시리얼 통신 오류: {e}")
        except Exception as e:
            print(f"❌ 예기치 못한 오류: {e}")

# 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonMonitorApp(root)
    root.mainloop()
