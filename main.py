import keyboard
import ctypes
import time
import numpy as np
import re
import traceback
import os
import threading
import pyautogui

import ui
from consts import DEBUG, CENTER, THRESHOLD_DEFAULT, LOOP_SLEEP, SLEEP_INTERVAL, TARGET_NAMES, PRECONDITION_THRESHOLD
from capture import grab_combined
from tile_matcher import best_match, check_precondition
from score_reader import check_number
from clicker import click_tsumo, click_skip

def main():
    keyboard.add_hotkey('ctrl+.', ui.pause_dialog)

    ret = ctypes.windll.user32.MessageBoxW(0, "请切换到游戏窗口，点击确定后开始运行", "准备就绪", 1)
    if ret != 1:
        os._exit(0)
    print("开始!")

    if DEBUG:
        root, lbl_score, lbl_action, lbl_precond = ui.setup_debug_window()

    last_score = None
    prev_cap = None
    same_count = 1

    while True:
        try:
            # ===== 暂停检测 =====
            while ui.paused:
                time.sleep(SLEEP_INTERVAL)

            pyautogui.moveTo(*CENTER)

            # ===== 合并截屏 =====
            combined = grab_combined()
            cap = combined[80:220, 85:175]      # 牌面 ROI
            num_cap = combined[0:30, 0:125]     # 分数 ROI

            # ===== 卡住检测（始终运行，先于先决条件）=====
            if prev_cap is not None and np.array_equal(cap, prev_cap):
                same_count += 1
                if DEBUG and same_count >= 2:
                    print(f"卡住检测: 连续 {same_count} 次相同")
            else:
                same_count = 1
            prev_cap = cap

            # 每种牌在麻将中仅有4张，同一局中不可能出现5张相同画面
            if same_count >= 5:
                same_count = 0
                cancelled = threading.Event()
                def _auto_close():
                    if not cancelled.wait(300):
                        pyautogui.moveTo(1890, 27)
                        time.sleep(1)
                        pyautogui.click(1890, 27)
                        print("卡住检测超时(5min)，自动关闭游戏窗口")
                        os._exit(0)
                threading.Thread(target=_auto_close, daemon=True).start()
                ui.alarm("画面连续5次结果一致，可能卡住")
                cancelled.set()

            # ===== 先决条件检测（控制重试，不满足时不进入牌面/分数检测）=====
            precond_score = check_precondition(combined[80:100, 110:145])
            if DEBUG:
                lbl_precond.configure(text=f"先决: {precond_score:.3f}")

            if precond_score < PRECONDITION_THRESHOLD:
                if DEBUG:
                    print(f"先决条件不满足 ({precond_score:.3f} < {PRECONDITION_THRESHOLD})，等待重试")
                time.sleep(SLEEP_INTERVAL)
                continue

            # ===== ORB 牌面匹配（无重试，一次出结果）=====
            name, conf, is_target = best_match(cap)

            key = name.replace('.png', '') if name else ''
            need = THRESHOLD_DEFAULT

            # ===== OCR 分数检测 =====
            score = check_number(last_score, num_cap)
            print(f"分数: {score}")
            if score != '---':
                m = re.match(r'(\d+)/(\d+)', score)
                if m:
                    last_score = int(m.group(1))
            if DEBUG:
                lbl_score.configure(text=f"分数: {score}")

            # ===== 决策：自摸 / 跳过 =====
            if name and is_target and key in TARGET_NAMES and conf >= need:
                if ui.paused:
                    continue
                if DEBUG:
                    lbl_action.configure(text=f"自摸  {key} ({conf}/{need})", fg='#006600')
                    root.update()
                click_tsumo(key, conf, need)
            else:
                if name and is_target and key in TARGET_NAMES:
                    info = f"{key} 匹配度{conf} < 阈值{need}"
                elif name:
                    info = f"{key} 非目标牌"
                else:
                    info = "无匹配"
                if DEBUG:
                    if name:
                        lbl_action.configure(text=f"跳过  {key}", fg='#cc6600')
                    else:
                        lbl_action.configure(text=f"跳过  无匹配", fg='#cc6600')
                    root.update()
                click_skip(info)

            # ===== 循环间隔 =====
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
