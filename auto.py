import cv2
import numpy as np
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
pyautogui.FAILSAFE = True

# ===== 分数报警阈值 =====
NUM_ALARM = 105   # cur < NUM_ALARM 时触发报警暂停
MAX_SCORE = 184   # 分数上限，画面未完全更新时检测不到此值则继续重试

# ===== 屏幕坐标配置 =====
TILE_REGION = (435, 875, 90, 153)   # 牌面截图区域 (left, top, width, height)
NUM_REGION = (365, 805, 125, 30)    # 分数数字区域
CENTER = (960, 540)                 # 屏幕中心（用于连点和鼠标复位）
SELF_BTN = (1200, 820)              # 自摸按钮坐标
SKIP_BTN = (500, 950)               # 跳过按钮坐标

# ===== 按键延迟配置（秒） =====
CLICK_DELAY = 0.05   # 点自摸前停顿
SKIP_DELAY = 0.05    # 点跳过前停顿
CLICK_TIMES = 70     # 自摸后连点次数（7.0秒）
LOOP_SLEEP = 1.2     # 主循环每次间隔

# ===== 模板路径 =====
TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'
TARGET_NAMES = {'1m', '9m', '9s', '1p', '9p', 'dong'}

# ===== 特征匹配阈值 =====
CONF_TARGET = 8
CONF_STRICT = {
    '9s.JPG': 10,   # 9条易与7条混淆，提高阈值避免误触
    '1p.JPG': 9,
    '9p.JPG': 9,
    '9m.JPG': 5,    # 9万特征点偏少，单独降低
}

# ===== 报警 =====

def _alarm(msg):
    """响三声警报 + 弹窗（确定=继续，取消=退出）"""
    winsound.Beep(880, 300)
    time.sleep(0.2)
    winsound.Beep(880, 300)
    time.sleep(0.2)
    winsound.Beep(880, 600)
    ret = ctypes.windll.user32.MessageBoxW(0, msg, "报警", 1)
    if ret != 1:
        os._exit(0)

# ===== 暂停控制 =====
paused = False

def _pause_dialog():
    """Ctrl+. 暂停 + 弹窗（确定=继续，取消=退出）"""
    global paused
    paused = True
    ret = ctypes.windll.user32.MessageBoxW(0, "已暂停，确定继续运行，取消退出程序", "暂停", 1)
    paused = False
    if ret != 1:
        os._exit(0)

keyboard.add_hotkey('ctrl+.', _pause_dialog)

# ===== 模板加载 =====

