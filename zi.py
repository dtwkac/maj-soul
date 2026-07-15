import time
import cv2
import numpy as np
import os
import pyautogui
import mss
import traceback
import keyboard
import sys

import ui
from consts import LOOP_SLEEP, SLEEP_INTERVAL

DEBUG = '--debug' in sys.argv

TILE_REGION = (1385, 885, 90, 140)
PRECOND_REGION = (1415, 885, 30, 20)
PRECOND_THRESHOLD = 0.9
ZI_THRESHOLD = 20

_CENTER = (960, 540)
_SKIP_BTN = (1430, 950)
_TSUMO_BTN = (1200, 820)

_ZI_DIR = r'D:\workspace\maj-soul\pics\zi'
_PRECOND_TEMPLATE = cv2.imread(r'D:\workspace\maj-soul\pics\pre.png', cv2.IMREAD_GRAYSCALE)

_ORB = cv2.ORB_create(nfeatures=200)
_BF = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
_SCT = mss.MSS()

_zi_templates = []
for f in os.listdir(_ZI_DIR):
    if not f.upper().endswith('.PNG'):
        continue
    img = cv2.imread(os.path.join(_ZI_DIR, f), cv2.IMREAD_GRAYSCALE)
    if img is None:
        continue
    _, des = _ORB.detectAndCompute(img, None)
    _zi_templates.append((f, des))
if not _zi_templates:
    print("错误: 没有字牌模板图片!"); exit(1)

def check_precondition():
    if _PRECOND_TEMPLATE is None:
        return 0.0
    img = np.asarray(_SCT.grab({"left": PRECOND_REGION[0], "top": PRECOND_REGION[1],
                                 "width": PRECOND_REGION[2], "height": PRECOND_REGION[3]}))
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    result = cv2.matchTemplate(gray, _PRECOND_TEMPLATE, cv2.TM_CCOEFF_NORMED)
    return float(cv2.minMaxLoc(result)[1])

def check_zi(cap):
    gray = cv2.cvtColor(cap, cv2.COLOR_BGRA2GRAY)
    _, des2 = _ORB.detectAndCompute(gray, None)
    if des2 is None:
        return None, 0

    best_name, best_cnt = None, 0
    for name, des1 in _zi_templates:
        if des1 is None:
            continue
        matches = _BF.match(des1, des2)
        good = sum(1 for m in matches if m.distance < 50)
        if good > best_cnt:
            best_cnt = good
            best_name = name
        if good > 50:
            break
    return best_name, best_cnt

def main():
    import ctypes
    keyboard.add_hotkey('ctrl+.', ui.pause_dialog)

    ret = ctypes.windll.user32.MessageBoxW(0, "请切换到游戏窗口，点击确定后开始运行", "准备就绪", 1)
    if ret != 1:
        os._exit(0)
    ui.START_TIME = time.time()

    print(f"[{time.strftime('%H:%M:%S')}] zi 开始")

    while True:
        try:
            while ui.paused:
                time.sleep(SLEEP_INTERVAL)

            pyautogui.moveTo(*_CENTER)

            cap = np.asarray(_SCT.grab({"left": TILE_REGION[0], "top": TILE_REGION[1],
                                         "width": TILE_REGION[2], "height": TILE_REGION[3]}))

            precond_score = check_precondition()
            if precond_score < PRECOND_THRESHOLD:
                if DEBUG:
                    print(f"先决条件不满足 ({precond_score:.3f} < {PRECOND_THRESHOLD})，等待重试")
                time.sleep(SLEEP_INTERVAL)
                continue

            if DEBUG:
                print(f"先决条件满足 ({precond_score:.3f})")

            name, conf = check_zi(cap)
            key = name.replace('.png', '') if name else None

            if name and conf >= ZI_THRESHOLD:
                print(f"[{time.strftime('%H:%M:%S')}] 匹配字牌 {key} ({conf} >= {ZI_THRESHOLD}) → 跳过")
                pyautogui.moveTo(*_SKIP_BTN)
                time.sleep(0.1)
                pyautogui.click(*_SKIP_BTN)
            else:
                if DEBUG:
                    if name:
                        print(f"[{time.strftime('%H:%M:%S')}] 匹配字牌 {key} ({conf} < {ZI_THRESHOLD})，阈值不足 → 自摸")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] 未匹配字牌 → 自摸")
                pyautogui.moveTo(*_TSUMO_BTN)
                time.sleep(0.1)
                pyautogui.click(*_TSUMO_BTN)
                for _ in range(25):
                    pyautogui.click(*_CENTER)
                    time.sleep(0.1)

            time.sleep(LOOP_SLEEP)

        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException:
            traceback.print_exc()
            print("\n!!! 发生未预期异常，安全退出 !!!\n")
            os._exit(1)

if __name__ == '__main__':
    main()
