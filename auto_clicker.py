import pyautogui
import keyboard
import time
import random
import sys
import relaunch
import winsound
import cv2
import mss
import numpy as np
import pytesseract
from consts import RELAUNCH_CONTINUE_REGION, RELAUNCH_CONTINUE_CLICK, CENTER, PRECONDITION_THRESHOLD
from speedhack import speedhack, kill_ce
import ui

pyautogui.PAUSE = 0

DEBUG = '--debug' in sys.argv

TSUMO_BTN = (1200, 815)
INTERVAL = 0.2
DETECT_INTERVAL = 5
_DETECT_REGION = {"left": 1470, "top": 630, "width": 30, "height": 12}
PRECOND_REGION = (1415, 885, 30, 20)
_PRECOND_TEMPLATE1 = cv2.imread('pics/pre1.png', cv2.IMREAD_GRAYSCALE)
_PRECOND_TEMPLATE2 = cv2.imread('pics/pre2.png', cv2.IMREAD_GRAYSCALE)
_CHECK_REGION = {"left": 830, "top": 450, "width": 195, "height": 150}

_sct = mss.MSS()

relaunch.RELAUNCH_QYZZ_REGION = (1635, 720, 110, 100)
relaunch.RELAUNCH_QYZZ_CLICK = (1695, 775)

_orig_play = winsound.PlaySound

paused = False

def toggle_pause():
    global paused
    paused = not paused
    print(f"[{time.strftime('%H:%M:%S')}] 已暂停" if paused else f"[{time.strftime('%H:%M:%S')}] 继续运行")

def detect_round_value():
    img = np.asarray(_sct.grab(_DETECT_REGION))
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    big = cv2.resize(gray, None, fx=16, fy=16, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(big)
    _, bw = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(bw, config='--psm 7 -c tessedit_char_whitelist=0123456789').strip()
    return text if text else None

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
        if not relaunch._wait_any(relaunch.RELAUNCH_QYZZ_REGION, [relaunch._QYZZ1, relaunch._QYZZ2], "qyzz", relaunch.RELAUNCH_QYZZ_CLICK):
            print(f"[{time.strftime('%H:%M:%S')}] 重启失败: qyzz 超限")
            return False
        pyautogui.click(105, 25)
        if not relaunch._wait(RELAUNCH_CONTINUE_REGION, relaunch._CONTINUE, "continue", RELAUNCH_CONTINUE_CLICK):
            print(f"[{time.strftime('%H:%M:%S')}] 重启失败: continue 超限")
            return False
        if not relaunch._wait_any(PRECOND_REGION, [_PRECOND_TEMPLATE1, _PRECOND_TEMPLATE2], "先决条件"):
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

if DEBUG:
    print(f"连点器启动: {TSUMO_BTN}, 点击间隔 {INTERVAL}s, 回合数卡住检测间隔 {DETECT_INTERVAL}s")
print("按 Ctrl+. 暂停/继续, Ctrl+C 退出")

restart_with_speedhack()

prev_rounds = None
prev_check = None
same_count = 0
check_count = 0
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
            rounds = detect_round_value()
            curr_check = cv2.cvtColor(np.asarray(_sct.grab(_CHECK_REGION)), cv2.COLOR_BGRA2GRAY)
            if DEBUG:
                print(f"  回合数: {rounds}")
            if rounds == prev_rounds:
                same_count += 1
                if same_count >= 1 and prev_check is not None:
                    result = cv2.matchTemplate(prev_check, curr_check, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)
                    if max_val >= PRECONDITION_THRESHOLD:
                        check_count += 1
                    else:
                        check_count = 0
                    if DEBUG:
                        print(f"  回合{rounds} 相同{same_count+1}次 check{check_count}/3 匹配度{max_val:.3f}")
                    if check_count >= 3:
                        print(f"[{time.strftime('%H:%M:%S')}] 连续3次check确认卡住(回合{rounds})")
                        restart_with_speedhack()
                        prev_rounds = None
                        prev_check = None
                        same_count = 0
                        check_count = 0
            else:
                prev_rounds = rounds
                same_count = 0
                check_count = 0
            prev_check = curr_check
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print(f"[{time.strftime('%H:%M:%S')}] 已停止")
