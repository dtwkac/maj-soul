import keyboard
import ctypes
import time
import numpy as np
import re
import traceback
import os
import sys
import pyautogui

import ui
from consts import DEBUG, CENTER, THRESHOLD_DEFAULT, LOOP_SLEEP, SLEEP_INTERVAL, TARGET_NAMES
from capture import grab_combined
from tile_matcher import best_match
from score_reader import check_number
from clicker import click_tsumo, click_skip

def main():
    keyboard.add_hotkey('ctrl+.', ui.pause_dialog)

    ctypes.windll.user32.MessageBoxW(0, "请切换到游戏窗口，点击确定后开始运行", "准备就绪", 0)
    print("开始!")

    if DEBUG:
        root, lbl_score, lbl_action = ui.setup_debug_window()

    last_score = None
    prev_cap = None
    same_count = 1

    while True:
        try:
            while ui.paused:
                time.sleep(SLEEP_INTERVAL)

            pyautogui.moveTo(*CENTER)

            combined = grab_combined()
            cap = combined[80:220, 85:175]
            num_cap = combined[0:30, 0:125]
            if prev_cap is not None and np.array_equal(cap, prev_cap):
                same_count += 1
            else:
                same_count = 1
            prev_cap = cap

            if same_count >= 5:
                same_count = 0
                ui.alarm("画面连续5次结果一致，可能卡住")

            name, conf, is_target = best_match(cap)

            if name is None:
                time.sleep(SLEEP_INTERVAL)
                combined = grab_combined()
                cap = combined[80:220, 85:175]
                num_cap = combined[0:30, 0:125]
                name, conf, is_target = best_match(cap)

            key = name.replace('.png', '') if name else ''
            need = THRESHOLD_DEFAULT

            score = check_number(last_score, num_cap)
            print(f"分数: {score}")
            if score != '---':
                m = re.match(r'(\d+)/(\d+)', score)
                if m:
                    last_score = int(m.group(1))
            if DEBUG:
                lbl_score.configure(text=f"分数: {score}")

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
