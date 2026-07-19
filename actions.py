import pyautogui
import time
import sys
import random
from consts import TSUMO_BTN, CENTER, SKIP_BTN, CLICK_TIMES

DEBUG = '--debug' in sys.argv

def click_tsumo(key, cnt, need):
    if DEBUG:
        print(f"{key} 匹配度{cnt} > 阈值{need} → 自摸")
    dx = random.randint(-5, 5)
    dy = random.randint(-5, 5)
    pyautogui.moveTo(*TSUMO_BTN)
    pyautogui.click(TSUMO_BTN[0] + dx, TSUMO_BTN[1] + dy)
    for _ in range(CLICK_TIMES):
        pyautogui.click(*CENTER)
        time.sleep(0.1)

def click_skip(info):
    if DEBUG:
        print(f"{info} → 跳过")
    pyautogui.moveTo(*SKIP_BTN)
    pyautogui.click(*SKIP_BTN)
    pyautogui.moveTo(*CENTER)
