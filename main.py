import keyboard
import ctypes
import time
import cv2
import numpy as np
import re
import traceback
import os
import pyautogui
import mss

import ui
import relaunch
from consts import DEBUG, CENTER, SKIP_BTN, THRESHOLD_DEFAULT, LOOP_SLEEP, SLEEP_INTERVAL, TARGET_NAMES, PRECONDITION_THRESHOLD, NUM_ALARM
from consts import NET_RESET_REGION, NET_RESET_THRESHOLD
from capture import grab_combined
from tile_matcher import best_match, check_precondition
from score_reader import check_number
from clicker import click_tsumo, click_skip

_NET_RESET_TEMPLATE = cv2.imread('pics/net_reset.png', cv2.IMREAD_GRAYSCALE)
_NET_SCT = mss.MSS()

def main():
    keyboard.add_hotkey('ctrl+.', ui.pause_dialog)

    ret = ctypes.windll.user32.MessageBoxW(0, "请切换到游戏窗口，点击确定后开始运行", "准备就绪", 1)
    if ret != 1:
        os._exit(0)
    ui.START_TIME = time.time()
    print("开始!")

    if DEBUG:
        root, lbl_score, lbl_action, lbl_precond, lbl_elapsed, lbl_restarts, lbl_last_restart = ui.setup_debug_window()

    last_score = None
    prev_cap = None
    same_count = 1
    detect_repeat = 1
    last_detect = (None, None)

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
                if DEBUG:
                    print(f"卡住检测: 连续 {same_count} 次相同")
            else:
                same_count = 1
            prev_cap = cap

            if DEBUG:
                elapsed = time.time() - ui.START_TIME
                lbl_elapsed.configure(text=f"已运行: {int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}")
                lbl_restarts.configure(text=f"重启次数: {relaunch.RESTART_COUNT}")
                lbl_last_restart.configure(text=f"上次重启: {relaunch.LAST_RESTART or '---'}")

            # 悬停在跳过按钮
            if same_count >= 5:
                print(f"连续 {same_count} 次相同，悬停跳过按钮重新截图比对")
                pyautogui.moveTo(*SKIP_BTN)
                time.sleep(1)
                combined = grab_combined()
                cap = combined[80:220, 85:175]
                if np.array_equal(cap, prev_cap):
                    if DEBUG:
                        print("卡住确认: 悬停处重新截图与上一帧仍相同，执行重连")
                    relaunch.run()
                    prev_cap = None
                    same_count = 1
                    continue
                prev_cap = cap

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

            if DEBUG:
                if name:
                    color = '#006600' if is_target else '#cc6600'
                    lbl_action.configure(text=f"{key} ({conf}/{need})", fg=color)
                else:
                    lbl_action.configure(text="无匹配", fg='#cc6600')
                root.update()

            # ===== 牌面检测结果一致性判断（降低网络检测开销）=====
            current_detect = (name, is_target)
            if current_detect == last_detect:
                detect_repeat += 1
            else:
                detect_repeat = 1
                last_detect = current_detect

            if detect_repeat >= 5:
                net_cap = np.asarray(_NET_SCT.grab({
                    "left": NET_RESET_REGION[0],
                    "top": NET_RESET_REGION[1],
                    "width": NET_RESET_REGION[2],
                    "height": NET_RESET_REGION[3]
                }))
                net_gray = cv2.cvtColor(net_cap, cv2.COLOR_BGRA2GRAY)
                net_res = cv2.matchTemplate(net_gray, _NET_RESET_TEMPLATE, cv2.TM_CCOEFF_NORMED)
                net_score = float(cv2.minMaxLoc(net_res)[1])
                if net_score >= NET_RESET_THRESHOLD:
                    print(f"牌面检测 5 次一致，匹配到网络断开画面 (匹配度 {net_score:.3f})，执行重连")
                    relaunch.run()
                    prev_cap = None
                    same_count = 1
                    detect_repeat = 1
                    last_detect = (None, None)
                    continue
                print("牌面 5 次一致但非网络断开，继续正常流程")
                detect_repeat = 1

            # ===== OCR 分数检测 =====
            score = check_number(last_score, num_cap)
            print(f"分数: {score}")
            if score != '---':
                m = re.match(r'(\d+)/(\d+)', score)
                if m:
                    last_score = int(m.group(1))
            else:
                print("分数: 未识别，跳过本轮")
                continue

            if last_score < NUM_ALARM:
                ui.alarm(f"分数 {last_score}，低于 {NUM_ALARM}!")
                continue
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
