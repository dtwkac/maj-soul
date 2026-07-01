import ctypes
import winsound
import time
import os
import tkinter as tk
from consts import DEBUG, SLEEP_INTERVAL

paused = False

def alarm(msg):
    winsound.Beep(660, 200)
    winsound.Beep(660, 200)
    winsound.Beep(660, 200)
    winsound.Beep(660, 200)
    winsound.Beep(660, 200)
    time.sleep(0.3)
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
    ret = ctypes.windll.user32.MessageBoxW(0, msg, "报警", 1)
    if ret != 1:
        os._exit(0)

def pause_dialog():
    global paused
    paused = True
    ret = ctypes.windll.user32.MessageBoxW(0, "已暂停，点击确定继续运行，取消退出程序", "暂停", 1)
    paused = False
    if ret != 1:
        os._exit(0)

def setup_debug_window():
    root = tk.Tk()
    root.title("雀魂检测")
    root.attributes('-topmost', True)
    root.resizable(False, False)
    root.configure(bg='#ffffff')

    frame = tk.Frame(root, bg='#ffffff', padx=14, pady=8)
    frame.pack(fill=tk.BOTH)

    tk.Label(frame, text="检测调试", font=('', 11, 'bold'), bg='#ffffff', fg='#3366cc').pack(anchor=tk.W)
    tk.Frame(frame, height=2, bg='#3366cc').pack(fill=tk.X, pady=(4, 6))
    lbl_score = tk.Label(frame, text="分数: ---", font=('Consolas', 16, 'bold'), bg='#ffffff', fg='#333')
    lbl_score.pack(anchor=tk.W)
    lbl_action = tk.Label(frame, text="等待中...", font=('Consolas', 16, 'bold'), bg='#ffffff', fg='#888')
    lbl_action.pack(anchor=tk.W)

    root.update()
    root.geometry("260x150+0+0")
    root.update()
    off_x = frame.winfo_rootx()
    off_y = frame.winfo_rooty()
    new_x = 550 - off_x - root.winfo_width()
    new_y = 770 - off_y - root.winfo_height()
    root.geometry(f"+{new_x}+{new_y}")

    return root, lbl_score, lbl_action
