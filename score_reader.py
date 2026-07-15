import cv2
import pytesseract
import re
import time
import os
import sys
import shutil
from consts import NUM_ALARM, RETRY_LIMIT, SLEEP_INTERVAL
from capture import grab_combined
import ui

DEBUG = '--debug' in sys.argv

_DEBUG_SAVED_SCORES = set()
if DEBUG:
    shutil.rmtree('temp', ignore_errors=True)
    os.makedirs('temp')

def check_number(prev_score=None, num_cap=None):
    # prev: 上一次循环中解析到的有效 (cur, total)，用于"连续两次一致"判断
    prev = None
    mismatch = 0
    while True:
        if num_cap is not None:
            raw = num_cap.copy()
            gray = cv2.cvtColor(num_cap, cv2.COLOR_BGRA2GRAY)
            num_cap = None
        else:
            combined = grab_combined()
            raw = combined[0:30, 0:125].copy()
            gray = cv2.cvtColor(raw, cv2.COLOR_BGRA2GRAY)
        gray = cv2.bilateralFilter(gray, 5, 75, 75)
        big = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, big = cv2.threshold(big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(
            big, config='--psm 7 -c tessedit_char_whitelist=0123456789/'
        ).strip()
        m = re.match(r'(\d+)/(\d+)', text)

        # old: prev 在本次 OCR 前的快照，仅用于日志（prev 随后可能被改写）
        old = prev

        if m:
            cur = int(m.group(1))
            total = int(m.group(2))

            if DEBUG:
                fn = m.group(1)
                if fn not in _DEBUG_SAVED_SCORES:
                    cv2.imwrite(f"temp/{fn}.png", raw[..., :3])
                    _DEBUG_SAVED_SCORES.add(fn)

            # 接受条件：首次检测 / 分数未大幅下降 / 高分连续两次一致（都是第一张自摸），且不高于上限
            # 低分（<NUM_ALARM）即使连续一致也不直接接受，走下面 retry 计数
            if cur <= total:
                if prev_score is None or cur >= prev_score - 8 or (prev == (cur, total) and cur >= NUM_ALARM):
                    prev = (cur, total)
                    return text
            if DEBUG:
                print(f"分数检测异常({prev_score}→{cur})，等待稳定")
        else:
            prev = None
        mismatch += 1
        p = f"{old[0]}/{old[1]}" if old else "无"
        if DEBUG:
            print(f"分数不匹配({mismatch}) 上次:{p} 当前:{text}，重试")
        # 累计异常次数达到上限 → 报警
        if mismatch >= RETRY_LIMIT:
            mismatch = 0
            ui.alarm("分数持续异常")
        if ui.paused:
            if m:
                return text
            if old is not None:
                return f"{old[0]}/{old[1]}"
            return '---'
        time.sleep(SLEEP_INTERVAL)
