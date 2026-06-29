import cv2
import numpy as np
import pyautogui
import os
import tkinter as tk
from tkinter import ttk

pyautogui.FAILSAFE = True

TILE_REGION = (435, 875, 90, 153)
TARGET_DIR = r'D:\workspace\maj-soul\pics\targets'
DISTRACTOR_DIR = r'D:\workspace\maj-soul\pics\distractors'
TARGET_NAMES = {'1m', '9m', '9s', '1p', '9p', 'dong'}
THRESHOLD_DEFAULT = 10

def load_templates(folder, is_target):
    items = []
    orb = cv2.ORB_create(nfeatures=500)
    for f in os.listdir(folder):
        if not f.upper().endswith(('.JPG', '.JPEG', '.PNG')):
            continue
        img = cv2.imread(os.path.join(folder, f), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        kp, des = orb.detectAndCompute(img, None)
        items.append((f, des, is_target))
    return items

templates = load_templates(TARGET_DIR, True)
if os.path.isdir(DISTRACTOR_DIR):
    templates += load_templates(DISTRACTOR_DIR, False)

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("牌面检测")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)

        self.frame = ttk.Frame(self.root, padding=16)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self._build_start()
        self._build_result()

        self._show_start()

    def _build_start(self):
        self.start_frame = ttk.Frame(self.frame)
        ttk.Label(self.start_frame, text="准备就绪，点击开始检测", font=('', 12)).pack(pady=(0, 12))
        ttk.Button(self.start_frame, text="开始检测", command=self._run).pack()

    def _build_result(self):
        self.result_frame = ttk.Frame(self.frame)

        ttk.Label(self.result_frame, text="检测结果", font=('', 15, 'bold'), foreground='#cc3300').pack(anchor=tk.W)
        self.best_label = ttk.Label(self.result_frame, font=('', 13, 'bold'), foreground='#cc6600')
        self.best_label.pack(anchor=tk.W, pady=(0, 6))

        tk.Frame(self.result_frame, height=1, bg='#ccc').pack(fill=tk.X)

        body = ttk.Frame(self.result_frame)
        body.pack(fill=tk.BOTH)

        self._add_group(body, '目标牌', show_header=True)
        self.target_rows = []
        for name, des, is_tgt in templates:
            if not is_tgt:
                continue
            row = self._build_row(body, name.replace('.JPG', ''), is_target=True)
            self.target_rows.append(row)

        self._add_group(body, '干扰牌')
        self.dist_rows = []
        for name, des, is_tgt in templates:
            if is_tgt:
                continue
            row = self._build_row(body, name.replace('.JPG', ''), is_target=False)
            self.dist_rows.append(row)

        btn_frame = ttk.Frame(self.result_frame)
        btn_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_frame, text="继续检测", command=self._run).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="退出", command=self.root.destroy).pack(side=tk.LEFT)

    def _add_group(self, parent, title, show_header=False):
        ttk.Label(parent, text=title, font=('', 11, 'bold'), foreground='#333').pack(anchor=tk.W, pady=(4, 1))
        if show_header:
            hdr = tk.Frame(parent, bg='#e0e0e0')
            hdr.pack(fill=tk.X)
            for txt, w in [('牌', 6), ('分数', 6), ('阈值', 6), ('类别', 4)]:
                tk.Label(hdr, text=txt, font=('Consolas', 11), bg='#e0e0e0', width=w, anchor=tk.W).pack(side=tk.LEFT)

    def _build_row(self, parent, label, is_target):
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

    def _show_start(self):
        self.result_frame.pack_forget()
        self.start_frame.pack(fill=tk.BOTH, expand=True)

    def _show_result(self, scores, best_name, best_cnt, best_is_target):
        self.start_frame.pack_forget()
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        best_label = best_name.replace('.JPG', '') if best_name else '无'
        self.best_label.configure(text=f"最佳: {best_label} ({best_cnt})")

        score_map = {}
        for name, cnt, is_tgt in scores:
            score_map[name.replace('.JPG', '')] = (cnt, name == best_name)

        for row_data in self.target_rows + self.dist_rows:
            label = row_data['name'].cget('text')
            cnt, is_best = score_map.get(label, (0, False))
            bg = '#ffffcc' if is_best else row_data['bg_normal']
            row_data['frame'].configure(bg=bg)
            row_data['name'].configure(bg=bg, font=('Consolas', 11, 'bold' if is_best else 'normal'))
            row_data['cnt'].configure(text=str(cnt), bg=bg, font=('Consolas', 11, 'bold' if is_best else 'normal'))
            row_data['need'].configure(bg=bg)
            row_data['type'].configure(bg=bg)

    def _run(self):
        bgr = np.array(pyautogui.screenshot(region=TILE_REGION))
        orb = cv2.ORB_create(nfeatures=500)
        gray = cv2.cvtColor(bgr, cv2.COLOR_RGB2GRAY)
        _, des2 = orb.detectAndCompute(gray, None)

        if des2 is None:
            self._show_result([], None, 0, False)
            return

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

        self._show_result(scores, best_name, best_cnt, best_is_target)

    def run(self):
        self.root.mainloop()

App().run()
