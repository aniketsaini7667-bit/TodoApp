import os
import json
import datetime
import shutil
import sys
import time
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk

from data_manager import DataManager, DATA_FILE, application_path
from utils import hex_to_rgba

class TodoApp(ctk.CTk):
    def check_crash_recovery(self):
        s = self.data_manager.data["settings"]
        if s.get("sw_running", False):
            last_hb = s.get("sw_last_heartbeat", 0)
            if last_hb > 0:
                elapsed_ms = (last_hb - s.get("sw_start", 0)) * 1000
                s["sw_elapsed"] = max(0, elapsed_ms)
            s["sw_running"] = False
            self.commit_all_time(s.get("sw_elapsed", 0))
            self.data_manager.save_data()

    def __init__(self):
        super().__init__()
        
        self.data_manager = DataManager(DATA_FILE)
        self.check_crash_recovery()
        
        ctk.set_appearance_mode("dark")
        
        self.apply_window_settings()

        self.title("Todo List - Pro")
        
        # Removed the WM_DELETE_WINDOW intercept so clicking X actually closes        
        # Use direct env variable to bypass IDE linter warnings about tempfile
        self.temp_icon_path = os.path.join(os.environ.get('TEMP', application_path), "todo_dynamic_icon.ico")
        
        # Delay the initial icon update with a robust 2-second timer. 
        self.update_idletasks()
        self.after(2000, self.update_app_icon)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- HEADER ----------------
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="My Tasks", font=("Segoe UI", 28, "bold"), text_color="#FFFFFF")
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.toggle_mode_btn = ctk.CTkButton(self.header_frame, text="🗕", width=45, height=45, font=("Segoe UI", 18), fg_color="#1A1A1A", hover_color="#333333", command=self.toggle_mini_mode)
        self.toggle_mode_btn.grid(row=0, column=1, sticky="e", padx=(0, 10))
        
        self.stats_btn = ctk.CTkButton(self.header_frame, text="📊", width=45, height=45, font=("Segoe UI", 18), fg_color="#1A1A1A", hover_color="#333333", command=self.toggle_stats_view)
        self.stats_btn.grid(row=0, column=2, sticky="e", padx=(0, 10))

        self.settings_btn = ctk.CTkButton(self.header_frame, text="⚙️", width=45, height=45, font=("Segoe UI", 18), fg_color="#1A1A1A", hover_color="#333333", command=self.toggle_settings_view)
        self.settings_btn.grid(row=0, column=3, sticky="e", padx=(0, 10))

        self.quit_header_btn = ctk.CTkButton(self.header_frame, text="🛑", width=45, height=45, font=("Segoe UI", 18), fg_color="#1A1A1A", hover_color="#AA0000", command=self.destroy)
        self.quit_header_btn.grid(row=0, column=4, sticky="e")

        # ---------------- MAIN CONTAINER ----------------
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # ---------------- TASKS VIEW (Primary) ----------------
        self.tasks_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tasks_view.grid(row=0, column=0, sticky="nsew")
        self.tasks_view.grid_columnconfigure(0, weight=1)
        self.tasks_view.grid_rowconfigure(1, weight=1)

        # ---------------- STATS VIEW ----------------
        self.stats_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.stats_view.grid_columnconfigure(0, weight=1)

        # Stopwatch Frame
        self.stopwatch_frame = ctk.CTkFrame(self.tasks_view, fg_color="#1a1a1a", corner_radius=10, height=60)
        self.stopwatch_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)
        self.stopwatch_frame.grid_columnconfigure(0, weight=1)
        self.stopwatch_frame.grid_columnconfigure(1, weight=0)
        
        self.lbl_sw_time = ctk.CTkLabel(self.stopwatch_frame, text="00:00:00", font=("Segoe UI", 28, "bold"), text_color="#ffffff")
        self.lbl_sw_time.grid(row=0, column=0, pady=10, padx=(20, 10), sticky="w")
        
        s = self.data_manager.data["settings"]
        start_txt = "Pause" if s.get("sw_running", False) else ("Resume" if s.get("sw_elapsed", 0) > 0 else "Start")
        start_color = "#28a745" if s.get("sw_running", False) else "#DC3545"
        text_col = "white"
        
        self.btn_sw_start = ctk.CTkButton(self.stopwatch_frame, text=start_txt, width=80, height=35, fg_color=start_color, text_color=text_col, font=("Segoe UI", 14, "bold"), command=self.toggle_stopwatch)
        self.btn_sw_start.grid(row=0, column=1, pady=10, padx=(10, 20), sticky="e")

        # Scrollable list
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tasks_view, fg_color="transparent")
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Input Frame
        self.input_frame = ctk.CTkFrame(self.tasks_view, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", pady=(10, 5))
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=0)
        self.input_frame.grid_columnconfigure(2, weight=0)

        self.entry_task = ctk.CTkEntry(self.input_frame, placeholder_text="What needs to be done?", height=40, fg_color="#121212", border_color="#333333", font=("Segoe UI", 14))
        self.entry_task.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.entry_task.bind("<Return>", lambda e: self.add_task())
        self.entry_task.focus_set()
        
        self.bind("<FocusIn>", self.on_window_focus)

        self.label_menu = ctk.CTkOptionMenu(
            self.input_frame, width=120, height=40, 
            fg_color="#121212", button_color="#222222", button_hover_color="#333333", font=("Segoe UI", 12),
            command=self.on_dropdown_change
        )
        self.label_menu.grid(row=0, column=1, padx=(0, 5))
        self.update_label_menu()

        self.add_btn = ctk.CTkButton(self.input_frame, text="Add", width=60, height=40, font=("Segoe UI", 14, "bold"), fg_color="#28a745", hover_color="#218838", command=self.add_task)
        self.add_btn.grid(row=0, column=2)

        # ---------------- SETTINGS VIEW ----------------
        self.settings_view = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        
        self.setup_settings_ui()
        self.load_tasks_ui()
        self.setup_global_hotkey()
        
        # ---------------- MINI TIMER CONTAINER ----------------
        self.is_mini_mode = False
        self.normal_geometry = ""
        
        self.mini_container = ctk.CTkFrame(self, fg_color="#000000") # OLED Black
        self.mini_container.grid_columnconfigure(0, weight=1)
        self.mini_container.grid_rowconfigure(0, weight=1)
        
        # Dimmer white to reduce OLED subpixel wear
        oled_color = self.data_manager.data["settings"].get("oled_text_color", "#B3B3B3")
        self.mini_lbl_sw_time = ctk.CTkLabel(self.mini_container, text="00:00:00", font=("Segoe UI", 36, "bold"), text_color=oled_color)
        self.mini_lbl_sw_time.place(relx=0.5, rely=0.5, anchor="center")
        
        # Drag window by clicking anywhere on the mini timer
        self.mini_lbl_sw_time.bind("<Button-1>", self.start_window_move)
        self.mini_lbl_sw_time.bind("<B1-Motion>", self.do_window_move)
        self.mini_container.bind("<Button-1>", self.start_window_move)
        self.mini_container.bind("<B1-Motion>", self.do_window_move)

        self.mini_btn_expand = ctk.CTkButton(self.mini_container, text="🗗", width=25, height=25, font=("Segoe UI", 12), fg_color="transparent", text_color="#888888", hover_color="#555555", command=self.toggle_mini_mode)
        
        # Completely hide the button until hovered to prevent burn-in
        def on_hover_enter(e): self.mini_btn_expand.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
        def on_hover_leave(e): self.mini_btn_expand.place_forget()
        
        self.mini_container.bind("<Enter>", on_hover_enter)
        self.mini_container.bind("<Leave>", on_hover_leave)
        self.mini_lbl_sw_time.bind("<Enter>", on_hover_enter)

        self.update_stopwatch_loop()
        self.current_view = "tasks"

    def start_window_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_window_move(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    def toggle_mini_mode(self):
        s = self.data_manager.data["settings"]
        if not self.is_mini_mode:
            self.is_mini_mode = True
            self.normal_geometry = self.geometry()
            
            self.withdraw() # Hide to apply overrideredirect smoothly
            self.overrideredirect(True)
            
            self.header_frame.grid_forget()
            self.main_container.grid_forget()
            self.mini_container.grid(row=0, column=0, sticky="nsew", rowspan=2)
            
            w = s.get("mini_window_width", 250)
            h = s.get("mini_window_height", 120)
            
            # Reposition to center of current geometry or keep position
            if "+" in self.normal_geometry:
                pos = self.normal_geometry.split("+", 1)[1]
                self.geometry(f"{w}x{h}+{pos}")
            else:
                self.geometry(f"{w}x{h}")
            
            try:
                alpha = float(s.get("mini_transparency", 1.0))
                self.attributes('-alpha', alpha)
            except:
                pass
                
            self.configure(fg_color="#000000")
            if not s.get("always_on_top", False):
                self.attributes('-topmost', True)
                
            self.deiconify()
            self.update() 
            
            # Keep the taskbar icon alive even when overrideredirect is True
            def apply_taskbar_hack():
                try:
                    import ctypes
                    hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
                    GWL_EXSTYLE = -20
                    WS_EX_APPWINDOW = 0x00040000
                    WS_EX_TOOLWINDOW = 0x00000080
                    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    style = style & ~WS_EX_TOOLWINDOW
                    style = style | WS_EX_APPWINDOW
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                    # Force Windows to apply the style and update the taskbar
                    ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010)
                    self.update_app_icon()
                except Exception:
                    pass
            self.after(100, apply_taskbar_hack)
        else:
            self.is_mini_mode = False
            
            self.withdraw()
            self.overrideredirect(False)
            
            self.mini_container.grid_forget()
            
            self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
            self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
            
            if self.normal_geometry:
                self.geometry(self.normal_geometry)
            else:
                self.apply_window_settings()
                
            self.attributes('-alpha', 1.0)
            bg = s.get("app_bg_color", "#000000")
            self.configure(fg_color=bg)
            if not s.get("always_on_top", False):
                self.attributes('-topmost', False)
                
            self.deiconify()
            self.update() # FORCE Tkinter to refresh the winfo_id cache!
            self.after(200, self.update_app_icon)
            
            # Restore the dark titlebar that Windows strips when toggling overrideredirect
            try:
                if hasattr(self, "_windows_set_titlebar_color"):
                    self._windows_set_titlebar_color(self._get_appearance_mode())
            except:
                pass


    def on_dropdown_change(self, choice):
        if "Q1" in choice:
            placeholder = "What is urgent & important today?"
        elif "Q2" in choice:
            placeholder = "What is important, but not urgent?"
        elif "Q3" in choice:
            placeholder = "What is urgent, but not important?"
        elif "Q4" in choice:
            placeholder = "What is neither urgent nor important?"
        else:
            placeholder = "What needs to be done?"
        self.entry_task.configure(placeholder_text=placeholder)

    def update_label_menu(self):
        quadrants = self.data_manager.data["quadrants"]
        options = [f"{v['emoji']} {v['name'].split(':')[0]}" for k, v in quadrants.items()]
        self.label_menu.configure(values=options)
        self.label_menu.set(options[0])
        self.on_dropdown_change(options[0])

    def apply_window_settings(self):
        s = self.data_manager.data["settings"]
        bg_color = s.get("app_bg_color", "#000000")
        w = s.get("window_width", 450)
        h = s.get("window_height", 650)
        is_top = s.get("always_on_top", False)
        
        try:
            self.configure(fg_color=bg_color)
        except Exception:
            self.configure(fg_color="#000000")
            
        self.geometry(f"{w}x{h}")
        self.attributes('-topmost', is_top)



    def update_advanced_stats(self):
        tasks = self.data_manager.data.get("tasks", [])
        history = self.data_manager.data.get("history", {})
        
        today = datetime.date.today()
        
        # 1. Update Heatmap
        for widget in self.heatmap_container.winfo_children():
            widget.destroy()
            
        for i in range(6, -1, -1):
            d = today - datetime.timedelta(days=i)
            d_str = str(d)
            if i == 0:
                # Today's count (Q1+Q2+Q3)
                count = len([t for t in tasks if t["completed"] and t.get("quadrant") in ["q1", "q2", "q3"]])
            else:
                h = history.get(d_str, {})
                count = h.get("q1", 0) + h.get("q2", 0) + h.get("q3", 0)
                
            # GitHub colors
            if count == 0:
                color = "#1E1E1E"
            elif count <= 2:
                color = "#0e4429"
            elif count <= 4:
                color = "#006d32"
            elif count <= 6:
                color = "#26a641"
            else:
                color = "#39d353"
                
            box = ctk.CTkFrame(self.heatmap_container, fg_color=color, height=35, corner_radius=4)
            box.grid(row=0, column=6-i, sticky="ew", padx=2)
            
            day_name = d.strftime("%a")
            ctk.CTkLabel(box, text=day_name, font=("Segoe UI", 9), text_color="#777777").place(relx=0.5, rely=0.5, anchor="center")

        # 2. ASCII Bar Chart (Today)
        q1_c = len([t for t in tasks if t["completed"] and t.get("quadrant") == "q1"])
        q2_c = len([t for t in tasks if t["completed"] and t.get("quadrant") == "q2"])
        q3_c = len([t for t in tasks if t["completed"] and t.get("quadrant") == "q3"])
        q4_c = len([t for t in tasks if t["completed"] and t.get("quadrant") == "q4"])
        
        ascii_text = f"Q1 (Fire)   : {'█' * q1_c} ({q1_c})\n"
        ascii_text += f"Q2 (Growth) : {'█' * q2_c} ({q2_c})\n"
        ascii_text += f"Q3 (Noise)  : {'█' * q3_c} ({q3_c})\n"
        ascii_text += f"Q4 (Waste)  : {'█' * q4_c} ({q4_c})"
        
        self.lbl_ascii_chart.configure(text=ascii_text)
        
        # 3. Matrix Health Score (Calculated from ALL active tasks)
        total_all_tasks = len(tasks)
        if total_all_tasks == 0:
            health = 0
            h_color = "#AAAAAA"
        else:
            # New Pro Rule: Your health is based on completing your most important tasks 
            # against your ENTIRE workload.
            health = int(((q1_c + q2_c) / total_all_tasks) * 100)
            
            if health >= 80:
                h_color = "#28a745"
            elif health >= 50:
                h_color = "#ffc107"
            elif health > 0:
                h_color = "#DC3545"
            else:
                h_color = "#AAAAAA"
                
        self.lbl_matrix_health.configure(text=f"Matrix Health: {health}/100", text_color=h_color)

    def toggle_stats_view(self):
        if self.current_view != "stats":
            self.tasks_view.grid_forget()
            self.settings_view.grid_forget()

            self.update_advanced_stats()
            self.stats_view.grid(row=0, column=0, sticky="nsew")
            self.title_label.configure(text="Analytics")
            self.stats_btn.configure(text="🔙")
            self.settings_btn.configure(text="⚙️")
            self.current_view = "stats"
        else:
            self.stats_view.grid_forget()
            self.tasks_view.grid(row=0, column=0, sticky="nsew")
            self.title_label.configure(text="My Tasks")
            self.stats_btn.configure(text="📊")
            self.current_view = "tasks"

    def toggle_settings_view(self):
        if self.current_view != "settings":
            self.tasks_view.grid_forget()
            self.stats_view.grid_forget()
            self.settings_view.grid(row=0, column=0, sticky="nsew")
            self.title_label.configure(text="Settings")
            self.settings_btn.configure(text="🔙")
            self.stats_btn.configure(text="📊")
            self.current_view = "settings"
        else:
            self.settings_view.grid_forget()
            self.tasks_view.grid(row=0, column=0, sticky="nsew")
            self.title_label.configure(text="My Tasks")
            self.settings_btn.configure(text="⚙️")
            self.current_view = "tasks"
            
    def toggle_zen_mode(self):
        self.data_manager.data["settings"]["zen_mode"] = self.zen_var.get()
        self.data_manager.save_data()
        self.load_tasks_ui()

    def setup_global_hotkey(self):
        try:
            import keyboard
            hotkey = self.data_manager.data["settings"].get("global_hotkey", "alt+t")
            sw_hotkey = self.data_manager.data["settings"].get("sw_hotkey", "alt+s")
            mini_hotkey = self.data_manager.data["settings"].get("mini_hotkey", "alt+m")
            keyboard.unhook_all()
            keyboard.add_hotkey(hotkey, self.on_global_hotkey)
            keyboard.add_hotkey(sw_hotkey, self.on_sw_hotkey)
            keyboard.add_hotkey(mini_hotkey, self.on_mini_hotkey)
        except Exception as e:
            print("Hotkey error:", e)

    def on_mini_hotkey(self):
        t = time.time()
        if t - getattr(self, "_last_hk_mini", 0) > 0.5:
            self._last_hk_mini = t
            self.after(0, self.toggle_mini_mode)

    def on_global_hotkey(self):
        t = time.time()
        if t - getattr(self, "_last_hk_global", 0) > 0.5:
            self._last_hk_global = t
            self.after(0, self.toggle_visibility)
        
    def on_sw_hotkey(self):
        t = time.time()
        if t - getattr(self, "_last_hk_sw", 0) > 0.5:
            self._last_hk_sw = t
            self.after(0, self.toggle_stopwatch)

    def on_window_focus(self, event):
        if getattr(event, "widget", None) == self:
            if hasattr(self, "entry_task") and self.entry_task.winfo_ismapped():
                self.entry_task.focus_set()

    def toggle_visibility(self):
        is_minimized_natively = False
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
            is_minimized_natively = ctypes.windll.user32.IsIconic(hwnd)
        except:
            pass

        if self.state() == 'iconic' or self.state() == 'withdrawn' or is_minimized_natively:
            if getattr(self, "is_mini_mode", False):
                try:
                    import ctypes
                    hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
                    ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
                except:
                    pass
                    
            self.deiconify()
            self.state('normal')
            
            is_top = self.data_manager.data["settings"].get("always_on_top", False)
            self.attributes('-topmost', True)
            self.update()
            if not is_top and not getattr(self, "is_mini_mode", False):
                self.attributes('-topmost', False)
                
            self.lift()
            self.focus_force()
            if not getattr(self, "is_mini_mode", False):
                if hasattr(self, "entry_task"):
                    self.after(100, lambda: self.entry_task.focus_set())
            else:
                def apply_taskbar_hack():
                    try:
                        import ctypes
                        hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
                        GWL_EXSTYLE = -20
                        WS_EX_APPWINDOW = 0x00040000
                        WS_EX_TOOLWINDOW = 0x00000080
                        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                        style = style & ~WS_EX_TOOLWINDOW
                        style = style | WS_EX_APPWINDOW
                        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010)
                        self.update_app_icon()
                    except Exception:
                        pass
                self.after(100, apply_taskbar_hack)
        else:
            if getattr(self, "is_mini_mode", False):
                try:
                    import ctypes
                    hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
                    ctypes.windll.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE
                except Exception:
                    self.withdraw()
            else:
                self.iconify()

    def toggle_always_on_top(self):
        is_top = self.always_top_var.get()
        self.attributes('-topmost', is_top)
        self.data_manager.data["settings"]["always_on_top"] = is_top
        self.data_manager.save_data()

    def update_stopwatch_loop(self):
        s = self.data_manager.data["settings"]
        if s.get("sw_running", False):
            elapsed_ms = (time.time() - s.get("sw_start", 0)) * 1000
            
            current_time = time.time()
            heartbeat_sec = float(s.get("heartbeat_mins", 10)) * 60.0
            if current_time - getattr(self, "_last_sw_heartbeat", 0) > heartbeat_sec:
                s["sw_last_heartbeat"] = current_time
                self._last_sw_heartbeat = current_time
                self.data_manager.save_data()
        else:
            elapsed_ms = s.get("sw_elapsed", 0)
            
        total_sec = int(elapsed_ms // 1000)
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        sec = total_sec % 60
        time_str = f"{h:02d}:{m:02d}:{sec:02d}"
        self.lbl_sw_time.configure(text=time_str)
        if hasattr(self, 'mini_lbl_sw_time'):
            self.mini_lbl_sw_time.configure(text=time_str)
            
            # OLED Pixel Shifting - Based on REAL time, not stopwatch time
            current_time = time.time()
            if getattr(self, "is_mini_mode", False):
                last_shift = getattr(self, "_last_pixel_shift", 0)
                # Shifting every 5 seconds so you can physically see it working!
                shift_interval = int(s.get("oled_shift_sec", 60))
                if current_time - last_shift > shift_interval:
                    self._last_pixel_shift = current_time
                    import random
                    # Shift radius large enough to see it jump clearly
                    rx = 0.5 + random.uniform(-0.1, 0.1)
                    ry = 0.5 + random.uniform(-0.1, 0.1)
                    self.mini_lbl_sw_time.place_configure(relx=rx, rely=ry)
        
        all_time_ms = s.get("sw_all_time", 0)
        last_rec = s.get("sw_last_recorded", 0)
        delta = max(0, elapsed_ms - last_rec)
        total_all_time_sec = int((all_time_ms + delta) // 1000)
        
        days = total_all_time_sec // 86400
        ah = (total_all_time_sec % 86400) // 3600
        am = (total_all_time_sec % 3600) // 60
        if hasattr(self, 'lbl_all_time') and self.lbl_all_time.winfo_exists():
            self.lbl_all_time.configure(text=f"{days} Day {ah:02d} Hour {am:02d} Min")
        
        self.after(1000, self.update_stopwatch_loop)
        
    def commit_all_time(self, current_elapsed):
        s = self.data_manager.data["settings"]
        last_rec = s.get("sw_last_recorded", 0)
        delta = max(0, current_elapsed - last_rec)
        if delta > 0:
            s["sw_all_time"] = s.get("sw_all_time", 0) + delta
            s["sw_last_recorded"] = current_elapsed
            self.data_manager.save_data()
            
    def toggle_stopwatch(self):
        s = self.data_manager.data["settings"]
        if not s.get("sw_running", False):
            s["sw_running"] = True
            s["sw_start"] = time.time() - (s.get("sw_elapsed", 0) / 1000.0)
            self.btn_sw_start.configure(text="Pause", fg_color="#28a745", hover_color="#218838", text_color="white")
        else:
            elapsed_ms = (time.time() - s.get("sw_start", 0)) * 1000
            self.commit_all_time(elapsed_ms)
            s["sw_running"] = False
            s["sw_elapsed"] = elapsed_ms
            self.btn_sw_start.configure(text="Resume", fg_color="#DC3545", hover_color="#c82333", text_color="white")
        self.data_manager.save_data()
        self.update_app_icon()
        
    def reset_stopwatch(self):
        s = self.data_manager.data["settings"]
        if s.get("sw_running", False):
            elapsed_ms = (time.time() - s.get("sw_start", 0)) * 1000
            self.commit_all_time(elapsed_ms)
        elif s.get("sw_elapsed", 0) > 0:
            self.commit_all_time(s.get("sw_elapsed", 0))
            
        s["sw_running"] = False
        s["sw_elapsed"] = 0.0
        s["sw_start"] = 0.0
        s["sw_last_recorded"] = 0.0
        self.btn_sw_start.configure(text="Start", fg_color="#DC3545", hover_color="#c82333", text_color="white")
        self.data_manager.save_data()
        self.lbl_sw_time.configure(text="00:00:00")
        if hasattr(self, 'mini_lbl_sw_time'): self.mini_lbl_sw_time.configure(text="00:00:00")
        self.update_app_icon()

    def setup_settings_ui(self):
        self.settings_view.grid_columnconfigure(0, weight=1)
        current_row = 0
        s = self.data_manager.data["settings"]

        # ---------------------------------------------------------
        # LIFETIME PRODUCTIVITY
        # ---------------------------------------------------------
        stats_frame = ctk.CTkFrame(self.stats_view, fg_color="#121212", corner_radius=8)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(10, 20))
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        
        # Top Center: Total Days
        install_date_str = s.get("install_date", str(datetime.date.today()))
        try:
            install_dt = datetime.datetime.strptime(install_date_str, "%Y-%m-%d").date()
            total_days = (datetime.date.today() - install_dt).days + 1
        except Exception:
            total_days = 1
            
        days_lbl = ctk.CTkLabel(stats_frame, text=f"Total {total_days} Days", font=("Segoe UI", 16, "bold"), text_color="#FFD700")
        days_lbl.grid(row=0, column=0, columnspan=2, pady=(10, 0))
        
        avg_ms = s.get("sw_all_time", 0) / total_days if total_days > 0 else 0
        avg_h = int(avg_ms // (1000 * 3600))
        avg_m = int((avg_ms % (1000 * 3600)) // (1000 * 60))
        avg_lbl = ctk.CTkLabel(stats_frame, text=f"📊 Avg Focus: {avg_h}h {avg_m}m/day   |   🔥 {s.get('streak', 1)} Day Streak", font=("Segoe UI", 16, "bold"), text_color="#00FFCC")
        avg_lbl.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Left side: Reset Button
        reset_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
        reset_frame.grid(row=2, column=0, sticky="w", padx=15, pady=15)
        ctk.CTkLabel(reset_frame, text="Stopwatch Controls", font=("Segoe UI", 12), text_color="#AAAAAA").pack(anchor="w", pady=(0, 5))
        self.reset_sw_btn = ctk.CTkButton(reset_frame, text="🔄 Reset", width=90, height=35, fg_color="#1A1A1A", hover_color="#c82333", font=("Segoe UI", 14, "bold"), command=self.reset_stopwatch)
        self.reset_sw_btn.pack(anchor="w")

        # Right side: Lifetime Stats
                
        # Zen Mode
        zen_frame = ctk.CTkFrame(self.stats_view, fg_color="transparent")
        zen_frame.grid(row=2, column=0, sticky="ew", pady=10)
        
        self.zen_var = ctk.BooleanVar(value=s.get("zen_mode", False))
        ctk.CTkSwitch(zen_frame, text="🧘‍♂️ Zen Mode (Hide Q3/Q4)", variable=self.zen_var, command=self.toggle_zen_mode).grid(row=0, column=0, padx=5, sticky="w")

        # ---------------- ADVANCED STATS ----------------
        self.adv_stats_frame = ctk.CTkFrame(self.stats_view, fg_color="transparent")
        self.adv_stats_frame.grid(row=3, column=0, sticky="ew", pady=10, padx=15)
        self.adv_stats_frame.grid_columnconfigure(0, weight=1)
        
        # 1. 7-Day Heatmap
        hm_label = ctk.CTkLabel(self.adv_stats_frame, text="7-Day Focus Heatmap", font=("Segoe UI", 14, "bold"))
        hm_label.pack(anchor="w", pady=(0, 5))
        
        self.heatmap_container = ctk.CTkFrame(self.adv_stats_frame, fg_color="transparent")
        self.heatmap_container.pack(fill="x", pady=(0, 15))
        # Allow expanding
        for i in range(7):
            self.heatmap_container.grid_columnconfigure(i, weight=1)
            
        # 2. ASCII Bar Chart
        bar_label = ctk.CTkLabel(self.adv_stats_frame, text="Today's Quadrant Flow", font=("Segoe UI", 14, "bold"))
        bar_label.pack(anchor="w", pady=(0, 5))
        self.lbl_ascii_chart = ctk.CTkLabel(self.adv_stats_frame, text="", font=("Courier New", 12), justify="left")
        self.lbl_ascii_chart.pack(anchor="w", pady=(0, 15))
        
        # 3. Matrix Health Score
        self.lbl_matrix_health = ctk.CTkLabel(self.adv_stats_frame, text="Matrix Health: 0/100", font=("Segoe UI", 20, "bold"))
        self.lbl_matrix_health.pack(anchor="w")


        prod_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
        prod_frame.grid(row=2, column=1, sticky="e", padx=15, pady=15)
        ctk.CTkLabel(prod_frame, text="Lifetime Productivity", font=("Segoe UI", 12), text_color="#AAAAAA").pack(anchor="e")
        self.lbl_total = ctk.CTkLabel(prod_frame, text=f"{s['total_completed']} Tasks Completed", font=("Segoe UI", 16, "bold"), text_color="#00AAFF")
        self.lbl_total.pack(anchor="e", pady=(2, 2))
        self.lbl_all_time = ctk.CTkLabel(prod_frame, text="0 Day 00 Hour 00 Min", font=("Segoe UI", 16, "bold"), text_color="#28a745")
        self.lbl_all_time.pack(anchor="e")
        
        # Time Adjustment
        adj_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
        adj_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=15)
        
        ctk.CTkLabel(adj_frame, text="Add Time:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 5))
        self.add_entry = ctk.CTkEntry(adj_frame, width=50, fg_color="#1A1A1A", border_color="#333333")
        self.add_entry.pack(side="left", padx=(0, 5))
        self.add_btn = ctk.CTkButton(adj_frame, text="Add", fg_color="#28a745", hover_color="#218838", width=50, command=self.add_time)
        self.add_btn.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(adj_frame, text="Reduce Time:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 5))
        self.reduce_entry = ctk.CTkEntry(adj_frame, width=50, fg_color="#1A1A1A", border_color="#333333")
        self.reduce_entry.pack(side="left", padx=(0, 5))
        self.reduce_btn = ctk.CTkButton(adj_frame, text="Reduce", fg_color="#DC3545", hover_color="#c82333", width=50, command=self.reduce_time)
        self.reduce_btn.pack(side="left")

        # ---------------------------------------------------------
        # GENERAL PREFERENCES
        # ---------------------------------------------------------
        ctk.CTkLabel(self.settings_view, text="General Preferences", font=("Segoe UI", 16, "bold")).grid(row=1, column=0, sticky="w", pady=(10, 5))
        
        toggles_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        toggles_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        toggles_frame.grid_columnconfigure(0, weight=1)
        toggles_frame.grid_columnconfigure(1, weight=1)
        
        self.sound_var = ctk.BooleanVar(value=s.get("sound_effects", True))
        ctk.CTkSwitch(toggles_frame, text="Sound Effects 🔔", variable=self.sound_var).grid(row=0, column=0, padx=5, sticky="w")
        self.always_top_var = ctk.BooleanVar(value=s.get("always_on_top", False))
        ctk.CTkSwitch(toggles_frame, text="Always on Top 📌", variable=self.always_top_var, command=self.toggle_always_on_top).grid(row=0, column=1, padx=5, sticky="e")

        time_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        time_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        time_frame.grid_columnconfigure(0, weight=1)
        time_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(time_frame, text="Day Start (HH:MM)", font=("Segoe UI", 12)).grid(row=0, column=0, pady=5, sticky="w")
        self.start_entry = ctk.CTkEntry(time_frame, fg_color="#121212", border_color="#333333", width=120)
        self.start_entry.insert(0, s["day_start"])
        self.start_entry.grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(time_frame, text="Day End (HH:MM)", font=("Segoe UI", 12)).grid(row=0, column=1, pady=5, sticky="e")
        self.end_entry = ctk.CTkEntry(time_frame, fg_color="#121212", border_color="#333333", width=120)
        self.end_entry.insert(0, s["day_end"])
        self.end_entry.grid(row=1, column=1, sticky="e")

        # ---------------------------------------------------------
        # HOTKEYS & CONTROLS
        # ---------------------------------------------------------
        ctk.CTkLabel(self.settings_view, text="Hotkeys & Controls", font=("Segoe UI", 16, "bold")).grid(row=4, column=0, sticky="w", pady=(10, 5))
        hotkey_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        hotkey_frame.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        hotkey_frame.grid_columnconfigure(0, weight=1)
        hotkey_frame.grid_columnconfigure(1, weight=1)
        hotkey_frame.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(hotkey_frame, text="App Toggle Hotkey", font=("Segoe UI", 12)).grid(row=0, column=0, pady=5, sticky="w")
        self.hotkey_entry = ctk.CTkEntry(hotkey_frame, fg_color="#121212", border_color="#333333", width=90)
        self.hotkey_entry.insert(0, s.get("global_hotkey", "alt+t"))
        self.hotkey_entry.grid(row=1, column=0, sticky="w")
        
        ctk.CTkLabel(hotkey_frame, text="Stopwatch Hotkey", font=("Segoe UI", 12)).grid(row=0, column=1, pady=5)
        self.sw_hotkey_entry = ctk.CTkEntry(hotkey_frame, fg_color="#121212", border_color="#333333", width=90)
        self.sw_hotkey_entry.insert(0, s.get("sw_hotkey", "alt+s"))
        self.sw_hotkey_entry.grid(row=1, column=1)
        
        ctk.CTkLabel(hotkey_frame, text="Mini Mode Hotkey", font=("Segoe UI", 12)).grid(row=0, column=2, pady=5, sticky="e")
        self.mini_hotkey_entry = ctk.CTkEntry(hotkey_frame, fg_color="#121212", border_color="#333333", width=90)
        self.mini_hotkey_entry.insert(0, s.get("mini_hotkey", "alt+m"))
        self.mini_hotkey_entry.grid(row=1, column=2, sticky="e")

        # ---------------------------------------------------------
        # APPEARANCE & COLORS
        # ---------------------------------------------------------
        ctk.CTkLabel(self.settings_view, text="Appearance & Colors", font=("Segoe UI", 16, "bold")).grid(row=6, column=0, sticky="w", pady=(10, 5))
        dim_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        dim_frame.grid(row=7, column=0, sticky="ew", pady=(0, 10))
        dim_frame.grid_columnconfigure(0, weight=1)
        dim_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(dim_frame, text="Window Width", font=("Segoe UI", 12)).grid(row=0, column=0, pady=5, sticky="w")
        self.width_entry = ctk.CTkEntry(dim_frame, fg_color="#121212", border_color="#333333", width=120)
        self.width_entry.insert(0, str(s.get("window_width", 450)))
        self.width_entry.grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(dim_frame, text="Window Height", font=("Segoe UI", 12)).grid(row=0, column=1, pady=5, sticky="e")
        self.height_entry = ctk.CTkEntry(dim_frame, fg_color="#121212", border_color="#333333", width=120)
        self.height_entry.insert(0, str(s.get("window_height", 650)))
        self.height_entry.grid(row=1, column=1, sticky="e")

        color_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        color_frame.grid(row=8, column=0, sticky="ew", pady=(0, 20))
        color_frame.grid_columnconfigure(0, weight=1)
        color_frame.grid_columnconfigure(1, weight=1)
        color_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(color_frame, text="App Bg (Hex)", font=("Segoe UI", 12)).grid(row=0, column=0, pady=5)
        self.bg_color_entry = ctk.CTkEntry(color_frame, fg_color="#121212", border_color="#333333", width=90)
        self.bg_color_entry.insert(0, s.get("app_bg_color", "#000000"))
        self.bg_color_entry.grid(row=1, column=0)

        ctk.CTkLabel(color_frame, text="Task Badge", font=("Segoe UI", 12)).grid(row=0, column=1, pady=5)
        self.badge_color_entry = ctk.CTkEntry(color_frame, fg_color="#121212", border_color="#333333", width=90)
        self.badge_color_entry.insert(0, s.get("badge_color", "#DC3545"))
        self.badge_color_entry.grid(row=1, column=1)
        
        ctk.CTkLabel(color_frame, text="SW Badge", font=("Segoe UI", 12)).grid(row=0, column=2, pady=5)
        self.sw_badge_color_entry = ctk.CTkEntry(color_frame, fg_color="#121212", border_color="#333333", width=90)
        self.sw_badge_color_entry.insert(0, s.get("sw_badge_color", "#28a745"))
        self.sw_badge_color_entry.grid(row=1, column=2)
        
        # ---------------------------------------------------------
        # MINI TIMER SETTINGS
        # ---------------------------------------------------------
        mini_dim_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        mini_dim_frame.grid(row=9, column=0, sticky="ew", pady=(0, 10))
        mini_dim_frame.grid_columnconfigure(0, weight=1)
        mini_dim_frame.grid_columnconfigure(1, weight=1)
        mini_dim_frame.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(mini_dim_frame, text="Mini Width", font=("Segoe UI", 12)).grid(row=0, column=0, pady=5, sticky="w")
        self.mini_width_entry = ctk.CTkEntry(mini_dim_frame, fg_color="#121212", border_color="#333333", width=80)
        self.mini_width_entry.insert(0, str(s.get("mini_window_width", 250)))
        self.mini_width_entry.grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(mini_dim_frame, text="Mini Height", font=("Segoe UI", 12)).grid(row=0, column=1, pady=5)
        self.mini_height_entry = ctk.CTkEntry(mini_dim_frame, fg_color="#121212", border_color="#333333", width=80)
        self.mini_height_entry.insert(0, str(s.get("mini_window_height", 120)))
        self.mini_height_entry.grid(row=1, column=1)
        
        ctk.CTkLabel(mini_dim_frame, text="Mini Opacity (0.1-1.0)", font=("Segoe UI", 12)).grid(row=0, column=2, pady=5, sticky="e")
        self.mini_alpha_entry = ctk.CTkEntry(mini_dim_frame, fg_color="#121212", border_color="#333333", width=80)
        self.mini_alpha_entry.insert(0, str(s.get("mini_transparency", 1.0)))
        self.mini_alpha_entry.grid(row=1, column=2, sticky="e")
        
        ctk.CTkLabel(mini_dim_frame, text="OLED Shift (sec)", font=("Segoe UI", 12)).grid(row=2, column=0, pady=(10,5), sticky="w")
        self.oled_shift_entry = ctk.CTkEntry(mini_dim_frame, fg_color="#121212", border_color="#333333", width=80)
        self.oled_shift_entry.insert(0, str(s.get("oled_shift_sec", 60)))
        self.oled_shift_entry.grid(row=3, column=0, sticky="w")
        
        ctk.CTkLabel(mini_dim_frame, text="OLED Text Color", font=("Segoe UI", 12)).grid(row=2, column=1, pady=(10,5))
        self.oled_color_entry = ctk.CTkEntry(mini_dim_frame, fg_color="#121212", border_color="#333333", width=80)
        self.oled_color_entry.insert(0, s.get("oled_text_color", "#B3B3B3"))
        self.oled_color_entry.grid(row=3, column=1)

        # ---------------------------------------------------------
        # TASK LEVELS
        # ---------------------------------------------------------
        ctk.CTkLabel(self.settings_view, text="Time Management Matrix", font=("Segoe UI", 16, "bold")).grid(row=10, column=0, sticky="w", pady=(10, 5))
        
        self.label_entries = {}
        labels_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        labels_frame.grid(row=11, column=0, sticky="ew", pady=(0, 20))
        labels_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(labels_frame, text="Emoji", font=("Segoe UI", 12)).grid(row=0, column=0, padx=2)
        ctk.CTkLabel(labels_frame, text="Level Name", font=("Segoe UI", 12)).grid(row=0, column=1, padx=2, sticky="w")
        ctk.CTkLabel(labels_frame, text="Hex Color", font=("Segoe UI", 12)).grid(row=0, column=2, padx=2)
        
        quadrants_data = self.data_manager.data["quadrants"]
        for idx, (lbl_key, lbl_val) in enumerate(quadrants_data.items()):
            row = idx + 1
            e_emoji = ctk.CTkEntry(labels_frame, width=40, fg_color="#121212", border_color="#333333", justify="center")
            e_emoji.insert(0, lbl_val["emoji"])
            e_emoji.grid(row=row, column=0, padx=2, pady=2)
            
            e_name = ctk.CTkEntry(labels_frame, fg_color="#121212", border_color="#333333")
            e_name.insert(0, lbl_val["name"])
            e_name.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
            
            e_color = ctk.CTkEntry(labels_frame, width=70, fg_color="#121212", border_color="#333333", justify="center")
            e_color.insert(0, lbl_val["color"])
            e_color.grid(row=row, column=2, padx=2, pady=2)
            
            self.label_entries[lbl_key] = {"emoji": e_emoji, "name": e_name, "color": e_color}

        # ---------------------------------------------------------
        # DATA & BACKUP
        # ---------------------------------------------------------
        backup_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        backup_frame.grid(row=12, column=0, sticky="ew", pady=(10, 15))
        backup_frame.grid_columnconfigure(0, weight=1)
        backup_frame.grid_columnconfigure(1, weight=1)
        
        btn_export = ctk.CTkButton(backup_frame, text="💾 Export Data", fg_color="#17a2b8", hover_color="#138496", font=("Segoe UI", 12, "bold"), command=self.export_backup)
        btn_export.grid(row=0, column=0, padx=5, sticky="ew")
        
        btn_import = ctk.CTkButton(backup_frame, text="📂 Import Data", fg_color="#ffc107", hover_color="#e0a800", text_color="black", font=("Segoe UI", 12, "bold"), command=self.import_backup)
        btn_import.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Advanced Settings
        adv_frame = ctk.CTkFrame(self.settings_view, fg_color="transparent")
        adv_frame.grid(row=13, column=0, sticky="ew", pady=(10, 0))
        ctk.CTkLabel(adv_frame, text="Data Heartbeat (Mins):", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.hb_entry = ctk.CTkEntry(adv_frame, width=60, fg_color="#121212", border_color="#333333")
        self.hb_entry.insert(0, str(s.get("heartbeat_mins", 10)))
        self.hb_entry.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(self.settings_view, text="Save & Apply", fg_color="#0055FF", hover_color="#0044CC", font=("Segoe UI", 14, "bold"), command=self.save_settings)
        save_btn.grid(row=14, column=0, pady=20)

    def add_time(self):
        import tkinter.messagebox
        val = self.add_entry.get()
        try:
            mins = float(val)
            if mins <= 0: return
        except ValueError:
            return
            
        # Rule 1: Cannot add more than 12 hours at once
        if mins > 720:
            tkinter.messagebox.showerror("Limit Exceeded", "You cannot add more than 12 hours (720 mins) at once!")
            return
            
        s = self.data_manager.data["settings"]
        
        current_today_ms = s.get("sw_elapsed", 0)
        if s.get("sw_running", False):
            current_today_ms += (time.time() - s.get("sw_start", 0)) * 1000
            
        ms_add = mins * 60 * 1000
        
        # Rule 2: Total time today cannot exceed 18 hours
        if (current_today_ms + ms_add) > (18 * 60 * 60 * 1000):
            tkinter.messagebox.showerror("Limit Exceeded", "Total focused time today cannot exceed 18 hours! Take a break!")
            return
            
        confirm = tkinter.messagebox.askyesno("Confirm", f"Add {mins} minutes to today & lifetime?")
        if not confirm: return
        
        s["sw_elapsed"] = s.get("sw_elapsed", 0) + ms_add
        s["sw_all_time"] = s.get("sw_all_time", 0) + ms_add
        s["sw_last_recorded"] = s.get("sw_last_recorded", 0) + ms_add
        
        if s.get("sw_running", False):
            s["sw_start"] -= (ms_add / 1000.0)
            
        self.data_manager.save_data()
        self.add_entry.delete(0, 'end')
        tkinter.messagebox.showinfo("Success", f"Added {mins} minutes.")

    def reduce_time(self):
        import tkinter.messagebox
        val = self.reduce_entry.get()
        try:
            mins = float(val)
            if mins <= 0: return
        except ValueError:
            return
            
        ms_reduce = mins * 60 * 1000
        s = self.data_manager.data["settings"]
        
        current_today_ms = s.get("sw_elapsed", 0)
        if s.get("sw_running", False):
            current_today_ms += (time.time() - s.get("sw_start", 0)) * 1000
            
        if ms_reduce > current_today_ms:
            tkinter.messagebox.showerror("Error", f"Cannot reduce {mins} mins. You only have {int(current_today_ms // 60000)} mins recorded today.")
            return
            
        if ms_reduce > s.get("sw_all_time", 0):
            tkinter.messagebox.showerror("Error", f"Cannot reduce {mins} mins. Exceeds lifetime total.")
            return
            
        confirm = tkinter.messagebox.askyesno("Confirm", f"Reduce {mins} minutes from today & lifetime?")
        if not confirm: return
        
        s["sw_elapsed"] = max(0, s.get("sw_elapsed", 0) - ms_reduce)
        s["sw_all_time"] = max(0, s.get("sw_all_time", 0) - ms_reduce)
        
        if s.get("sw_running", False):
            s["sw_start"] += (ms_reduce / 1000.0)
            
        self.data_manager.save_data()
        self.reduce_entry.delete(0, 'end')
        self.lbl_sw_time.configure(text="00:00:00")
        tkinter.messagebox.showinfo("Success", f"Reduced {mins} minutes.")

    def refresh_stats(self):
        total = self.data_manager.data["settings"]["total_completed"]
        self.lbl_total.configure(text=f"{total} Tasks Completed")

    def export_backup(self):
        filepath = ctk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile=f"TodoBackup_{datetime.date.today()}.json"
        )
        if filepath:
            shutil.copy2(DATA_FILE, filepath)
            
    def import_backup(self):
        filepath = ctk.filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")]
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if "settings" in data and "tasks" in data:
                    shutil.copy2(filepath, DATA_FILE)
                    self.data_manager = DataManager(DATA_FILE)
                    self.apply_window_settings()
                    self.toggle_settings_view() 
                    self.load_tasks_ui()
                    self.update_label_menu()
                    self.update_app_icon()
            except Exception:
                pass 

    def update_app_icon(self):
        tasks = self.data_manager.get_tasks()
        remaining = len([t for t in tasks if not t["completed"]])
        
        s = self.data_manager.data["settings"]
        if s.get("sw_running", False):
            badge_hex = s.get("sw_badge_color", "#28a745")
        else:
            badge_hex = s.get("badge_color", "#DC3545")
            
        badge_rgba = hex_to_rgba(badge_hex)
        
        import sys
        
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)
            
        try:
            img = Image.open(resource_path("base_icon.png")).convert("RGBA")
            img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(img)
        except Exception:
            img = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            draw.ellipse((64, 64, 960, 960), fill=(25, 25, 25, 255), outline=(80, 80, 80, 255), width=24)
            
            draw.line((288, 544, 448, 736), fill="white", width=64)
            draw.line((448, 736, 672, 448), fill="white", width=64)
        
        if remaining > 0 or s.get("sw_running", False):
            # GIANT BADGE covering the entire top right and part of the center
            draw.ellipse((400, 16, 1008, 624), fill=badge_rgba) 
            
            if remaining > 0:
                font_paths = [
                    "C:\\Windows\\Fonts\\arialbd.ttf",
                    "C:\\Windows\\Fonts\\arial.ttf",
                    "C:\\Windows\\Fonts\\segoeuib.ttf",
                    "C:\\Windows\\Fonts\\segoeui.ttf",
                    "arial.ttf"
                ]
                font = None
                for fp in font_paths:
                    if os.path.exists(fp):
                        try:
                            font = ImageFont.truetype(fp, 480) # MASSIVE FONT SIZE
                            break
                        except:
                            pass
                
                if font is None:
                    try:
                        font = ImageFont.truetype("arialbd.ttf", 480)
                    except:
                        font = ImageFont.load_default()
                    
                text = str(remaining) if remaining < 10 else "9+"
                
                # The exact center of the new giant badge
                draw.text((704, 320), text, font=font, fill="white", anchor="mm")
            
        sizes = [128, 64, 48, 32, 24, 16]
        img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
        append_imgs = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
        
        img_256.save(self.temp_icon_path, format="ICO", append_images=append_imgs)
        
        try:
            self.wm_iconbitmap(self.temp_icon_path) 
            
            import ctypes
            
            LR_LOADFROMFILE = 0x0010
            IMAGE_ICON = 1
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            
            SM_CXSMICON = 49
            SM_CYSMICON = 50
            SM_CXICON = 11
            SM_CYICON = 12
            
            # Use GA_ROOT to get the true top-level window handle in Tkinter
            hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2)
            
            cx_small = ctypes.windll.user32.GetSystemMetrics(SM_CXSMICON)
            cy_small = ctypes.windll.user32.GetSystemMetrics(SM_CYSMICON)
            cx_big = ctypes.windll.user32.GetSystemMetrics(SM_CXICON)
            cy_big = ctypes.windll.user32.GetSystemMetrics(SM_CYICON)
            
            hicon_small = ctypes.windll.user32.LoadImageW(None, self.temp_icon_path, IMAGE_ICON, cx_small, cy_small, LR_LOADFROMFILE)
            hicon_big = ctypes.windll.user32.LoadImageW(None, self.temp_icon_path, IMAGE_ICON, cx_big, cy_big, LR_LOADFROMFILE)
            
            if hicon_small:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            if hicon_big:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                
            # Use ITaskbarList3 COM Interface for Pinned Taskbar Overlay Badges
            if remaining > 0 or s.get("sw_running", False):
                badge_img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
                badge_draw = ImageDraw.Draw(badge_img)
                badge_draw.ellipse((0, 0, 256, 256), fill=badge_rgba)
                
                if remaining > 0:
                    b_font = None
                    b_font_paths = [
                        "C:\\Windows\\Fonts\\arialbd.ttf",
                        "C:\\Windows\\Fonts\\arial.ttf",
                        "C:\\Windows\\Fonts\\segoeuib.ttf",
                        "C:\\Windows\\Fonts\\segoeui.ttf"
                    ]
                    for fp in b_font_paths:
                        if os.path.exists(fp):
                            try: b_font = ImageFont.truetype(fp, 180); break
                            except: pass
                    if not b_font: b_font = ImageFont.load_default()
                    
                    badge_draw.text((128, 128), text, font=b_font, fill="white", anchor="mm")
                    
                overlay_path = os.path.join(os.environ.get('TEMP', application_path), "todo_overlay.ico")
                badge_img.save(overlay_path, format="ICO", sizes=[(16, 16)])
                self.set_taskbar_overlay(hwnd, overlay_path, text if remaining > 0 else "")
            else:
                self.set_taskbar_overlay(hwnd, None, "")
                
        except Exception:
            pass

    def set_taskbar_overlay(self, hwnd, icon_path, description=""):
        try:
            from comtypes import IUnknown, GUID, COMMETHOD, HRESULT
            from ctypes import c_void_p, c_uint, c_wchar_p
            from ctypes.wintypes import HWND, BOOL, HICON
            
            class ITaskbarList3(IUnknown):
                _iid_ = GUID('{ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}')
                _methods_ = [
                    COMMETHOD([], HRESULT, 'HrInit'),
                    COMMETHOD([], HRESULT, 'AddTab', (['in'], HWND, 'hwnd')),
                    COMMETHOD([], HRESULT, 'DeleteTab', (['in'], HWND, 'hwnd')),
                    COMMETHOD([], HRESULT, 'ActivateTab', (['in'], HWND, 'hwnd')),
                    COMMETHOD([], HRESULT, 'SetActiveAlt', (['in'], HWND, 'hwnd')),
                    COMMETHOD([], HRESULT, 'MarkFullscreenWindow', (['in'], HWND, 'hwnd'), (['in'], BOOL, 'fFullscreen')),
                    COMMETHOD([], HRESULT, 'SetProgressValue', (['in'], HWND, 'hwnd'), (['in'], c_uint, 'ullCompleted'), (['in'], c_uint, 'ullTotal')),
                    COMMETHOD([], HRESULT, 'SetProgressState', (['in'], HWND, 'hwnd'), (['in'], c_uint, 'tbpFlags')),
                    COMMETHOD([], HRESULT, 'RegisterTab', (['in'], HWND, 'hwndTab'), (['in'], HWND, 'hwndMDI')),
                    COMMETHOD([], HRESULT, 'UnregisterTab', (['in'], HWND, 'hwndTab')),
                    COMMETHOD([], HRESULT, 'SetTabOrder', (['in'], HWND, 'hwndTab'), (['in'], HWND, 'hwndInsertBefore')),
                    COMMETHOD([], HRESULT, 'SetTabActive', (['in'], HWND, 'hwndTab'), (['in'], HWND, 'hwndMDI'), (['in'], c_uint, 'dwReserved')),
                    COMMETHOD([], HRESULT, 'ThumbBarAddButtons', (['in'], HWND, 'hwnd'), (['in'], c_uint, 'cButtons'), (['in'], c_void_p, 'pButton')),
                    COMMETHOD([], HRESULT, 'ThumbBarUpdateButtons', (['in'], HWND, 'hwnd'), (['in'], c_uint, 'cButtons'), (['in'], c_void_p, 'pButton')),
                    COMMETHOD([], HRESULT, 'ThumbBarSetImageList', (['in'], HWND, 'hwnd'), (['in'], c_void_p, 'himl')),
                    COMMETHOD([], HRESULT, 'SetOverlayIcon', (['in'], HWND, 'hwnd'), (['in'], HICON, 'hIcon'), (['in'], c_wchar_p, 'pszDescription')),
                ]
            
            import comtypes.client
            CLSID_TaskbarList = GUID('{56FDF344-FD6D-11d0-958A-006097C9A090}')
            taskbar = comtypes.client.CreateObject(CLSID_TaskbarList, interface=ITaskbarList3)
            taskbar.HrInit()
            
            import ctypes
            LR_LOADFROMFILE = 0x0010
            IMAGE_ICON = 1
            hicon = ctypes.windll.user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE) if icon_path else 0
            
            # Force Windows to register the window in the taskbar before setting the overlay!
            # If DWM lags, SetOverlayIcon fails. AddTab guarantees it is registered.
            taskbar.AddTab(hwnd)
            taskbar.SetOverlayIcon(hwnd, hicon, description)
        except Exception as e:
            print("Taskbar COM Error:", e)


    def toggle_quadrant(self, q_id):
        s = self.data_manager.data["settings"]
        is_expanded = s.get(f"{q_id}_expanded", True)
        s[f"{q_id}_expanded"] = not is_expanded
        self.data_manager.save_data()
        self.load_tasks_ui()

    def toggle_repeated(self, task_id):
        self.data_manager.toggle_repeated(task_id)
        self.load_tasks_ui()


    def load_tasks_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tasks = self.data_manager.get_tasks()
        quadrants_config = self.data_manager.data["quadrants"]
        settings = self.data_manager.data["settings"]
        
        row_idx = 0

        for q_id, q_data in quadrants_config.items():
            if settings.get("zen_mode", False) and q_id in ["q3", "q4"]:
                continue

            is_expanded = settings.get(f"{q_id}_expanded", True)
            
            # Header Frame (Black UI)
            header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#0a0a0a", corner_radius=5)
            header_frame.grid(row=row_idx, column=0, sticky="ew", pady=(10, 2))
            header_frame.grid_columnconfigure(0, weight=1)
            
            q_tasks_temp = [t for t in tasks if t.get("quadrant") == q_id]
            has_pending = any(not t["completed"] for t in q_tasks_temp)
            indicator = " 🔔" if has_pending else ""
            
            header_btn = ctk.CTkButton(
                header_frame, 
                text=f"{'▼' if is_expanded else '▶'} {q_data['emoji']} {q_data['name']}{indicator}",
                fg_color="transparent", text_color="#DDDDDD", font=("Segoe UI", 16, "bold"),
                hover_color="#1a1a1a", anchor="w",
                command=lambda q=q_id: self.toggle_quadrant(q)
            )
            header_btn.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            row_idx += 1
            
            if not is_expanded:
                continue
                
            # Tasks for this quadrant
            q_tasks = [t for t in tasks if t.get("quadrant") == q_id]
            q_tasks_sorted = sorted(q_tasks, key=lambda t: t["completed"])
            
            for task in q_tasks_sorted:
                color = q_data["color"]
                border_col = color if not task["completed"] else "#333333"
                
                task_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#121212", corner_radius=8, border_width=1, border_color=border_col)
                task_frame.grid(row=row_idx, column=0, sticky="ew", pady=4, padx=(10,0))
                task_frame.grid_columnconfigure(1, weight=1)
                
                checkbox = ctk.CTkCheckBox(
                    task_frame, text="", width=24, checkbox_height=22, checkbox_width=22,
                    fg_color="#28a745", hover_color="#218838", border_color="#444444",
                    command=lambda t_id=task["id"]: self.toggle_task(t_id)
                )
                if task["completed"]:
                    checkbox.select()
                checkbox.grid(row=0, column=0, padx=(12, 10), pady=12)
                
                text_color = "#555555" if task["completed"] else color
                font = ("Segoe UI", 16, "overstrike") if task["completed"] else ("Segoe UI", 16)
                
                label = ctk.CTkLabel(task_frame, text=task["text"], font=font, text_color=text_color, anchor="w")
                label.grid(row=0, column=1, sticky="ew")
                
                # Double click to edit
                label.bind("<Double-Button-1>", lambda e, lbl=label, t_id=task["id"], txt=task["text"]: self.start_edit_task(lbl, t_id, txt))

                # Hover-only up/down buttons (invisible until hovered)
                hidden_color = "#121212"
                visible_color = "#AAAAAA"
                
                up_btn = ctk.CTkButton(
                    task_frame, text="▲", width=25, height=30, fg_color="transparent", 
                    hover_color="#333333", text_color=hidden_color, font=("Arial", 12),
                    command=lambda t_id=task["id"]: self.move_task(t_id, -1)
                )
                up_btn.grid(row=0, column=2, padx=(0, 2))
                
                down_btn = ctk.CTkButton(
                    task_frame, text="▼", width=25, height=30, fg_color="transparent", 
                    hover_color="#333333", text_color=hidden_color, font=("Arial", 12),
                    command=lambda t_id=task["id"]: self.move_task(t_id, 1)
                )
                down_btn.grid(row=0, column=3, padx=(0, 5))

                def on_enter(e, u=up_btn, d=down_btn):
                    u.configure(text_color=visible_color)
                    d.configure(text_color=visible_color)

                def on_leave(e, u=up_btn, d=down_btn):
                    u.configure(text_color=hidden_color)
                    d.configure(text_color=hidden_color)

                # Bind hover events to the entire row
                for widget in [task_frame, label, checkbox, up_btn, down_btn]:
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)

                is_rep = task.get("is_repeated", False)
                rep_btn = ctk.CTkButton(
                    task_frame, text="🔂", width=30, height=30, fg_color="transparent", 
                    hover_color="#333333", text_color="#00FFCC" if is_rep else "#444444", font=("Segoe UI", 18),
                    command=lambda t_id=task["id"]: self.toggle_repeated(t_id)
                )
                rep_btn.grid(row=0, column=4, padx=(5, 5))
                
                del_btn = ctk.CTkButton(
                    task_frame, text="✕", width=30, height=30, fg_color="transparent", 
                    hover_color="#331111", text_color="#FF4444", font=("Arial", 16),
                    command=lambda t_id=task["id"]: self.delete_task(t_id)
                )
                del_btn.grid(row=0, column=5, padx=(0, 10))
                
                row_idx += 1


    def start_edit_task(self, label, task_id, current_text):
        label.grid_forget()
        entry = ctk.CTkEntry(label.master, font=("Segoe UI", 16))
        entry.insert(0, current_text)
        entry.grid(row=0, column=1, sticky="ew", padx=5)
        entry.focus()
        
        def save_edit(event=None):
            new_text = entry.get().strip()
            if new_text and new_text != current_text:
                self.data_manager.update_task_text(task_id, new_text)
            self.load_tasks_ui()
            
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)

    def add_task(self):
        text = self.entry_task.get().strip()
        if text:
            import re
            match = re.match(r"^:q([1-4]):\s*(.*)", text, re.IGNORECASE)
            if match:
                selected_id = f"q{match.group(1)}"
                text = match.group(2).strip()
            else:
                selected_str = self.label_menu.get()
                quadrants = self.data_manager.data["quadrants"]
                selected_id = "q4"
                for k, v in quadrants.items():
                    if f"{v['emoji']} {v['name'].split(':')[0]}" == selected_str:
                        selected_id = k
                        break
            
            if not text:
                return


            self.data_manager.add_task(text, selected_id)
            
            # PLAY SOUND ON ADD
            if self.data_manager.data["settings"].get("sound_effects", True):
                try:
                    import winsound
                    winsound.PlaySound("SystemDefault", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except:
                    pass
                    
            self.entry_task.delete(0, ctk.END)
            
            # Ensure the quadrant is expanded when a task is added
            self.data_manager.data["settings"][f"{selected_id}_expanded"] = True
            self.data_manager.save_data()
            
            self.load_tasks_ui()
            self.update_app_icon()

    def toggle_task(self, task_id):
        task = next((t for t in self.data_manager.data["tasks"] if t["id"] == task_id), None)
        was_completed = task["completed"] if task else False
        
        self.data_manager.toggle_task(task_id)
        
        if not was_completed and self.data_manager.data["settings"].get("sound_effects", True):
            try:
                import winsound
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except:
                pass
                
        self.load_tasks_ui()
        self.update_app_icon()
        if self.current_view == "settings":
            self.refresh_stats()

    def delete_task(self, task_id):
        self.data_manager.delete_task(task_id)
        self.load_tasks_ui()
        self.update_app_icon()

    def move_task(self, task_id, direction):
        self.data_manager.move_task(task_id, direction)
        self.load_tasks_ui()

    def save_settings(self):
        s = self.data_manager.data["settings"]
        
        s["sound_effects"] = self.sound_var.get()
        s["always_on_top"] = self.always_top_var.get()
        
        try:
            s["heartbeat_mins"] = int(self.hb_entry.get())
        except ValueError:
            pass
            
        s["day_start"] = self.start_entry.get()
        s["day_end"] = self.end_entry.get()
        
        bg = self.bg_color_entry.get().strip()
        if not bg.startswith('#'): bg = '#' + bg
        
        badge = self.badge_color_entry.get().strip()
        if not badge.startswith('#'): badge = '#' + badge
        
        sw_badge = self.sw_badge_color_entry.get().strip()
        if not sw_badge.startswith('#'): sw_badge = '#' + sw_badge
        
        s["app_bg_color"] = bg
        s["badge_color"] = badge
        s["sw_badge_color"] = sw_badge
        s["global_hotkey"] = self.hotkey_entry.get().strip()
        s["sw_hotkey"] = self.sw_hotkey_entry.get().strip()
        s["mini_hotkey"] = self.mini_hotkey_entry.get().strip()
        
        self.setup_global_hotkey()
        
        try:
            s["window_width"] = int(self.width_entry.get())
            s["window_height"] = int(self.height_entry.get())
            s["mini_window_width"] = int(self.mini_width_entry.get())
            s["mini_window_height"] = int(self.mini_height_entry.get())
            s["mini_transparency"] = float(self.mini_alpha_entry.get())
            s["oled_shift_sec"] = int(self.oled_shift_entry.get())
            
            oled_col = self.oled_color_entry.get().strip()
            if not oled_col.startswith('#'): oled_col = '#' + oled_col
            s["oled_text_color"] = oled_col
            if hasattr(self, 'mini_lbl_sw_time'):
                self.mini_lbl_sw_time.configure(text_color=oled_col)
        except ValueError:
            pass 
            
        # PRO FEATURES: Save Custom Quadrants
        for lbl_key, entries in self.label_entries.items():
            col = entries["color"].get().strip()
            if not col.startswith('#'): col = '#' + col
            
            self.data_manager.data["quadrants"][lbl_key] = {
                "emoji": entries["emoji"].get().strip(),
                "name": entries["name"].get().strip(),
                "color": col
            }
            
        self.data_manager.save_data()
        
        self.apply_window_settings()
        self.update_label_menu()
        self.load_tasks_ui()
        self.update_app_icon()
        
        self.toggle_settings_view()

if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()

