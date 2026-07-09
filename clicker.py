import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pyautogui
from pynput.mouse import Listener as MouseListener, Button, Controller
from pynput.keyboard import Listener as KeyListener, Key, KeyCode
import json
import os
import ctypes

# ===== РЕШЕНИЕ ПРОБЛЕМЫ С DPI =====
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

# ===== ГЛОБАЛЬНЫЕ =====
mouse = Controller()
running = False
actions = []
show_trajectory = True
trajectory_window = None
settings = {
    'click_button': 'right',
    'slide_speed': 1,
    'loop_delay': 1,
    'slide_mode': 'there_and_back',
    'start_key': 'enter',
    'stop_key': 'enter',
    'slide_repeat': 1
}
config_file = 'settings.json'
waiting_for_b = False
temp_points = []
root = None
slide_counter = 0

# ===== ЗАГРУЗКА/СОХРАНЕНИЕ =====
def load_settings():
    global settings
    try:
        with open(config_file, 'r') as f:
            settings.update(json.load(f))
    except:
        save_settings()

def save_settings():
    with open(config_file, 'w') as f:
        json.dump(settings, f, indent=4)

# ===== ТРАЕКТОРИЯ =====
def show_trajectory_line(a, b):
    global trajectory_window
    
    if trajectory_window:
        try:
            trajectory_window.destroy()
        except:
            pass
    
    if not show_trajectory:
        return
    
    root_traj = tk.Tk()
    root_traj.overrideredirect(True)
    root_traj.attributes('-topmost', True)
    root_traj.attributes('-transparentcolor', 'white')
    root_traj.geometry(f"{pyautogui.size().width}x{pyautogui.size().height}+0+0")
    root_traj.configure(bg='white')
    
    canvas = tk.Canvas(root_traj, bg='white', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    canvas.create_line(a[0], a[1], b[0], b[1], fill='red', width=4)
    
    canvas.create_oval(a[0]-10, a[1]-10, a[0]+10, a[1]+10, fill='#00ff00', outline='#00cc00', width=2)
    canvas.create_text(a[0], a[1]-25, text='A', fill='#00ff00', font=('Arial', 18, 'bold'))
    
    canvas.create_oval(b[0]-10, b[1]-10, b[0]+10, b[1]+10, fill='#ff4444', outline='#cc0000', width=2)
    canvas.create_text(b[0], b[1]-25, text='B', fill='#ff4444', font=('Arial', 18, 'bold'))
    
    for i in range(1, 20):
        t = i / 20
        x = int(a[0] + (b[0] - a[0]) * t)
        y = int(a[1] + (b[1] - a[1]) * t)
        canvas.create_oval(x-3, y-3, x+3, y+3, fill='yellow', outline='orange')
    
    trajectory_window = root_traj
    root_traj.mainloop()

def hide_trajectory():
    global trajectory_window
    if trajectory_window:
        try:
            trajectory_window.destroy()
            trajectory_window = None
        except:
            pass

def toggle_trajectory():
    global show_trajectory, trajectory_window
    show_trajectory = not show_trajectory
    
    if not show_trajectory:
        hide_trajectory()
    
    status = "ВКЛ" if show_trajectory else "ВЫКЛ"
    return status

# ===== ОСНОВНОЙ ЦИКЛ (БЕЗ ЛИШНИХ global) =====
def main_loop():
    global running, slide_counter  # <-- ВСЕ global в одном месте!
    
    while running:
        for action in actions:
            if not running:
                break
            
            if action['type'] == 'click':
                x, y = action['x'], action['y']
                button = get_button(settings['click_button'])
                mouse.position = (x, y)
                mouse.click(button)
                time.sleep(settings['loop_delay'] / 1000)
            
            elif action['type'] == 'slide':
                slide_counter = 0
                a = (action['x1'], action['y1'])
                b = (action['x2'], action['y2'])
                button = get_button(settings['click_button'])
                repeat_count = settings['slide_repeat']
                
                if show_trajectory:
                    threading.Thread(target=show_trajectory_line, args=(a, b), daemon=True).start()
                    time.sleep(0.01)
                
                for rep in range(repeat_count):
                    if not running:
                        break
                    
                    slide_counter = rep + 1
                    print(f"🔄 Слайд {slide_counter}/{repeat_count}")
                    
                    do_slide_ultra_fast(a, b, button)
                    
                    if not running:
                        break
                    
                    time.sleep(0.01)
                    do_slide_ultra_fast(b, a, button)
                    
                    if rep < repeat_count - 1:
                        time.sleep(settings['loop_delay'] / 1000)
                
                print(f"✅ Слайд выполнен {slide_counter} раз(а) (туда-обратно)")
                
                if slide_counter >= repeat_count:
                    running = False
                    print("⏹ Автоматическая остановка!")
                    try:
                        root.after(0, update_gui_stop)
                    except:
                        pass
                
                time.sleep(settings['loop_delay'] / 1000)

def update_gui_stop():
    """Обновляет GUI при автоматической остановке"""
    global running
    running = False
    try:
        if root:
            for widget in root.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Button) and "РАБОТАЕТ" in child.cget('text'):
                            child.config(text="▶ СТАРТ", bg='#4caf50')
                            break
            for widget in root.winfo_children():
                if isinstance(widget, tk.Label) and "ЗАПУЩЕН" in widget.cget('text'):
                    widget.config(text="🔴 ОСТАНОВЛЕН", fg='#f44336')
                    break
    except:
        pass

