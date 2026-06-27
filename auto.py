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

# ===== 屏幕坐标配置 =====
TILE_REGION = (435, 875, 90, 153)   # 牌面截图区域 (left, top, width, height)
NUM_REGION = (365, 805, 110, 30)    # 分数数字区域
CENTER = (960, 540)                 # 屏幕中心（用于连点和鼠标复位）
SELF_BTN = (1200, 820)              # 自摸按钮坐标
SKIP_BTN = (500, 950)               # 跳过按钮坐标

# ===== 按键延迟配置（秒） =====
CLICK_DELAY = 0.05   # 点自摸前停顿
SKIP_DELAY = 0.05    # 点跳过前停顿
CLICK_TIMES = 73     # 自摸后连点次数（7.3秒）
LOOP_SLEEP = 1.2     # 主循环每次间隔

# ===== 模板路径 =====
TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'
TARGET_NAMES = {'1m', '9m', '9s', '1p', '9p', 'dong'}

# ===== 特征匹配阈值 =====
# 最佳模板的好匹配数 >= 阈值时判定命中
CONF_TARGET = 8
CONF_STRICT = {
    '9s.JPG': 10,   # 9条易与7条混淆，提高阈值避免误触
    '1p.JPG': 9,
    '9p.JPG': 9,
    '9m.JPG': 5,    # 9万特征点偏少，单独降低
}

# ===== 分数报警阈值 =====
# cur < max * NUM_ALARM_RATIO 时触发报警暂停
NUM_ALARM_RATIO = 110 / 184

# ===== 暂停控制 =====
paused = False

def _toggle_pause():
    global paused
    paused = not paused
    print(f"\n{'=== 已暂停 (Ctrl+. 恢复) ===' if paused else '=== 已恢复 ==='}\n")

keyboard.add_hotkey('ctrl+.', _toggle_pause)

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
        print(f"  [{('目标' if is_target else '干扰')}] {f} ({cnt} 特征点)")
    return items

templates = _load_templates(TARGET_DIR, True)
if os.path.isdir(DISTRACTOR_DIR):
    templates += _load_templates(DISTRACTOR_DIR, False)
if not templates:
    print("错误: 没有模板图片!"); exit(1)

n_target = sum(1 for t in templates if t[2])
n_dist = len(templates) - n_target
print(f"共 {len(templates)} 模板 (目标{n_target}, 干扰{n_dist})")
print(f"目标牌: {', '.join(sorted(TARGET_NAMES))}")
print("关闭窗口即可停止")

# ===== 截图与匹配 =====

def _capture():
    """截取牌面区域，返回 RGB 数组"""
    return np.array(pyautogui.screenshot(region=TILE_REGION))

def _best_match(bgr, debug=True):
    """ORB 特征匹配：对所有模板计算好匹配数，返回 (最佳模板名, 好匹配数, 是否目标)"""
    gray = cv2.cvtColor(bgr, cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(nfeatures=500)
    _, des2 = orb.detectAndCompute(gray, None)
    if des2 is None:
        print("  [特征] 无特征点")
        return None, 0, False

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
        print(f"  [特征] {dbg} → 最佳:{label}({best_cnt})")
    return best_name, best_cnt, best_is_target

# ===== 分数检测 =====

def _check_number():
    """OCR 读取分数区域，低于阈值则报警暂停"""
    img = np.array(pyautogui.screenshot(region=NUM_REGION))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(
        th, config='--psm 7 -c tessedit_char_whitelist=0123456789/'
    ).strip()
    m = re.match(r'(\d+)/(\d+)', text)
    if m:
        cur_str, max_str = m.group(1), m.group(2)
        cur, maxv = int(cur_str), int(max_str)
        score = f"{cur}/{maxv}"
        # 判断是否低于报警分数
        if cur < maxv * NUM_ALARM_RATIO:
            winsound.Beep(880, 300)
            time.sleep(0.2)
            winsound.Beep(880, 300)
            time.sleep(0.2)
            winsound.Beep(880, 600)
            ctypes.windll.user32.MessageBoxW(
                0, f"分数={cur}/{maxv}，低于 {NUM_ALARM_RATIO:.0%}，程序暂停", "报警", 0
            )
            global paused
            paused = True
            print(f"\n=== 分数 {cur}/{maxv} 低于 {NUM_ALARM_RATIO:.0%}，已暂停 (Ctrl+F3 恢复) ===\n")
    else:
        score = '---'
    return score

# ===== 点击动作 =====

def _click_self(ms, score, name_str, cnt, need):
    print(f"[{ms:.0f}ms] {name_str.replace('.JPG','')} 匹配={cnt}/{need} → 自摸")
    pyautogui.moveTo(*SELF_BTN)
    time.sleep(CLICK_DELAY)
    pyautogui.click(*SELF_BTN)
    for _ in range(CLICK_TIMES):
        pyautogui.click(*CENTER)
        time.sleep(0.1)

def _click_skip(ms, info):
    print(f"[{ms:.0f}ms] {info} → 跳过")
    pyautogui.moveTo(*SKIP_BTN)
    time.sleep(SKIP_DELAY)
    pyautogui.click(*SKIP_BTN)
    pyautogui.moveTo(*CENTER)

# ===== 主循环 =====

print("10秒后开始，请切换到游戏窗口...")
for i in range(10, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print("开始!")

while True:
    try:
        while paused:
            time.sleep(0.3)

        pyautogui.moveTo(*CENTER)
        t0 = time.time()

        name, conf, is_target = _best_match(_capture())
        elapsed = (time.time() - t0) * 1000

        key = name.replace('.JPG', '') if name else ''
        need = CONF_STRICT.get(name, CONF_TARGET)
        score = _check_number()

        if name and is_target and key in TARGET_NAMES and conf >= need:
            _click_self(elapsed, score, name, conf, need)
        else:
            info = f"{name}(匹配={conf})" if name else "无匹配"
            _click_skip(elapsed, info)

        time.sleep(LOOP_SLEEP)

    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException:
        traceback.print_exc()
        print("\n!!! 异常，5秒后继续 !!!\n")
        time.sleep(5)
