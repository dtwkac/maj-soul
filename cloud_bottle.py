import pyautogui
import keyboard
import time
from consts import CENTER, TSUMO_BTN

paused = True

def toggle():
    global paused
    paused = not paused
    if paused:
        pyautogui.moveTo(*TSUMO_BTN)
    print("已暂停" if paused else "继续运行")

keyboard.add_hotkey('w', toggle)
print("连点器启动，已暂停。按 w 开始/暂停，Ctrl+C 退出")

try:
    while True:
        if not paused:
            pyautogui.click(*CENTER)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n已停止")