def do_slide_ultra_fast(start, end, button):
    global running
    
    mouse.position = start
    mouse.press(button)
    time.sleep(0.005)
    
    steps = 30
    speed = settings['slide_speed'] / 1000
    
    for i in range(1, steps + 1):
        if not running:
            break
        t = i / steps
        x = int(start[0] + (end[0] - start[0]) * t)
        y = int(start[1] + (end[1] - start[1]) * t)
        mouse.position = (x, y)
        time.sleep(speed)
    
    mouse.release(button)

def get_button(name):
    buttons = {
        'left': Button.left,
        'right': Button.right,
        'middle': Button.middle
    }
    return buttons.get(name, Button.right)

# ===== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС =====
class AutoClickerGUI:
    def __init__(self):
        global root
        self.root = tk.Tk()
        self.root.title("🎮 Автокликер v5.4")
        self.root.geometry("580x800")
        self.root.resizable(False, False)
        self.root.configure(bg='#1e1e1e')
        root = self.root
        
        # Горячие клавиши
        self.root.bind('<F1>', lambda e: self.add_click())
        self.root.bind('<F2>', lambda e: self.add_slide())
        self.root.bind('<Control-u>', lambda e: self.toggle_trajectory_gui())
        self.root.bind('<Control-c>', lambda e: self.clear_all())
        
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#007acc',
            'success': '#4caf50',
            'danger': '#f44336',
            'warning': '#ff9800'
        }
        
        self.create_widgets()
        self.update_list()
        load_settings()
        
        # Загрузка настроек
        self.speed_var.set(settings['slide_speed'])
        self.delay_var.set(settings['loop_delay'])
        self.mode_var.set(settings['slide_mode'])
        self.button_var.set(settings['click_button'])
        self.start_key_var.set(settings['start_key'])
        self.stop_key_var.set(settings['stop_key'])
        self.repeat_var.set(settings['slide_repeat'])
        
        # Старт слушателей
        self.start_key_listener()
        self.start_mouse_listener()
    
    def create_widgets(self):
        # Заголовок
        header = tk.Label(self.root, text="🎮 АВТОКЛИКЕР v5.4", 
                          font=('Arial', 20, 'bold'), bg=self.colors['bg'], fg=self.colors['fg'])
        header.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="🔴 ОСТАНОВЛЕН", 
                                     font=('Arial', 14), bg=self.colors['bg'], fg=self.colors['danger'])
        self.status_label.pack(pady=5)
        
        # Инфо
        info = tk.Label(self.root, text="F1 - Клик | F2 - Слайд | Ctrl+U - Траектория", 
                        bg=self.colors['bg'], fg='#888888', font=('Arial', 9))
        info.pack(pady=2)
        
        # Рамка действий
        frame_actions = tk.LabelFrame(self.root, text="📋 Действия", 
                                      font=('Arial', 12, 'bold'), bg=self.colors['bg'], fg=self.colors['fg'])
        frame_actions.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Список
        self.listbox = tk.Listbox(frame_actions, height=8, bg='#2d2d2d', fg='white', 
                                  selectbackground=self.colors['accent'], font=('Arial', 10))
        self.listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Кнопки действий
        frame_buttons = tk.Frame(frame_actions, bg=self.colors['bg'])
        frame_buttons.pack(pady=5)
        
        btn_add_click = tk.Button(frame_buttons, text="➕ Клик (F1)", command=self.add_click,
                                  bg=self.colors['accent'], fg='white', width=13)
        btn_add_click.pack(side=tk.LEFT, padx=5)
        
        btn_add_slide = tk.Button(frame_buttons, text="📍 Слайд (F2)", command=self.add_slide,
                                  bg=self.colors['accent'], fg='white', width=13)
        btn_add_slide.pack(side=tk.LEFT, padx=5)
        
        btn_remove = tk.Button(frame_buttons, text="🗑 Удалить", command=self.remove_last,
                               bg=self.colors['warning'], fg='white', width=13)
        btn_remove.pack(side=tk.LEFT, padx=5)
        
        btn_clear = tk.Button(frame_buttons, text="🧹 Очистить (Ctrl+C)", command=self.clear_all,
                              bg=self.colors['danger'], fg='white', width=13)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        # Настройки
        frame_settings = tk.LabelFrame(self.root, text="⚙️ Настройки", 
                                       font=('Arial', 12, 'bold'), bg=self.colors['bg'], fg=self.colors['fg'])
        frame_settings.pack(padx=20, pady=10, fill=tk.X)
        
        # Скорость
        frame_speed = tk.Frame(frame_settings, bg=self.colors['bg'])
        frame_speed.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_speed, text="⚡ Скорость (MS):", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.speed_var = tk.IntVar(value=1)
        speed_spinbox = tk.Spinbox(frame_speed, from_=1, to=50, textvariable=self.speed_var,
                                   width=10, bg='#2d2d2d', fg='white', command=self.update_speed)
        speed_spinbox.pack(side=tk.RIGHT, padx=10)
        
        # Задержка
        frame_delay = tk.Frame(frame_settings, bg=self.colors['bg'])
        frame_delay.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_delay, text="⏱ Задержка (MS):", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.delay_var = tk.IntVar(value=1)
        delay_spinbox = tk.Spinbox(frame_delay, from_=1, to=100, textvariable=self.delay_var,
                                   width=10, bg='#2d2d2d', fg='white', command=self.update_delay)
        delay_spinbox.pack(side=tk.RIGHT, padx=10)
        
        # Количество повторений
        frame_repeat = tk.Frame(frame_settings, bg=self.colors['bg'])
        frame_repeat.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_repeat, text="🔄 Повторений (1 = туда-обратно):", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.repeat_var = tk.IntVar(value=1)
        repeat_spinbox = tk.Spinbox(frame_repeat, from_=1, to=9999, textvariable=self.repeat_var,
                                    width=10, bg='#2d2d2d', fg='white', command=self.update_repeat)
        repeat_spinbox.pack(side=tk.RIGHT, padx=10)
        
        # Кнопка мыши
        frame_button = tk.Frame(frame_settings, bg=self.colors['bg'])
        frame_button.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_button, text="🖱 Кнопка слайда:", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.button_var = tk.StringVar(value='right')
        button_combo = ttk.Combobox(frame_button, textvariable=self.button_var,
                                    values=['left', 'right', 'middle'], width=10, state='readonly')
        button_combo.pack(side=tk.RIGHT, padx=10)
        button_combo.bind('<<ComboboxSelected>>', self.update_button)
        
        # Режим
        frame_mode = tk.Frame(frame_settings, bg=self.colors['bg'])
        frame_mode.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_mode, text="🔄 Режим:", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.mode_var = tk.StringVar(value='there_and_back')
        mode_combo = ttk.Combobox(frame_mode, textvariable=self.mode_var,
                                  values=['one_way', 'there_and_back'], 
                                  width=15, state='readonly')
        mode_combo.pack(side=tk.RIGHT, padx=10)
        mode_combo.bind('<<ComboboxSelected>>', self.update_mode)
        
        # Управление
        frame_keys = tk.LabelFrame(self.root, text="🎮 Управление", 
                                   font=('Arial', 11, 'bold'), bg=self.colors['bg'], fg=self.colors['fg'])
        frame_keys.pack(padx=20, pady=10, fill=tk.X)
        
        # Старт
        frame_start = tk.Frame(frame_keys, bg=self.colors['bg'])
        frame_start.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_start, text="▶ Клавиша СТАРТ:", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.start_key_var = tk.StringVar(value='enter')
        start_combo = ttk.Combobox(frame_start, textvariable=self.start_key_var,
                                   values=['enter', 'mouse5', 'mouse4', 'f3', 'f4'], 
                                   width=12, state='readonly')
        start_combo.pack(side=tk.RIGHT, padx=10)
        start_combo.bind('<<ComboboxSelected>>', self.update_start_key)
        
        # Стоп
        frame_stop = tk.Frame(frame_keys, bg=self.colors['bg'])
        frame_stop.pack(pady=5, fill=tk.X)
        
        tk.Label(frame_stop, text="⏹ Клавиша СТОП:", 
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=10)
        
        self.stop_key_var = tk.StringVar(value='enter')
        stop_combo = ttk.Combobox(frame_stop, textvariable=self.stop_key_var,
                                  values=['enter', 'mouse5', 'mouse4', 'f3', 'f4'], 
                                  width=12, state='readonly')
        stop_combo.pack(side=tk.RIGHT, padx=10)
        stop_combo.bind('<<ComboboxSelected>>', self.update_stop_key)
        
        # Кнопки управления
        frame_control = tk.Frame(self.root, bg=self.colors['bg'])
        frame_control.pack(pady=10)
        
        self.start_btn = tk.Button(frame_control, text="▶ СТАРТ", command=self.toggle_running,
                                   bg=self.colors['success'], fg='white', width=18, height=2,
                                   font=('Arial', 12, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(frame_control, text="⏹ СТОП", command=self.stop,
                                  bg=self.colors['danger'], fg='white', width=18, height=2,
                                  font=('Arial', 12, 'bold'))
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Траектория
        frame_traj = tk.Frame(self.root, bg=self.colors['bg'])
        frame_traj.pack(pady=5)
        
        self.traj_btn = tk.Button(frame_traj, text="📐 Траектория ВКЛ (Ctrl+U)", 
                                  command=self.toggle_trajectory_gui,
                                  bg='#2d2d2d', fg='#00ff00', width=25)
        self.traj_btn.pack()
        
        # Сохранение
        btn_save = tk.Button(self.root, text="💾 Сохранить настройки", command=self.save_settings,
                             bg=self.colors['accent'], fg='white', width=25, height=1)
        btn_save.pack(pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_speed(self):
        settings['slide_speed'] = self.speed_var.get()
    
    def update_delay(self):
        settings['loop_delay'] = self.delay_var.get()
    
    def update_repeat(self):
        settings['slide_repeat'] = self.repeat_var.get()
        print(f"🔄 Повторений: {settings['slide_repeat']} (1 = туда-обратно)")
    
    def update_button(self, event=None):
        settings['click_button'] = self.button_var.get()
    
    def update_mode(self, event=None):
        settings['slide_mode'] = self.mode_var.get()
    
    def update_start_key(self, event=None):
        settings['start_key'] = self.start_key_var.get()
        save_settings()
    
    def update_stop_key(self, event=None):
        settings['stop_key'] = self.stop_key_var.get()
        save_settings()
    
    def toggle_trajectory_gui(self):
        status = toggle_trajectory()
        self.traj_btn.config(text=f"📐 Траектория {status} (Ctrl+U)", 
                            fg='#00ff00' if show_trajectory else '#ff4444')
        self.status_label.config(text=f"📐 Траектория: {status}", fg=self.colors['warning'])
    
    def update_list(self):
        self.listbox.delete(0, tk.END)
        for i, action in enumerate(actions, 1):
            if action['type'] == 'click':
                text = f"{i}. 🖱 Клик ({action['x']}, {action['y']})"
            else:
                text = f"{i}. 📍 Слайд ({action['x1']}, {action['y1']}) → ({action['x2']}, {action['y2']})"
            self.listbox.insert(tk.END, text)
    
    def add_click(self):
        pos = pyautogui.position()
        actions.append({'type': 'click', 'x': pos.x, 'y': pos.y})
        self.update_list()
        self.status_label.config(text=f"✅ Клик: ({pos.x}, {pos.y})", fg=self.colors['success'])
    
    def add_slide(self):
        global waiting_for_b, temp_points
        
        if not waiting_for_b:
            pos = pyautogui.position()
            temp_points = [(pos.x, pos.y)]
            waiting_for_b = True
            self.status_label.config(text=f"📍 Точка А: ({pos.x}, {pos.y}) → Наведи на Б и нажми F2", 
                                    fg=self.colors['warning'])
        else:
            pos = pyautogui.position()
            temp_points.append((pos.x, pos.y))
            actions.append({
                'type': 'slide',
                'x1': temp_points[0][0],
                'y1': temp_points[0][1],
                'x2': temp_points[1][0],
                'y2': temp_points[1][1]
            })
            self.update_list()
            
            if show_trajectory:
                threading.Thread(target=show_trajectory_line, args=(temp_points[0], temp_points[1]), daemon=True).start()
            
            waiting_for_b = False
            temp_points = []
            self.status_label.config(text=f"✅ Слайд добавлен! (повторений: {settings['slide_repeat']})", 
                                    fg=self.colors['success'])
    
    def remove_last(self):
        if actions:
            actions.pop()
            self.update_list()
            self.status_label.config(text="🗑 Удалено последнее", fg=self.colors['warning'])
        else:
            self.status_label.config(text="❌ Нет действий", fg=self.colors['danger'])
    
    def clear_all(self):
        actions.clear()
        self.update_list()
        self.status_label.config(text="🧹 Все удалено", fg=self.colors['danger'])
    
    def toggle_running(self):
        global running
        if not actions:
            messagebox.showwarning("Предупреждение", "Нет действий для выполнения!")
            return
        
        running = not running
        if running:
            self.status_label.config(text="🟢 ЗАПУЩЕН!", fg=self.colors['success'])
            self.start_btn.config(text="▶ РАБОТАЕТ", bg=self.colors['success'])
            threading.Thread(target=main_loop, daemon=True).start()
        else:
            self.status_label.config(text="🔴 ОСТАНОВЛЕН", fg=self.colors['danger'])
            self.start_btn.config(text="▶ СТАРТ", bg=self.colors['success'])
    
    def stop(self):
        global running
        running = False
        self.status_label.config(text="🔴 ОСТАНОВЛЕН", fg=self.colors['danger'])
        self.start_btn.config(text="▶ СТАРТ", bg=self.colors['success'])
    
    def save_settings(self):
        global settings
        settings['slide_speed'] = self.speed_var.get()
        settings['loop_delay'] = self.delay_var.get()
        settings['slide_mode'] = self.mode_var.get()
        settings['click_button'] = self.button_var.get()
        settings['start_key'] = self.start_key_var.get()
        settings['stop_key'] = self.stop_key_var.get()
        settings['slide_repeat'] = self.repeat_var.get()
        save_settings()
        self.status_label.config(text="✅ Настройки сохранены!", fg=self.colors['success'])
    
    def start_key_listener(self):
        def on_press(key):
            try:
                if settings['start_key'] == 'enter' and key == Key.enter:
                    self.root.after(0, self.toggle_running)
                elif settings['start_key'] == 'f3' and key == Key.f3:
                    self.root.after(0, self.toggle_running)
                elif settings['start_key'] == 'f4' and key == Key.f4:
                    self.root.after(0, self.toggle_running)
                
                if settings['stop_key'] == 'enter' and key == Key.enter:
                    self.root.after(0, self.stop)
                elif settings['stop_key'] == 'f3' and key == Key.f3:
                    self.root.after(0, self.stop)
                elif settings['stop_key'] == 'f4' and key == Key.f4:
                    self.root.after(0, self.stop)
                
                if key == Key.f1:
                    self.root.after(0, self.add_click)
                elif key == Key.f2:
                    self.root.after(0, self.add_slide)
            except:
                pass
        
        listener = KeyListener(on_press=on_press)
        listener.daemon = True
        listener.start()
    
    def start_mouse_listener(self):
        def on_click(x, y, button, pressed):
            if pressed:
                if button == Button.x2:
                    if settings['start_key'] == 'mouse5':
                        self.root.after(0, self.toggle_running)
                    if settings['stop_key'] == 'mouse5':
                        self.root.after(0, self.stop)
                
                elif button == Button.x1:
                    if settings['start_key'] == 'mouse4':
                        self.root.after(0, self.toggle_running)
                    if settings['stop_key'] == 'mouse4':
                        self.root.after(0, self.stop)
        
        listener = MouseListener(on_click=on_click)
        listener.daemon = True
        listener.start()
    
    def on_close(self):
        global running
        running = False
        save_settings()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    load_settings()
    app = AutoClickerGUI()
    app.run()