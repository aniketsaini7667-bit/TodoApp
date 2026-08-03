from todo_app import TodoApp

try:
    from ctypes import windll
    import ctypes
    windll.shcore.SetProcessDpiAwareness(1)
    myappid = 'aniket.todoapp.pro.2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

if __name__ == '__main__':
    app = TodoApp()
    app.mainloop()

