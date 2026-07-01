"""
阈值检测测试工具
对当前画面进行 ORB 特征匹配，以表格形式展示各模板的匹配分数，
用于调校匹配阈值和验证模板效果。
"""

import cv2
import numpy as np
import pyautogui
import os
import tkinter as tk
from tkinter import ttk

# ===== 牌面截图区域（与 main.py 一致） =====
TILE_REGION = (450, 885, 90, 140)

# ===== 模板路径 =====
TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'
TARGET_NAMES = {os.path.splitext(f)[0] for f in os.listdir(TARGET_DIR) if f.upper().endswith('.PNG')}

# ===== 特征匹配阈值（与 main.py 一致） =====
THRESHOLD_DEFAULT = 20


def load_templates(folder, is_target):
    """读取文件夹内所有图片，用 ORB 提取特征描述子"""
    items = []
    orb = cv2.ORB_create(nfeatures=500)
    for f in os.listdir(folder):
        if not f.upper().endswith('.PNG'):
            continue
        img = cv2.imread(os.path.join(folder, f), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        kp, des = orb.detectAndCompute(img, None)
        items.append((f, des, is_target))
    return items


# 模块级：启动时一次性加载所有模板
templates = load_templates(TARGET_DIR, True)
if os.path.isdir(DISTRACTOR_DIR):
    templates += load_templates(DISTRACTOR_DIR, False)


class App:
    """Tkinter GUI：开始→检测→展示结果→继续检测 循环"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("牌面检测")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)

        # 主容器，padding 16px
        self.frame = ttk.Frame(self.root, padding=16)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 两个子 Frame 持久化，切换时只 pack_forget/pack，避免闪烁
        self._build_start()
        self._build_result()

        self._show_start()

    # ---------- 构建 UI ----------

    def _build_start(self):
        """初始状态：提示 + 开始按钮"""
        self.start_frame = ttk.Frame(self.frame)
        ttk.Label(self.start_frame, text="准备就绪，点击开始检测", font=('', 12)).pack(pady=(0, 12))
        ttk.Button(self.start_frame, text="开始检测", command=self._run).pack()

    def _build_result(self):
        """结果界面：预创建所有控件，后续只更新内容"""
        self.result_frame = ttk.Frame(self.frame)

        # 标题
        ttk.Label(self.result_frame, text="检测结果", font=('', 15, 'bold'), foreground='#cc3300').pack(anchor=tk.W)
        # 最佳匹配（橙色加粗）
        self.best_label = ttk.Label(self.result_frame, font=('', 13, 'bold'), foreground='#cc6600')
        self.best_label.pack(anchor=tk.W)
        # 判定结果（红色/绿色）
        self.judge_label = ttk.Label(self.result_frame, font=('', 12, 'bold'))
        self.judge_label.pack(anchor=tk.W, pady=(0, 6))

        # 分隔线
        tk.Frame(self.result_frame, height=1, bg='#ccc').pack(fill=tk.X)

        # 表格容器
        body = ttk.Frame(self.result_frame)
        body.pack(fill=tk.BOTH)

        # 目标牌组
        self._add_group(body, '目标牌', show_header=True)
        self.target_rows = []
        for name, des, is_tgt in templates:
            if not is_tgt:
                continue
            row = self._build_row(body, name.replace('.png', ''), is_target=True)
            self.target_rows.append(row)

        # 干扰牌组
        self._add_group(body, '干扰牌')
        self.dist_rows = []
        for name, des, is_tgt in templates:
            if is_tgt:
                continue
            row = self._build_row(body, name.replace('.png', ''), is_target=False)
            self.dist_rows.append(row)

        # 底部按钮
        btn_frame = ttk.Frame(self.result_frame)
        btn_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_frame, text="继续检测", command=self._run).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="退出", command=self.root.destroy).pack(side=tk.LEFT)

    def _add_group(self, parent, title, show_header=False):
        """添加分组标题，可选的表头栏"""
        ttk.Label(parent, text=title, font=('', 11, 'bold'), foreground='#333').pack(anchor=tk.W, pady=(4, 1))
        if show_header:
            hdr = tk.Frame(parent, bg='#e0e0e0')
            hdr.pack(fill=tk.X)
            for txt, w in [('牌', 6), ('分数', 6), ('阈值', 6), ('类别', 4)]:
                tk.Label(hdr, text=txt, font=('Consolas', 11), bg='#e0e0e0', width=w, anchor=tk.W).pack(side=tk.LEFT)

    def _build_row(self, parent, label, is_target):
        """创建单行控件，返回字典便于后续更新"""
        need = THRESHOLD_DEFAULT
        bg = '#e8e8e8' if is_target else '#fafafa'
        row = tk.Frame(parent, bg=bg)
        row.pack(fill=tk.X)

        lbl_name = tk.Label(row, text=label, font=('Consolas', 11), bg=bg, width=6, anchor=tk.W)
        lbl_name.pack(side=tk.LEFT)

        lbl_cnt = tk.Label(row, text='0', font=('Consolas', 11), bg=bg, width=6, anchor=tk.W)
        lbl_cnt.pack(side=tk.LEFT)

        lbl_need = tk.Label(row, text=str(need), font=('Consolas', 11), bg=bg, width=6, anchor=tk.W)
        lbl_need.pack(side=tk.LEFT)

        lbl_type = tk.Label(row, text='目标' if is_target else '干扰', font=('', 10), bg=bg,
                            fg='#006600' if is_target else '#996600', width=4)
        lbl_type.pack(side=tk.LEFT)

        return {'frame': row, 'name': lbl_name, 'cnt': lbl_cnt, 'need': lbl_need, 'type': lbl_type,
                'bg_normal': bg, 'is_target': is_target}

    # ---------- 界面切换 ----------

    def _show_start(self):
        self.result_frame.pack_forget()
        self.start_frame.pack(fill=tk.BOTH, expand=True)

    def _show_result(self, scores, best_name, best_cnt, best_is_target, judge):
        self.start_frame.pack_forget()
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # 更新顶部最佳信息
        best_label = best_name.replace('.png', '') if best_name else '无'
        self.best_label.configure(text=f"最佳: {best_label} ({best_cnt})")

        # 更新判定结果
        action, info, is_tsumo = judge
        fg = '#006600' if is_tsumo else '#cc3300'
        self.judge_label.configure(text=f"判定: {action} ({info})", foreground=fg)

        # 构建 标签→(分数, 是否最佳) 映射
        score_map = {}
        for name, cnt, is_tgt in scores:
            score_map[name.replace('.png', '')] = (cnt, name == best_name)

        # 逐行更新分数、背景色、字体粗细
        for row_data in self.target_rows + self.dist_rows:
            label = row_data['name'].cget('text')
            cnt, is_best = score_map.get(label, (0, False))
            bg = '#ffffcc' if is_best else row_data['bg_normal']
            row_data['frame'].configure(bg=bg)
            row_data['name'].configure(bg=bg, font=('Consolas', 11, 'bold' if is_best else 'normal'))
            row_data['cnt'].configure(text=str(cnt), bg=bg, font=('Consolas', 11, 'bold' if is_best else 'normal'))
            row_data['need'].configure(bg=bg)
            row_data['type'].configure(bg=bg)

    # ---------- 检测流程 ----------

    def _run(self):
        """截图 → 匹配 → 展示结果"""
        bgr = np.array(pyautogui.screenshot(region=TILE_REGION))
        orb = cv2.ORB_create(nfeatures=500)
        gray = cv2.cvtColor(bgr, cv2.COLOR_RGB2GRAY)
        _, des2 = orb.detectAndCompute(gray, None)

        if des2 is None:
            self._show_result([], None, 0, False, ('跳过', '无特征点', False))
            return

        # 对所有模板进行 BFMatcher 交叉匹配，取好匹配数（距离 < 50）
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        scores = []
        for name, des1, is_target in templates:
            if des1 is None:
                scores.append((name, 0, is_target))
                continue
            matches = bf.match(des1, des2)
            good = sum(1 for m in matches if m.distance < 50)
            scores.append((name, good, is_target))
        scores.sort(key=lambda x: -x[1])

        best_name, best_cnt, best_is_target = scores[0]
        key = best_name.replace('.png', '') if best_name else ''
        if best_name and best_is_target and key in TARGET_NAMES and best_cnt >= THRESHOLD_DEFAULT:
            judge = ('自摸', f'{key} {best_cnt} ≥ {THRESHOLD_DEFAULT}', True)
        elif best_name and best_is_target and key in TARGET_NAMES:
            judge = ('跳过', f'{key} {best_cnt} < {THRESHOLD_DEFAULT}', False)
        elif best_name:
            judge = ('跳过', f'{key} 非目标牌', False)
        else:
            judge = ('跳过', '无匹配', False)

        self._show_result(scores, best_name, best_cnt, best_is_target, judge)

    def run(self):
        self.root.mainloop()


App().run()
