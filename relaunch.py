import time
import cv2
import numpy as np
import mss
import pyautogui
import ui
from consts import RETRY_LIMIT, RELAUNCH_THRESHOLD, RELAUNCH_INTERVAL
from consts import RELAUNCH_DIR, RELAUNCH_BTN, RELAUNCH_QYZZ_REGION, RELAUNCH_QYZZ_CLICK
from consts import RELAUNCH_CONTINUE_REGION, RELAUNCH_CONTINUE_CLICK, RELAUNCH_PRECOND_REGION
from consts import PRECONDITION_TEMPLATE

_QYZZ = cv2.imread(f'{RELAUNCH_DIR}/qyzz.png', cv2.IMREAD_GRAYSCALE)
_CONTINUE = cv2.imread(f'{RELAUNCH_DIR}/continue.png', cv2.IMREAD_GRAYSCALE)
_PRECOND = cv2.imread(PRECONDITION_TEMPLATE, cv2.IMREAD_GRAYSCALE)

def _match(region, template):
    with mss.MSS() as sct:
        img = np.asarray(sct.grab({"left": region[0], "top": region[1], "width": region[2], "height": region[3]}))
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    return float(cv2.minMaxLoc(res)[1])

def _wait(region, template, label, click_pos=None):
    for attempt in range(1, RETRY_LIMIT + 1):
        score = _match(region, template)
        print(f"  [{attempt}/{RETRY_LIMIT}] {label} 匹配度: {score:.3f}")
        if score >= RELAUNCH_THRESHOLD:
            if click_pos:
                pyautogui.click(*click_pos)
                print(f"  {label} 匹配，点击 {click_pos}")
                time.sleep(5)
            else:
                print(f"  {label} 匹配")
            return True
        if attempt < RETRY_LIMIT:
            print(f"  等待 {RELAUNCH_INTERVAL}s 后重试...")
            time.sleep(RELAUNCH_INTERVAL)
    print(f"  重连失败: {label} 匹配超限")
    return False

def run():
    print("触发重连流程")
    pyautogui.click(*RELAUNCH_BTN)
    print("已点击刷新，等待 30s...")
    time.sleep(30)

    if not _wait(RELAUNCH_QYZZ_REGION, _QYZZ, "qyzz", RELAUNCH_QYZZ_CLICK):
        ui.alarm("重连失败: qyzz 匹配超限")
        return
    if not _wait(RELAUNCH_CONTINUE_REGION, _CONTINUE, "continue", RELAUNCH_CONTINUE_CLICK):
        ui.alarm("重连失败: continue 匹配超限")
        return
    if not _wait(RELAUNCH_PRECOND_REGION, _PRECOND, "先决条件"):
        ui.alarm("重连失败: 先决条件匹配超限")
        return
    print("重连完成")
