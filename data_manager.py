import os
import json
import datetime
import sys
import time

# PRO FIX: Ensure data.json saves exactly where the .exe is located!
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(application_path, "data.json")

DEFAULT_DATA = {
    "settings": {
        "heartbeat_mins": 10,
        "day_start": "08:00",
        "day_end": "23:59",
        "total_completed": 0,
        "last_reset_date": str(datetime.date.today()),
        "install_date": str(datetime.date.today()),
        "app_bg_color": "#000000",
        "badge_color": "#DC3545",
        "window_width": 450,
        "window_height": 650,
        "sound_effects": True,
        "sw_running": False,
        "sw_start": 0.0,
        "sw_elapsed": 0.0,
        "sw_all_time": 0.0,
        "sw_last_recorded": 0.0,
        "sw_hotkey": "alt+x",
        "sw_badge_color": "#28a745",
        "mini_hotkey": "alt+z",
        "mini_window_width": 160,
        "mini_window_height": 60,
        "mini_transparency": 0.5,
        "oled_shift_sec": 60,
        "q1_expanded": True,
        "q2_expanded": True,
        "q3_expanded": True,
        "q4_expanded": True
    },
    "quadrants": {
        "q1": {"name": "Q1: Urgent & Important", "color": "#ef4444", "emoji": "🔥"},
        "q2": {"name": "Q2: Not Urgent, Important", "color": "#28a745", "emoji": "🚀"},
        "q3": {"name": "Q3: Urgent, Not Important", "color": "#f97316", "emoji": "🗣️"},
        "q4": {"name": "Q4: Not Urgent, Not Important", "color": "#6c757d", "emoji": "🗑️"}
    },
    "tasks": [],
    "history": {}
}

