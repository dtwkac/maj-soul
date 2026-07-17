import pyautogui
import keyboard
import time
import subprocess
import csv
import re
import pytesseract
import mss
import cv2
import numpy as np

_CE_PROC = 'cheatengine-x86_64-SSE4.exe'

def is_ce_running():
    out = subprocess.check_output(
        ['tasklist', '/FI', f'IMAGENAME eq {_CE_PROC}', '/FO', 'CSV', '/NH'],
        encoding='gbk'
    )
    return bool(out.strip())

def kill_ce():
    if is_ce_running():
        print("关闭已有CE进程")
        subprocess.run(['taskkill', '/F', '/IM', _CE_PROC],
                        capture_output=True, encoding='gbk')


def speedhack():
    # 步骤1: 获取firefox最大内存占用pid并转8位hex
    output = subprocess.check_output(
        ['tasklist', '/FI', 'IMAGENAME eq firefox.exe', '/FO', 'CSV', '/NH'],
        encoding='gbk'
    )
    best_pid, best_mem = None, 0
    for row in csv.reader(output.strip().splitlines()):
        if len(row) < 5:
            continue
        pid = int(row[1])
        mem = int(row[4].replace(' K', '').replace(',', ''))
        if mem > best_mem:
            best_pid, best_mem = pid, mem
    if best_pid is None:
        raise RuntimeError("未找到firefox进程")
    pid16 = f"{best_pid:08X}"
    print(f"firefox PID={best_pid}, hex={pid16}")

    # 步骤2: 启动CE
    pyautogui.click(950, 1050)
    time.sleep(3)
    if not is_ce_running():
        raise RuntimeError("CE启动失败，进程未运行")

    # 步骤3: 打开进程选择窗口
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
            print(f"  匹配PID(差异{best_diffs}字符), 点击 y={click_y}")
            pyautogui.click(880, click_y)
            return True
        return False

    # 先连按3次page down到最底部
    print("  page down x3...")
    for _ in range(3):
        pyautogui.press('pagedown')
        time.sleep(0.5)

    found = False
    for attempt in range(10):
        print(f"  第{attempt+1}次 pageup + OCR...")
        pyautogui.press('pageup')
        time.sleep(1)
        lines = ocr_lines()
        print(f"  OCR行数: {len(lines)}")
        if find_and_click(lines):
            found = True
            break
    if not found:
        print(f"[!] 未找到进程 {pid16}-firefox.exe，等待手动关闭CE...")
        while True:
            time.sleep(1)
    time.sleep(1)

    # 步骤5: 点击Open
    pyautogui.click(895, 760)
    time.sleep(1)

    # 步骤6: Enable Speedhack
    pyautogui.click(1200, 500)
    time.sleep(1)

    # 步骤7: 输入倍速5
    pyautogui.click(1275, 525)
    time.sleep(0.3)
    keyboard.press_and_release('ctrl+a')
    time.sleep(0.1)
    keyboard.press_and_release('backspace')
    time.sleep(0.1)
    keyboard.write('5')
    time.sleep(1)

    # 步骤8: Apply
    pyautogui.click(1280, 605)

    # 步骤9: firefox回到前台
    pyautogui.click(1800, 540)
    print("speedhack 已设置")
