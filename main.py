import cv2
import numpy as np
import mss
import pyautogui
import os
import time
import ctypes
import pytesseract
import winsound
import keyboard
import re
import traceback
pytesseract.pytesseract.tesseract_cmd = r'D:\workspace\maj-soul\Tesseract-OCR\tesseract.exe'
# ===== 分数报警阈值 =====
NUM_ALARM = 105

# ===== 屏幕坐标配置 =====
TILE_REGION = (450, 885, 90, 140)
NUM_REGION = (365, 805, 125, 30)
CENTER = (960, 540)
TSUMO_BTN = (1200, 820)
SKIP_BTN = (500, 950)

# ===== 循环配置 =====
CLICK_TIMES = 70
LOOP_SLEEP = 1.2
RETRY_LIMIT = 10
SLEEP_INTERVAL = 0.2

# ===== 模板路径 =====
TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'
TARGET_NAMES = {os.path.splitext(f)[0] for f in os.listdir(TARGET_DIR) if f.upper().endswith('.PNG')}

# ===== 特征匹配阈值 =====
THRESHOLD_DEFAULT = 20

_SCT = mss.MSS()
_ORB = cv2.ORB_create(nfeatures=500)
_BF = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
_COMBINED = {"left": 365, "top": 805, "width": 175, "height": 223}

def _grab_combined():
    return np.asarray(_SCT.grab(_COMBINED))

# ===== 报警 =====

def _alarm(msg):
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

# ===== 暂停控制 =====
paused = False

def _pause_dialog():
    global paused
    paused = True
    ret = ctypes.windll.user32.MessageBoxW(0, "已暂停，点击确定继续运行，取消退出程序", "暂停", 1)
    paused = False
    if ret != 1:
        os._exit(0)

# ===== 模板加载 =====

def _load_templates(folder, is_target):
    items = []
    for f in os.listdir(folder):
        if not f.upper().endswith('.PNG'):
            continue
        img = cv2.imread(os.path.join(folder, f), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        kp, des = _ORB.detectAndCompute(img, None)
        items.append((f, des, is_target))
    return items

templates = _load_templates(TARGET_DIR, True)
if os.path.isdir(DISTRACTOR_DIR):
    templates += _load_templates(DISTRACTOR_DIR, False)
if not templates:
    print("错误: 没有模板图片!"); exit(1)

print(f"目标牌: {', '.join(sorted(TARGET_NAMES))}")

# ===== 截图与匹配 =====

def _capture():
    combined = _grab_combined()
    return combined[80:220, 85:175]

def _best_match(bgr, debug=True):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGRA2GRAY)
    _, des2 = _ORB.detectAndCompute(gray, None)
    if des2 is None:
        print("未检测到牌面特征点")
        return None, 0, False

    best_name, best_cnt, best_is_target = None, 0, False
    scores = []

    for name, des1, is_target in templates:
        if des1 is None:
            scores.append((name, 0))
            continue
        matches = _BF.match(des1, des2)
        good = sum(1 for m in matches if m.distance < 50)
        scores.append((name, good))
        if good > best_cnt:
            best_cnt = good
            best_name = name
            best_is_target = is_target

    if debug:
        scores.sort(key=lambda x: -x[1])
        dbg = '  '.join(f"{s[0].replace('.png', '')}={s[1]}" for s in scores[:6])
        label = best_name.replace('.png', '') if best_name else '无'
        print(f"[特征] {dbg} → 最佳:{label}({best_cnt})")

    return best_name, best_cnt, best_is_target

# ===== 分数检测 =====

