# 无条件自摸连点器，OCR检测卡住自动重启+CE加速
import pyautogui
import keyboard
import time
import random
import sys
from common import relaunch
import winsound
import cv2
import mss
import numpy as np
from common.consts import RELAUNCH_CONTINUE_REGION, CENTER, TSUMO_BTN
from common.speedhack import speedhack, kill_ce
from common import ui

pyautogui.PAUSE = 0

DEBUG = '--debug' in sys.argv

INTERVAL = 0.2
DETECT_INTERVAL = 2
PRECOND_REGION = (1415, 885, 30, 20)
_PRECOND_TEMPLATE1 = cv2.imread('pics/pre1.png', cv2.IMREAD_GRAYSCALE)
_PRECOND_TEMPLATE2 = cv2.imread('pics/pre2.png', cv2.IMREAD_GRAYSCALE)
# 卡住检测区域
_CHECK_REGION = {"left": 1005, "top": 735, "width": 115, "height": 80}
SIMILARITY_THRESHOLD = 0.99
STUCK_LIMIT = 8

_sct = mss.MSS()

_orig_play = winsound.PlaySound

paused = False

def toggle_pause():
    global paused
    paused = not paused
    print(f"[{time.strftime('%H:%M:%S')}] 已暂停" if paused else f"[{time.strftime('%H:%M:%S')}] 继续运行")

def do_restart():
    winsound.PlaySound = lambda *a, **k: None
    try:
        kill_ce()
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
        if not relaunch._wait_for_match_multi(relaunch.RELAUNCH_QYZZ_REGION, [relaunch._QYZZ1, relaunch._QYZZ2], "qyzz", True):
            print(f"[{time.strftime('%H:%M:%S')}] 重启失败: qyzz 超限")
            return False
        pyautogui.click(105, 25)
        if not relaunch._wait_for_match(RELAUNCH_CONTINUE_REGION, relaunch._CONTINUE, "continue", True):
            print(f"[{time.strftime('%H:%M:%S')}] 重启失败: continue 超限")
            return False
        if not relaunch._wait_for_match_multi(PRECOND_REGION, [_PRECOND_TEMPLATE1, _PRECOND_TEMPLATE2], "先决条件", False):
            print(f"[{time.strftime('%H:%M:%S')}] 重启失败: 先决条件超限")
            return False
        print(f"[{time.strftime('%H:%M:%S')}] 重启完成")
        pyautogui.moveTo(*CENTER)
        return True
    finally:
        winsound.PlaySound = _orig_play

def restart_with_speedhack():
    while True:
        if do_restart():
            if speedhack():
                break

keyboard.add_hotkey('ctrl+.', toggle_pause)

print(f"[{time.strftime('%H:%M:%S')}] 连点器启动，按 Ctrl+. 暂停/继续，Ctrl+C 退出")

restart_with_speedhack()

prev_check = None
same_count = 0
try:
    last_detect = 0
    while True:
        if not paused:
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            pyautogui.click(TSUMO_BTN[0] + dx, TSUMO_BTN[1] + dy)
        now = time.time()
        if not paused and now - last_detect >= DETECT_INTERVAL:
            last_detect = now
            curr_check = cv2.cvtColor(np.asarray(_sct.grab(_CHECK_REGION)), cv2.COLOR_BGRA2GRAY)
            if prev_check is not None:
                result = cv2.matchTemplate(prev_check, curr_check, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val >= SIMILARITY_THRESHOLD:
                    same_count += 1
                else:
                    same_count = 0
                if DEBUG:
                    print(f"  卡住检测 same_count={same_count}/{STUCK_LIMIT} 匹配度{max_val:.3f}")
                if same_count >= 5:
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    time.sleep(1)
                if same_count >= STUCK_LIMIT:
                    print(f"[{time.strftime('%H:%M:%S')}] 连续{STUCK_LIMIT}次画面相同，确认卡住")
                    restart_with_speedhack()
                    prev_check = None
                    same_count = 0
            prev_check = curr_check
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print(f"[{time.strftime('%H:%M:%S')}] 已停止")
