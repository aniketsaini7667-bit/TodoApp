# FocusTodo Pro 🎯

FocusTodo Pro is a professional, feature-rich desktop task management application designed to maximize your productivity using the Eisenhower Matrix, integrated time-tracking, and advanced daily accountability features.

Built with performance in mind, FocusTodo runs natively on Windows, offering a stunning dark-mode interface and an OLED-friendly floating mini-timer.

---

## ✨ Core Features

- **Eisenhower Matrix Task Management**: Categorize your tasks to prioritize effectively:
  - **Q1: Urgent & Important** 🔥 (Do First)
  - **Q2: Not Urgent, Important** 🚀 (Schedule)
  - **Q3: Urgent, Not Important** 🗣️ (Delegate)
  - **Q4: Not Urgent, Not Important** 🗑️ (Don't Do)
- **Floating Mini-Timer**: Switch to a minimal, draggable, always-on-top floating timer widget to track time without cluttering your screen.
- **Smart Automation**: 
  - **Midnight Auto-Reset**: Automatically archives completed tasks at the end of the day.
  - **Auto-Demotion**: Tasks lingering in Q1 for more than 48 hours are automatically demoted to Q3 to keep your priorities realistic.
- **Advanced Analytics**: Visualize your productivity with a built-in heatmap and lifetime completed-task trackers.
- **Global Hotkeys**: Control the app from anywhere on your PC:
  - Alt + X : Start/Stop Timer
  - Alt + Z : Toggle Mini-Timer Mode
  - Alt + A : Show/Hide the entire Application
- **Quick-Add Syntax**: Type :q1: Buy groceries in the input box to instantly route the task into Quadrant 1!
- **Data Security**: Your data never touches the cloud. All tasks are saved securely on your local hard drive in the Windows AppData folder.

---

## 🚀 How to Install & Use (End Users)

FocusTodo Pro uses a professional installer so you don't need to mess with command lines or Python installations.

1. **Download**: Go to the **[Releases](../../releases)** tab on the right side of this GitHub page and download FocusTodo_Installer.exe.
2. **Install**: Double-click the installer. It will safely extract the application without requiring Administrator privileges.
3. **Launch**: Double-click the new FocusTodo icon on your Desktop or search for it in the Windows Start Menu!
4. **Conquer Your Day**: Add tasks, track your time, and watch your productivity stats soar.

---

## 💻 How to Build from Source (Developers)

If you want to modify the code and compile your own executable, follow these instructions:

### 1. Requirements
* Python 3.12+
* GCC Compiler (MinGW64)
* Inno Setup 6 (for packaging)

### 2. Setup
Clone the repository and install the required dependencies:
``bash
pip install customtkinter pillow nuitka zstandard
``

### 3. Compile the Executable (Nuitka)
We use Nuitka to translate the Python code into highly optimized C code. 
*(Make sure to rename main.py to FocusTodo.py before compiling so the executable gets the correct name).*
``bash
python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=tk-inter --windows-icon-from-ico=base_icon.ico --include-data-file=base_icon.png=base_icon.png --include-data-file=base_icon.ico=base_icon.ico FocusTodo.py
``

### 4. Create the Installer (Inno Setup)
Once Nuitka finishes compiling into the FocusTodo.dist folder, open installer_script.iss with Inno Setup and click **Compile**. This will generate the final, distributable FocusTodo_Installer.exe.

---
*Built for extreme focus. No subscriptions, no cloud sync, just you and your goals.*