def _load_templates(folder, is_target):
    items = []
    orb = cv2.ORB_create(nfeatures=500)
    for f in os.listdir(folder):
        if not f.upper().endswith(('.JPG', '.JPEG', '.PNG')):
            continue
        img = cv2.imread(os.path.join(folder, f), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        kp, des = orb.detectAndCompute(img, None)
        cnt = len(kp) if kp is not None else 0
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
    """截取牌面区域，返回 RGB 数组"""
    return np.array(pyautogui.screenshot(region=TILE_REGION))

def _best_match(bgr, debug=True):
    """ORB 特征匹配：连续两次匹配结果相同则返回；10次不一致则报警"""
    orb = cv2.ORB_create(nfeatures=500)
    prev = None
    mismatch = 0
    while True:
        fail_count = 0
        while True:
            gray = cv2.cvtColor(bgr, cv2.COLOR_RGB2GRAY)
            _, des2 = orb.detectAndCompute(gray, None)
            if des2 is not None:
                break
            if paused:
                return None, 0, False
            fail_count += 1
            print(f"未检测到牌面特征点，第{fail_count}次重试")
            if fail_count >= 30:
                fail_count = 0
                _alarm("连续多次无法检测到牌面特征点，请检查游戏窗口")
            time.sleep(0.2)
            bgr = _capture()

        best_name, best_cnt, best_is_target = None, 0, False
        scores = []
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        for name, des1, is_target in templates:
            if des1 is None:
                scores.append((name, 0))
                continue
            matches = bf.match(des1, des2)
            good = sum(1 for m in matches if m.distance < 50)
            scores.append((name, good))
            if good > best_cnt:
                best_cnt = good
                best_name = name
                best_is_target = is_target

        if debug:
            scores.sort(key=lambda x: -x[1])
            dbg = '  '.join(f"{s[0].replace('.JPG','')}={s[1]}" for s in scores[:6])
            label = best_name.replace('.JPG','') if best_name else '无'
            print(f"[特征] {dbg} → 最佳:{label}({best_cnt})")

        cur = (best_name, best_cnt, best_is_target)
        if prev == cur:
            return cur
        if paused:
            return None, 0, False
        mismatch += 1
        p_name, p_cnt, _ = prev or ('无', 0, False)
        p_label = p_name.replace('.JPG','') if p_name else '无'
        c_label = best_name.replace('.JPG','') if best_name else '无'
        print(f"不匹配({mismatch}) 上次:{p_label}({p_cnt}) / 当前:{c_label}({best_cnt})，重试")
        if mismatch >= 10:
            mismatch = 0
            _alarm("牌面结果持续不一致")
        prev = cur
        time.sleep(0.1)
        bgr = _capture()

# ===== 分数检测 =====

def _check_number():
    """OCR 读取分数区域，连续两次相同则接受；10次不一致则报警"""
    prev = None
    mismatch = 0
    while True:
        img = np.array(pyautogui.screenshot(region=NUM_REGION))
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_LINEAR)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(
            th, config='--psm 7 -c tessedit_char_whitelist=0123456789/'
        ).strip()
        m = re.match(r'(\d+)/(\d+)', text)
        if m:
            cur = int(m.group(1))
            total = int(m.group(2))
            if prev == (cur, total):
                if cur < NUM_ALARM:
                    _alarm(f"分数 {cur}，低于 {NUM_ALARM}!")
                return text
            prev = (cur, total)
        else:
            prev = None
        mismatch += 1
        if mismatch >= 10:
            mismatch = 0
            _alarm("分数持续异常")
        if paused:
            return '---'
        print(f"分数不匹配({mismatch}) {text!r}，重试")
        time.sleep(0.2)

# ===== 点击动作 =====

def _click_self(name_str, cnt, need):
    print(f"{name_str.replace('.JPG','')} 匹配={cnt}/{need} → 自摸")
    pyautogui.moveTo(*SELF_BTN)
    time.sleep(CLICK_DELAY)
    pyautogui.click(*SELF_BTN)
    for _ in range(CLICK_TIMES):
        pyautogui.click(*CENTER)
        time.sleep(0.1)

def _click_skip(info):
    print(f"{info} → 跳过")
    pyautogui.moveTo(*SKIP_BTN)
    time.sleep(SKIP_DELAY)
    pyautogui.click(*SKIP_BTN)
    pyautogui.moveTo(*CENTER)

# ===== 主循环 =====

ctypes.windll.user32.MessageBoxW(0, "请切换到游戏窗口，点击确认后开始运行", "准备就绪", 0)
print("开始!")

while True:
    try:
        while paused:
            time.sleep(0.3)

        pyautogui.moveTo(*CENTER)

        name, conf, is_target = _best_match(_capture())

        key = name.replace('.JPG', '') if name else ''
        need = CONF_STRICT.get(name, CONF_TARGET)
        score = _check_number()
        print(f"分数: {score}")
        if paused:
            continue

        if name and is_target and key in TARGET_NAMES and conf >= need:
            _click_self(name, conf, need)
        else:
            info = f"{name}(匹配={conf})" if name else "无匹配"
            _click_skip(info)

        time.sleep(LOOP_SLEEP)
        print("-" * 60)

    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException:
        traceback.print_exc()
        print("\n!!! 异常，5秒后继续 !!!\n")
        time.sleep(5)