def _check_number(prev_score=None, num_cap=None):
    prev = None
    mismatch = 0
    while True:
        if num_cap is not None:
            gray = cv2.cvtColor(num_cap, cv2.COLOR_BGRA2GRAY)
            num_cap = None
        else:
            combined = _grab_combined()
            gray = cv2.cvtColor(combined[0:30, 0:125], cv2.COLOR_BGRA2GRAY)
        gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_LINEAR)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(
            th, config='--psm 7 -c tessedit_char_whitelist=0123456789/'
        ).strip()
        m = re.match(r'(\d+)/(\d+)', text)
        old = prev
        if m:
            cur = int(m.group(1))
            total = int(m.group(2))

            if prev_score is None or cur >= prev_score - 8:
                if cur < NUM_ALARM:
                    _alarm(f"分数 {cur}，低于 {NUM_ALARM}!")
                return text

            if prev == (cur, total):
                if cur < NUM_ALARM:
                    _alarm(f"分数 {cur}，低于 {NUM_ALARM}!")
                return text

            prev = (cur, total)
            print(f"分数变化异常({prev_score}→{cur})，等待稳定")
        else:
            prev = None
        mismatch += 1
        p = f"{old[0]}/{old[1]}" if old else "无"
        print(f"分数不匹配({mismatch}) 上次:{p} 当前:{text}，重试")
        if mismatch >= RETRY_LIMIT:
            mismatch = 0
            _alarm("分数持续异常")
        if paused:
            return '---'
        time.sleep(SLEEP_INTERVAL)

# ===== 点击动作 =====

def _click_tsumo(name_str, cnt, need):
    print(f"{name_str.replace('.png', '')} 匹配度{cnt} > 阈值{need} → 自摸")
    pyautogui.moveTo(*TSUMO_BTN)
    pyautogui.click(*TSUMO_BTN)
    for _ in range(CLICK_TIMES):
        pyautogui.click(*CENTER)
        time.sleep(0.1)

def _click_skip(info):
    print(f"{info} → 跳过")
    pyautogui.moveTo(*SKIP_BTN)
    pyautogui.click(*SKIP_BTN)
    pyautogui.moveTo(*CENTER)

# ===== 主循环 =====

def main():
    keyboard.add_hotkey('ctrl+.', _pause_dialog)

    ctypes.windll.user32.MessageBoxW(0, "请切换到游戏窗口，点击确定后开始运行", "准备就绪", 0)
    print("开始!")
    last_score = None

    prev_cap = None
    same_count = 0
    no_match_count = 0

    while True:
        try:
            while paused:
                time.sleep(SLEEP_INTERVAL)

            pyautogui.moveTo(*CENTER)

            combined = _grab_combined()
            cap = combined[80:220, 85:175]
            num_cap = combined[0:30, 0:125]
            if prev_cap is not None and np.array_equal(cap, prev_cap):
                same_count += 1
            else:
                same_count = 0
            prev_cap = cap

            if same_count >= 4:
                same_count = 0
                _alarm("画面连续5次结果一致，可能卡住")

            name, conf, is_target = _best_match(cap)

            if not name:
                no_match_count += 1
                if no_match_count >= RETRY_LIMIT:
                    no_match_count = 0
                else:
                    print(f"无匹配({no_match_count}/{RETRY_LIMIT})，继续检测")
                    time.sleep(SLEEP_INTERVAL)
                    continue
            else:
                no_match_count = 0

            key = name.replace('.png', '') if name else ''
            need = THRESHOLD_DEFAULT
            score = _check_number(last_score, num_cap)
            print(f"分数: {score}")
            if paused:
                continue
            if score != '---':
                m = re.match(r'(\d+)/(\d+)', score)
                if m:
                    last_score = int(m.group(1))

            if name and is_target and key in TARGET_NAMES and conf >= need:
                _click_tsumo(name, conf, need)
            else:
                if name and is_target and key in TARGET_NAMES:
                    info = f"{name.replace('.png', '')} 匹配度{conf} < 阈值{need}"
                elif name:
                    info = f"{name.replace('.png', '')} 非目标牌"
                else:
                    info = "无匹配"
                _click_skip(info)

            time.sleep(LOOP_SLEEP)
            print("-" * 60)

        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException:
            traceback.print_exc()
            print("\n!!! 异常，5秒后继续 !!!\n")
            time.sleep(5)

if __name__ == '__main__':
    main()
