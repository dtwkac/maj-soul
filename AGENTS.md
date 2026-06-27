# maj-soul — 雀魂自动刷分脚本

## 技术栈
- **语言/运行环境**: Python ≥3.14（`.python-version` / `pyproject.toml`）
- **包管理器**: `uv`（`uv.lock` 锁定）
- **平台**: Windows only（`winsound`、`ctypes`、`keyboard`）

## 关键命令
```bash
uv sync                    # 安装依赖
uv run auto.py             # 运行主脚本
uv run mouse_pos.py        # 坐标捕获工具（右键退出）
# 无测试 / 无 lint / 无 typecheck / 无 CI
```

## 项目结构
- `auto.py` — 唯一生产入口，所有核心逻辑在此
- `mouse_pos.py` — 获取屏幕坐标的辅助工具（Tkinter 悬浮窗）
- `main.py` — 空占位文件，无实际用途
- `pics/targets/` — 目标牌模板（触发自摸）
- `pics/distractors/` — 干扰牌模板（触发跳过）
- `Tesseract-OCR/` — 本地 Tesseract 安装目录（已在 .gitignore）

## 约束
- **分辨率**: 仅支持 1920×1080 全屏，坐标硬编码
- **Tesseract 路径**: 硬编码为 `D:\workspace\maj-soul\Tesseract-OCR\tesseract.exe`
- **模板**: 模板图片必须保持原始像素尺寸，禁止缩放
- **紧急停止**: 鼠标移到屏幕四角可停止（`pyautogui.FAILSAFE = True`）
- **暂停**: `Ctrl+.` 切换暂停/恢复

## 架构要点
- 主循环无限运行，`try/except BaseException` 包裹，异常后 5s 自动继续
- 每轮: 截图(90×153) → ORB BFMatcher(crossCheck, Hamming<50) → 最佳模板决策 → OCR 分数检测 → 自摸/跳过
- 忽略 `mahjong_auto_ORB_*.py`、`auto_ORB_*.py`、`mouse_tracker.py`（.gitignore 排除的旧文件）
- `pyproject.toml` 是唯一项目配置；无 formatter/linter 配置，格式自由
