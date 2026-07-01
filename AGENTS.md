# maj-soul — 雀魂青云之志S4自动刷分脚本

## 技术栈
- **语言/运行环境**: Python ≥3.14（`.python-version` / `pyproject.toml`）
- **包管理器**: `uv`（`uv.lock` 锁定）
- **平台**: Windows only（`winsound`、`ctypes`、`keyboard`、`mss`）

## 关键命令
```bash
uv sync                    # 安装依赖
uv run python main.py      # 静默运行（无 GUI 窗口）
uv run python main.py --debug  # 显示调试信息窗口
uv run python tools/mouse_pos.py        # 坐标捕获工具（右键退出）
uv run python tools/threshold_test.py   # 阈值检测测试工具
# 无测试 / 无 lint / 无 typecheck / 无 CI
```

## 提交规则
- **commit 前先同步 README.md 和 AGENTS.md**，确保代码变更对应的文档（常量值、快捷键、流程图等）已更新

## 项目结构
- `consts.py` — 全部常量（坐标、阈值、路径、DEBUG 标志）
- `capture.py` — 截屏（mss，合并 175×223 区域）
- `tile_matcher.py` — 牌型匹配（ORB 特征 + BFMatcher，模板加载）
- `score_reader.py` — 分数检测（Tesseract OCR，含 debug 截图）
- `clicker.py` — 点击动作（自摸/跳过）
- `ui.py` — 用户交互（报警、暂停弹窗、debug 窗口）
- `main.py` — 入口，主循环
- `tools/mouse_pos.py` — 获取屏幕坐标的辅助工具（Tkinter 悬浮窗）
- `tools/threshold_test.py` — 阈值检测测试工具（Tkinter GUI）
- `pics/targets/` — 目标牌模板（触发自摸）
- `pics/distractors/` — 干扰牌模板（触发跳过）
- `Tesseract-OCR/` — 本地 Tesseract 安装目录（已在 .gitignore）

## 约束
- **分辨率**: 仅支持 1920×1080 全屏，坐标硬编码
- **Tesseract 路径**: 硬编码为 `D:\workspace\maj-soul\Tesseract-OCR\tesseract.exe`
- **模板**: 模板图片必须保持原始像素尺寸，禁止缩放
- **停止**: 关闭控制台窗口可停止程序
- **暂停**: `Ctrl+.` 弹窗暂停；确定继续运行，取消退出程序

## 架构要点
- 主循环无限运行，`try/except BaseException` 包裹，异常后打印堆栈并 `os._exit(1)` 安全退出
- 每轮: 合并截屏(capture, 175×223) → 视图切片取牌面/分数 ROI → 卡住检测（与上轮截图比较，连续5次相同报警） → ORB BFMatcher(tile_matcher, crossCheck, Hamming<50, good>50时break) → OCR 分数检测(score_reader，每轮统一调用，分数大幅下降时连续两次一致即接受） → 自摸/跳过
- ORB nfeatures=200，检测器与 BFMatcher 在模块级缓存（`tile_matcher._ORB` / `tile_matcher._BF`），每圈不重复构造
- OCR 灰度图直出 Tesseract（无二值化/放大），PSM 7 + whitelist 0123456789/
- `ui.alarm`: 5 × Beep(660Hz, 200ms) + PlaySound("SystemExclamation")，消息框确定继续/取消退出
- 无匹配时等待 0.2s 重试一次（重截屏+重新匹配），仍无匹配才跳过
- `--debug` 可选：开启 Tkinter 调试窗口（`ui.setup_debug_window`，右下角固定 550,770，260×150，Consolas 16 bold）
- `Tesseract-OCR/`（已在 .gitignore）
- `pyproject.toml` 是唯一项目配置；无 formatter/linter 配置，格式自由