class DataManager:
    def __init__(self, filename):
        self.filename = filename
        self.data = self.load_data()
        self.migrate_data()
        self.check_day_end_reset()

    def migrate_data(self):
        # Migrate labels to quadrants
        if "labels" in self.data:
            old_labels = self.data.pop("labels")
            self.data["quadrants"] = DEFAULT_DATA["quadrants"].copy()
            
            # Map old tasks to new quadrants and repeated flag
            for task in self.data.get("tasks", []):
                old_label = task.get("label", "label_1")
                task["is_repeated"] = (old_label == "label_2") or task.get("is_repeated", False)
                
                if old_label == "label_1":
                    task["quadrant"] = "q1"
                elif old_label == "label_2":
                    task["quadrant"] = "q2" # Repeated tasks default to Q2
                elif old_label == "label_3":
                    task["quadrant"] = "q2"
                elif old_label == "label_4":
                    task["quadrant"] = "q3"
                elif old_label == "label_5":
                    task["quadrant"] = "q1"
                else:
                    task["quadrant"] = task.get("quadrant", "q4")
                    
                if "label" in task:
                    del task["label"]

        if "history" not in self.data:
            self.data["history"] = {}

        if "quadrants" not in self.data:
            self.data["quadrants"] = DEFAULT_DATA["quadrants"].copy()

        for key, val in DEFAULT_DATA["settings"].items():
            if key not in self.data["settings"]:
                self.data["settings"][key] = val
                
        s = self.data["settings"]
        today = datetime.date.today()
        last_act_str = s.get("last_active_date", str(today))
        try:
            last_act = datetime.datetime.strptime(last_act_str, "%Y-%m-%d").date()
            diff = (today - last_act).days
            if diff == 1:
                s["streak"] = s.get("streak", 1) + 1
            elif diff > 1:
                s["streak"] = 1
        except:
            pass
        s["last_active_date"] = str(today)

        for task in self.data["tasks"]:
            if "quadrant" not in task:
                task["quadrant"] = "q4"
            if "is_repeated" not in task:
                task["is_repeated"] = False
                
        self.save_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump(DEFAULT_DATA, f, indent=4)
            return DEFAULT_DATA
        else:
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except Exception:
                return DEFAULT_DATA

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_tasks(self):
        return self.data["tasks"]

    def add_task(self, text, quadrant_id):
        task_id = max([t["id"] for t in self.data["tasks"]] + [0]) + 1
        self.data["tasks"].append({
            "id": task_id, 
            "text": text, 
            "completed": False, 
            "quadrant": quadrant_id,
            "is_repeated": False,
            "added_ts": time.time()
        })
        self.save_data()


    def update_task_text(self, task_id, new_text):
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                task["text"] = new_text
                self.save_data()
                return True
        return False

    def toggle_task(self, task_id):
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                if task["completed"]:
                    self.data["settings"]["total_completed"] += 1
                else:
                    self.data["settings"]["total_completed"] -= 1
        self.save_data()

    def toggle_repeated(self, task_id):
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                task["is_repeated"] = not task.get("is_repeated", False)
                break
        self.save_data()

    def delete_task(self, task_id):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        self.save_data()

    def move_task(self, task_id, direction):
        idx = next((i for i, t in enumerate(self.data["tasks"]) if t["id"] == task_id), -1)
        if idx == -1: return
        my_task = self.data["tasks"][idx]
        my_status = my_task["completed"]
        my_quadrant = my_task["quadrant"]
        
        # Only move within the same quadrant and status
        same_group = [t for t in self.data["tasks"] if t["completed"] == my_status and t["quadrant"] == my_quadrant]
        sub_idx = next(i for i, t in enumerate(same_group) if t["id"] == task_id)
        target_sub_idx = sub_idx + direction
        
        if 0 <= target_sub_idx < len(same_group):
            target_task = same_group[target_sub_idx]
            target_idx = next(i for i, t in enumerate(self.data["tasks"]) if t["id"] == target_task["id"])
            self.data["tasks"][idx], self.data["tasks"][target_idx] = self.data["tasks"][target_idx], self.data["tasks"][idx]
            self.save_data()

    def check_day_end_reset(self):
        now = datetime.datetime.now()
        
        try:
            end_hour, end_minute = map(int, self.data["settings"]["day_end"].split(":"))
            end_time = datetime.time(end_hour, end_minute)
        except:
            end_time = datetime.time(23, 59)
            
        last_reset_ts = self.data["settings"].get("last_reset_ts", now.timestamp())
        
        today_reset_dt = datetime.datetime.combine(now.date(), end_time)
        if now >= today_reset_dt:
            last_barrier = today_reset_dt
        else:
            last_barrier = today_reset_dt - datetime.timedelta(days=1)
            
        if "last_reset_ts" not in self.data["settings"]:
            self.data["settings"]["last_reset_ts"] = now.timestamp()
            self.save_data()
            return
            
        if last_reset_ts < last_barrier.timestamp():
            self._clear_completed()
            
            s = self.data["settings"]
            if s.get("sw_running", False):
                current_time = time.time()
                elapsed = (current_time - s.get("sw_start", 0)) * 1000
                delta = max(0, elapsed - s.get("sw_last_recorded", 0))
                s["sw_all_time"] = s.get("sw_all_time", 0) + delta
            elif s.get("sw_elapsed", 0) > 0:
                delta = max(0, s.get("sw_elapsed", 0) - s.get("sw_last_recorded", 0))
                s["sw_all_time"] = s.get("sw_all_time", 0) + delta
                
            s["sw_running"] = False
            s["sw_elapsed"] = 0.0
            s["sw_start"] = 0.0
            s["sw_last_recorded"] = 0.0
            
            self.data["settings"]["last_reset_ts"] = now.timestamp()
            
        # PRO FIX: Auto-Demotion for Q1 tasks older than 48 hours
        now_ts = time.time()
        for t in self.data["tasks"]:
            if t.get("quadrant") == "q1" and not t.get("completed"):
                added = t.get("added_ts")
                if added and (now_ts - added) > 48 * 3600:
                    t["quadrant"] = "q3"
                    
        self.save_data()

    def _clear_completed(self):
        today_str = str(datetime.date.today())
        completed_counts = {"q1": 0, "q2": 0, "q3": 0, "q4": 0}
        for t in self.data["tasks"]:
            if t["completed"] and t.get("quadrant"):
                q_id = t["quadrant"]
                if q_id in completed_counts:
                    completed_counts[q_id] += 1
        
        self.data["history"][today_str] = completed_counts

        new_tasks = []
        for t in self.data["tasks"]:
            if not t["completed"]:
                new_tasks.append(t)
            elif t.get("is_repeated", False):
                t["completed"] = False
                new_tasks.append(t)
        self.data["tasks"] = new_tasks
