"""
牌面检测区域截图工具
对当前画面中 main.py 使用的牌面检测区域进行截图，
弹出保存对话框让用户输入文件名并保存。
"""

import mss
import numpy as np
import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import ctypes

# 与 main.py 完全一致的截图区域
_COMBINED = {"left": 365, "top": 805, "width": 175, "height": 223}

def capture_tile():
    """截取牌面区域，与 main.py._capture() 切片一致"""
    with mss.MSS() as sct:
        combined = np.asarray(sct.grab(_COMBINED))
    return combined[80:220, 85:175]

def main():
    img = capture_tile()

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    ret = ctypes.windll.user32.MessageBoxW(0, '点击"是"保存到 targets，点击"否"保存到 distractors', '选择类型', 4)
    if ret == 2:
        messagebox.showinfo('取消', '已取消保存')
        root.destroy()
        return

    sub = 'targets' if ret == 6 else 'distractors'
    default_dir = os.path.join(root_dir, 'pics', sub)
    os.makedirs(default_dir, exist_ok=True)

    file_path = filedialog.asksaveasfilename(
        defaultextension='.png',
        filetypes=[
            ('PNG', '*.png'),
            ('JPEG', '*.jpg'),
            ('所有文件', '*.*'),
        ],
        title=f'保存牌面截图 — {sub}',
        initialdir=default_dir,
    )

    if file_path:
        cv2.imwrite(file_path, cv2.cvtColor(img, cv2.COLOR_BGRA2BGR))
        messagebox.showinfo('保存成功', f'已保存至:\n{file_path}')
    else:
        messagebox.showinfo('取消', '已取消保存')

    root.destroy()

if __name__ == '__main__':
    main()
