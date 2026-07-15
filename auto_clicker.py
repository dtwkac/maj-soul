import pyautogui
import keyboard
import time
import relaunch
import winsound
import cv2
from consts import RELAUNCH_CONTINUE_REGION, RELAUNCH_CONTINUE_CLICK
import ui

pyautogui.PAUSE = 0

X, Y = 1200, 815
INTERVAL = 0.2
RESTART_INTERVAL = 3600
TILE_REGION = (1385, 885, 90, 140)
PRECOND_REGION = (1415, 885, 30, 20)
_PRECOND_TEMPLATE1 = cv2.imread('pics/pre1.png', cv2.IMREAD_GRAYSCALE)
_PRECOND_TEMPLATE2 = cv2.imread('pics/pre2.png', cv2.IMREAD_GRAYSCALE)

relaunch.RELAUNCH_QYZZ_REGION = (1635, 720, 110, 100)
relaunch.RELAUNCH_QYZZ_CLICK = (1695, 775)

_orig_play = winsound.PlaySound

paused = False

def toggle_pause():
    global paused
    paused = not paused
    print("已暂停" if paused else "继续运行")

def do_restart():
    winsound.PlaySound = lambda *a, **k: None
    try:
        relaunch.RESTART_COUNT += 1
        relaunch.LAST_RESTART = time.strftime('%H:%M:%S')
        print(f"[{relaunch.LAST_RESTART}] 触发重启")
        pyautogui.click(365, 25)
        time.sleep(1)
        pyautogui.click(310, 30)
        time.sleep(1)
        pyautogui.click(40, 120)
        time.sleep(1)
        pyautogui.click(85, 290)
        time.sleep(30)
        if not relaunch._wait_any(relaunch.RELAUNCH_QYZZ_REGION, [relaunch._QYZZ1, relaunch._QYZZ2], "qyzz", relaunch.RELAUNCH_QYZZ_CLICK):
            ui.alarm("重启失败: qyzz 超限")
            return
        pyautogui.click(105, 25)
        time.sleep(1)
        if not relaunch._wait(RELAUNCH_CONTINUE_REGION, relaunch._CONTINUE, "continue", RELAUNCH_CONTINUE_CLICK):
            ui.alarm("重启失败: continue 超限")
            return
        if not relaunch._wait_any(PRECOND_REGION, [_PRECOND_TEMPLATE1, _PRECOND_TEMPLATE2], "先决条件"):
            ui.alarm("重启失败: 先决条件超限")
            return
        print(f"[{time.strftime('%H:%M:%S')}] 重启完成，继续连点")
    finally:
        winsound.PlaySound = _orig_play

keyboard.add_hotkey('ctrl+.', toggle_pause)

print(f"连点器启动: ({X}, {Y}), 间隔 {INTERVAL}s, 重启间隔 {RESTART_INTERVAL}s")
print("按 Ctrl+. 暂停/继续, Ctrl+C 退出")

do_restart()
CENTER = (960, 540)

try:
    while True:
        for _ in range(int(RESTART_INTERVAL / INTERVAL)):
            if not paused:
                pyautogui.moveTo(*CENTER)
                pyautogui.click(X, Y)
            time.sleep(INTERVAL)
        print(f"[{time.strftime('%H:%M:%S')}] 已满 {RESTART_INTERVAL}s，执行重启")
        do_restart()
except KeyboardInterrupt:
    print("\n已停止")
