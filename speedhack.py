import pyautogui
import keyboard
import time
import subprocess
import csv
import re
import os
import sys
import pytesseract
import mss
import cv2
import numpy as np

DEBUG = '--debug' in sys.argv

_CE_PROC = 'cheatengine-x86_64-SSE4-AVX2.exe'
_CE_DIR = r'D:\workspace\maj-soul\Cheat Engine'
_CE_EXE = os.path.join(_CE_DIR, 'Cheat Engine.exe')

def is_ce_running():
    out = subprocess.check_output(
        ['tasklist', '/FI', f'IMAGENAME eq {_CE_PROC}', '/FO', 'CSV', '/NH'],
        encoding='gbk'
    )
    return _CE_PROC.lower() in out.lower()

def kill_ce():
    if is_ce_running():
        if DEBUG:
            print("  关闭已有CE进程")
        subprocess.run(['taskkill', '/F', '/IM', _CE_PROC],
                        capture_output=True, encoding='gbk')
        time.sleep(1)
        if DEBUG:
            print("  CE进程已关闭")


def speedhack():
    # 步骤1: 获取firefox最大内存占用pid并转8位hex
    output = subprocess.check_output(
        ['tasklist', '/FI', 'IMAGENAME eq firefox.exe', '/FO', 'CSV', '/NH'],
        encoding='gbk'
    )
    rows = [r for r in csv.reader(output.strip().splitlines()) if len(r) >= 5]
    best_pid, best_mem = None, 0
    for row in rows:
        pid = int(row[1])
        mem = int(row[4].replace(' K', '').replace(',', ''))
        if mem > best_mem:
            best_pid, best_mem = pid, mem
    if best_pid is None:
        print("[!] 未找到firefox进程")
        return False
    pid16 = f"{best_pid:08X}"
    if DEBUG:
        print(f"  firefox PID={best_pid}, hex={pid16}")
        print(f"  共 {len(rows)} 个firefox进程, 最大内存={best_mem}K")

    # 步骤2: 启动CE
    if DEBUG:
        print("  [步骤2] 启动CE...")
    subprocess.Popen([_CE_EXE])
    time.sleep(3)
    if not is_ce_running():
        print("[!] CE启动失败，进程未运行")
        kill_ce()
        return False
    if DEBUG:
        print("  CE进程已运行")

    # 步骤3: 打开进程选择窗口
    if DEBUG:
        print("  [步骤3] 打开进程选择窗口")
    pyautogui.click(580, 235)
    time.sleep(1)

    # 步骤4: OCR查找进程
    proc_region = {"left": 827, "top": 360, "width": 293, "height": 380}
    sct = mss.MSS()

    def ocr_lines():
        img = np.asarray(sct.grab(proc_region))
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        big = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        big = cv2.adaptiveThreshold(big, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 10)
        data = pytesseract.image_to_data(big, config='--psm 6', output_type=pytesseract.Output.DICT)
        lines = {}
        for i, txt in enumerate(data['text']):
            txt = txt.strip()
            if not txt:
                continue
            y = data['top'][i]
            h = data['height'][i]
            placed = False
            for ly in list(lines):
                if abs(ly - y) < 15:
                    lines[ly]['text'] += txt
                    lines[ly]['y'] = min(lines[ly]['y'], y)
                    lines[ly]['h'] = max(lines[ly]['h'], h)
                    placed = True
                    break
            if not placed:
                lines[y] = {'text': txt, 'y': y, 'h': h}
        return lines

    def find_and_click(lines):
        norm_pid = pid16.lower()
        best_match = None
        best_diffs = 999
        for ly, info in lines.items():
            if 'firefox' not in info['text'].lower():
                continue
            hex_str = re.sub(r'[^0-9a-fA-F]', '', info['text'])
            for j in range(len(hex_str) - 7):
                candidate = hex_str[j:j+8].lower()
                diffs = sum(1 for a, b in zip(candidate, norm_pid) if a != b)
                if diffs < best_diffs:
                    best_diffs = diffs
                    best_match = info
        if best_match and best_diffs == 0:
            cy = best_match['y'] + best_match['h'] // 2
            click_y = proc_region["top"] + cy // 2
            if DEBUG:
                print(f"  匹配PID(差异{best_diffs}字符), 点击 y={click_y}")
            pyautogui.click(880, click_y)
            return True
        if DEBUG and best_match:
            print(f"  最佳匹配差异{best_diffs}字符, 未达精确匹配")
        return False

    # 先连按3次page down到最底部
    for _ in range(3):
        pyautogui.press('pagedown')
        time.sleep(0.5)

    found = False
    for attempt in range(5):
        if attempt > 0:
            pyautogui.press('pageup')
        time.sleep(1)
        for retry in range(3):
            if retry > 0:
                time.sleep(1)
            if DEBUG:
                print(f"  第{attempt+1}页 第{retry+1}次 OCR...")
            lines = ocr_lines()
            if DEBUG:
                print(f"  OCR行数: {len(lines)}")
            if find_and_click(lines):
                found = True
                break
        if found:
            break
    if not found:
        print(f"[!] 未找到进程 {pid16}-firefox.exe")
        kill_ce()
        return False
    time.sleep(1)

    # 步骤5: 点击Open
    if DEBUG:
        print("  [步骤5] Open")
    pyautogui.click(895, 760)
    time.sleep(1)

    # 步骤6: Enable Speedhack
    if DEBUG:
        print("  [步骤6] Enable Speedhack")
    pyautogui.click(1200, 500)
    time.sleep(1)

    # 步骤7: 输入倍速5
    if DEBUG:
        print("  [步骤7] 输入倍速5")
    pyautogui.click(1275, 525)
    time.sleep(0.3)
    keyboard.press_and_release('ctrl+a')
    time.sleep(0.1)
    keyboard.press_and_release('backspace')
    time.sleep(0.1)
    keyboard.write('5')
    time.sleep(1)

    # 步骤8: Apply
    if DEBUG:
        print("  [步骤8] Apply")
    pyautogui.moveTo(1280, 605)
    time.sleep(1)
    pyautogui.click(1280, 605)

    # 步骤9: firefox回到前台
    if DEBUG:
        print("  [步骤9] firefox前台")
    pyautogui.moveTo(1800, 540)
    time.sleep(1)
    pyautogui.click(1800, 540)
    print(f"[{time.strftime('%H:%M:%S')}] speedhack 已设置")
    print('-' * 80)
    return True
