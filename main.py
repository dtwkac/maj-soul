import cv2
import numpy as np
import mss
import pyautogui
import os
import sys
import time
import ctypes
import pytesseract
import winsound
import keyboard
import re
import traceback
import tkinter as tk
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
CLICK_TIMES = 72
LOOP_SLEEP = 1.2
SLEEP_INTERVAL = 0.2
RETRY_LIMIT = 5

# ===== 模板路径 =====
TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'
TARGET_NAMES = {os.path.splitext(f)[0] for f in os.listdir(TARGET_DIR) if f.upper().endswith('.PNG')}

# ===== 特征匹配阈值 =====
THRESHOLD_DEFAULT = 20

_SCT = mss.MSS()
_ORB = cv2.ORB_create(nfeatures=200)
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

def _best_match(bgr):
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
        if good > 50:
            break

    if '--debug' in sys.argv:
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
        text = pytesseract.image_to_string(
            gray, config='--psm 7 -c tessedit_char_whitelist=0123456789/'
        ).strip()
        m = re.match(r'(\d+)/(\d+)', text)
        old = prev
        if m:
            cur = int(m.group(1))
            total = int(m.group(2))

            if prev_score is None or cur >= prev_score - 8 or prev == (cur, total):
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

def _click_tsumo(key, cnt, need):
    print(f"{key} 匹配度{cnt} > 阈值{need} → 自摸")
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

    debug = '--debug' in sys.argv

    if debug:
        root = tk.Tk()
        root.title("雀魂检测")
        root.attributes('-topmost', True)
        root.resizable(False, False)
        root.configure(bg='#ffffff')

        frame = tk.Frame(root, bg='#ffffff', padx=14, pady=8)
        frame.pack(fill=tk.BOTH)

        # 标题行
        tk.Label(frame, text="检测调试", font=('', 11, 'bold'), bg='#ffffff', fg='#3366cc').pack(anchor=tk.W)
        # 分隔线
        tk.Frame(frame, height=2, bg='#3366cc').pack(fill=tk.X, pady=(4, 6))
        # 分数
        _lbl_score = tk.Label(frame, text="分数: ---", font=('Consolas', 16, 'bold'), bg='#ffffff', fg='#333')
        _lbl_score.pack(anchor=tk.W)
        # 动作
        _lbl_action = tk.Label(frame, text="等待中...", font=('Consolas', 16, 'bold'), bg='#ffffff', fg='#888')
        _lbl_action.pack(anchor=tk.W)

        root.update()
        # 固定窗口大小，暂放 (0,0) 测量装饰偏移
        root.geometry("260x150+0+0")
        root.update()
        off_x = frame.winfo_rootx()
        off_y = frame.winfo_rooty()
        new_x = 550 - off_x - root.winfo_width()
        new_y = 770 - off_y - root.winfo_height()
        root.geometry(f"+{new_x}+{new_y}")

    last_score = None

    prev_cap = None
    same_count = 1

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
                same_count = 1
            prev_cap = cap

            if same_count >= 5:  # 连续5帧相同 → 报警
                same_count = 0
                _alarm("画面连续5次结果一致，可能卡住")

            name, conf, is_target = _best_match(cap)

            key = name.replace('.png', '') if name else ''
            need = THRESHOLD_DEFAULT

            score = _check_number(last_score, num_cap)
            print(f"分数: {score}")
            if score != '---':
                m = re.match(r'(\d+)/(\d+)', score)
                if m:
                    last_score = int(m.group(1))
            if debug:
                _lbl_score.configure(text=f"分数: {score}")

            if name and is_target and key in TARGET_NAMES and conf >= need:
                if paused:
                    continue
                if debug:
                    _lbl_action.configure(text=f"自摸  {key} ({conf}/{need})", fg='#006600')
                    root.update()
                _click_tsumo(key, conf, need)
            else:
                if name and is_target and key in TARGET_NAMES:
                    info = f"{key} 匹配度{conf} < 阈值{need}"
                elif name:
                    info = f"{key} 非目标牌"
                else:
                    info = "无匹配"
                if debug:
                    if name:
                        _lbl_action.configure(text=f"跳过  {key}", fg='#cc6600')
                    else:
                        _lbl_action.configure(text=f"跳过  无匹配", fg='#cc6600')
                    root.update()
                _click_skip(info)

            time.sleep(LOOP_SLEEP)
            print("-" * 60)

        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException:
            traceback.print_exc()
            print("\n!!! 发生未预期异常，安全退出 !!!\n")
            os._exit(1)

if __name__ == '__main__':
    main()
