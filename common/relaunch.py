import time
import cv2
import numpy as np
import mss
import pyautogui
import winsound
import sys
from common import ui
from common.consts import RETRY_LIMIT, RELAUNCH_THRESHOLD, RELAUNCH_INTERVAL

DEBUG = '--debug' in sys.argv
from common.consts import RELAUNCH_DIR, RELAUNCH_QYZZ_REGION
from common.consts import RELAUNCH_CONTINUE_REGION, RELAUNCH_PRECOND_REGION
from common.consts import PRECONDITION_TEMPLATE

_QYZZ1 = cv2.imread(f'{RELAUNCH_DIR}/qyzz1.png', cv2.IMREAD_GRAYSCALE)
_QYZZ2 = cv2.imread(f'{RELAUNCH_DIR}/qyzz2.png', cv2.IMREAD_GRAYSCALE)
_CONTINUE = cv2.imread(f'{RELAUNCH_DIR}/continue.png', cv2.IMREAD_GRAYSCALE)
_PRECOND = cv2.imread(PRECONDITION_TEMPLATE, cv2.IMREAD_GRAYSCALE)

_SCT = mss.MSS()
RESTART_COUNT = 0
LAST_RESTART = None

def _match(region, template):
    img = np.asarray(_SCT.grab({"left": region[0], "top": region[1], "width": region[2], "height": region[3]}))
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    score, _, _, loc = cv2.minMaxLoc(res)
    th, tw = template.shape[:2]
    center = (region[0] + loc[0] + tw // 2, region[1] + loc[1] + th // 2)
    return float(score), center

def _wait(region, template, label, click_pos=None):
    for attempt in range(1, RETRY_LIMIT + 1):
        score, center = _match(region, template)
        if DEBUG:
            print(f"  [{attempt}/{RETRY_LIMIT}] {label} 匹配度: {score:.3f}")
        if score >= RELAUNCH_THRESHOLD:
            if click_pos is not False:
                pyautogui.click(*center)
                if DEBUG:
                    print(f"  {label} 匹配，点击 {center}")
            else:
                if DEBUG:
                    print(f"  {label} 匹配")
            time.sleep(5)
            if click_pos is not False:
                while True:
                    s, c = _match(region, template)
                    if s < RELAUNCH_THRESHOLD:
                        break
                    pyautogui.click(*c)
                    if DEBUG:
                        print(f"  {label} 画面未改变，再次点击 {c}")
                    time.sleep(5)
            return True
        if attempt < RETRY_LIMIT:
            if DEBUG:
                print(f"  等待 {RELAUNCH_INTERVAL}s 后重试...")
            time.sleep(RELAUNCH_INTERVAL)
    print(f"  重连失败: {label} 匹配超限")
    return False

def _wait_any(region, templates, label, click_pos=None):
    for attempt in range(1, RETRY_LIMIT + 1):
        best_score = 0
        best_center = None
        best_idx = 0
        for i, tmpl in enumerate(templates):
            score, center = _match(region, tmpl)
            if score > best_score:
                best_score = score
                best_center = center
                best_idx = i
            if DEBUG:
                print(f"  [{attempt}/{RETRY_LIMIT}] {label}[{i+1}] 匹配度: {score:.3f}")
        if best_score >= RELAUNCH_THRESHOLD:
            if click_pos is not False:
                pyautogui.click(*best_center)
                if DEBUG:
                    print(f"  {label} 匹配(模板{best_idx+1})，点击 {best_center}")
            else:
                if DEBUG:
                    print(f"  {label} 匹配(模板{best_idx+1})")
            time.sleep(5)
            if click_pos is not False:
                while True:
                    still_match = False
                    for tmpl in templates:
                        s, _ = _match(region, tmpl)
                        if s >= RELAUNCH_THRESHOLD:
                            still_match = True
                            break
                    if not still_match:
                        break
                    pyautogui.click(*best_center)
                    if DEBUG:
                        print(f"  {label} 画面未改变，再次点击 {best_center}")
                    time.sleep(5)
            return True
        if attempt < RETRY_LIMIT:
            if DEBUG:
                print(f"  等待 {RELAUNCH_INTERVAL}s 后重试...")
            time.sleep(RELAUNCH_INTERVAL)
    print(f"  重连失败: {label} 匹配超限")
    return False

def run():
    global RESTART_COUNT, LAST_RESTART
    t = time.strftime('%H:%M:%S')
    print(f"[{t}] 触发重连流程")
    RESTART_COUNT += 1
    LAST_RESTART = t
    for i in range(10):
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        if DEBUG:
            print(f"警告音 {i+1}/10")
        time.sleep(1)
    pyautogui.click(365, 25)      # 新建标签页
    time.sleep(1)
    pyautogui.click(310, 30)      # 关闭旧标签页
    time.sleep(1)
    pyautogui.click(40, 120)      # 收藏夹
    time.sleep(1)
    pyautogui.click(85, 290)      # 网页
    time.sleep(30)

    if not _wait_any(RELAUNCH_QYZZ_REGION, [_QYZZ1, _QYZZ2], "qyzz", True):
        ui.alarm("重连失败: qyzz 匹配超限")
        return
    pyautogui.click(105, 25)      # 静音
    time.sleep(1)
    if not _wait(RELAUNCH_CONTINUE_REGION, _CONTINUE, "continue", True):
        ui.alarm("重连失败: continue 匹配超限")
        return
    if not _wait(RELAUNCH_PRECOND_REGION, _PRECOND, "先决条件", False):
        ui.alarm("重连失败: 先决条件匹配超限")
        return
    print(f"[{time.strftime('%H:%M:%S')}] 重连完成")
