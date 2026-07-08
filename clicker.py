import pyautogui
import time
from consts import TSUMO_BTN, CENTER, SKIP_BTN, CLICK_TIMES, DEBUG

def click_tsumo(key, cnt, need):
    if DEBUG:
        print(f"{key} 匹配度{cnt} > 阈值{need} → 自摸")
    pyautogui.moveTo(*TSUMO_BTN)
    pyautogui.click(*TSUMO_BTN)
    for _ in range(CLICK_TIMES):
        pyautogui.click(*CENTER)
        time.sleep(0.1)

def click_skip(info):
    if DEBUG:
        print(f"{info} → 跳过")
    pyautogui.moveTo(*SKIP_BTN)
    pyautogui.click(*SKIP_BTN)
    pyautogui.moveTo(*CENTER)
