import tkinter as tk
import pyautogui

class MouseTracker:
    def __init__(self):
        self.root = tk.Tk()
        
        # --- 窗体美化设置 ---
        self.root.title("坐标")
        self.root.attributes("-topmost", True)     # 永远置顶
        self.root.attributes("-alpha", 0.85)       # 半透明效果 (0.0 ~ 1.0)
        self.root.overrideredirect(True)           # 隐藏边框和标题栏
        self.root.configure(bg="#2d2d2d")          # 深色背景
        
        # 标签组件：用于显示文字
        self.label = tk.Label(
            self.root, 
            text="X: 0000 Y: 0000", 
            font=("Consolas", 11, "bold"), 
            fg="#61afef",                          # 科技感蓝色字体
            bg="#2d2d2d", 
            padx=10, 
            pady=5
        )
        self.label.pack()

        # 绑定右键点击事件，方便随时退出程序
        self.root.bind("<Button-3>", lambda e: self.root.destroy())
        
        # 绑定左键拖动，虽然它会自动跟随鼠标，但留个拖动保险
        self.label.bind("<B1-Motion>", self.drag)

        # 开始实时更新循环
        self.update_position()

    def drag(self, event):
        # 允许通过左键拖动窗口
        self.root.geometry(f"+{event.x_root}+{event.y_root}")

    def update_position(self):
        try:
            # 获取鼠标当前坐标
            x, y = pyautogui.position()
            
            # 更新文本
            self.label.config(text=f"X: {x} Y: {y}")
            
            # 让悬浮窗稍微偏离鼠标光标一点（比如右下方 +20 像素），避免挡住鼠标点击
            # 1920x1080 范围内移动
            self.root.geometry(f"+{x + 20}+{y + 20}")
            
        except Exception:
            pass
        
        # 每 20 毫秒刷新一次（丝滑无卡顿）
        self.root.after(20, self.update_position)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MouseTracker()
    app.run()