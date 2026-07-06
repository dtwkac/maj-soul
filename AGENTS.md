# maj-soul — 雀魂青云之志S4自动刷分脚本

## 技术栈
- **语言/运行环境**: Python ≥3.14（`.python-version` / `pyproject.toml`）
- **包管理器**: `uv`（`uv.lock` 锁定）
- **平台**: Windows only（`winsound`、`ctypes`、`keyboard`、`mss`）

## 关键命令
```bash
uv sync                    # 安装依赖
uv run python main.py              # 静默运行（无 GUI 窗口）
uv run python main.py --debug      # 显示调试信息窗口
uv run python tools/mouse_pos.py        # 坐标捕获工具（右键退出）
uv run python tools/threshold_test.py   # 阈值检测测试工具
# 无测试 / 无 lint / 无 typecheck / 无 CI
```

## 提交规则
- **commit 前先同步 README.md 和 AGENTS.md**，确保代码变更对应的文档（常量值、快捷键、流程图等）已更新

## 项目结构
- `consts.py` — 全部常量（坐标、阈值、路径、DEBUG 标志）
- `capture.py` — 截屏（mss，合并 175×223 区域）
- `tile_matcher.py` — 牌型匹配（ORB 特征 + BFMatcher，模板加载）+ 先决条件检测
- `score_reader.py` — 分数检测（Tesseract OCR，含 debug 截图）
- `clicker.py` — 点击动作（自摸/跳过）
- `relaunch.py` — 重连模块（卡住时刷新游戏并等待回归）
- `ui.py` — 用户交互（报警、暂停弹窗、debug 窗口）
- `main.py` — 入口，主循环
- `tools/mouse_pos.py` — 获取屏幕坐标的辅助工具（Tkinter 悬浮窗）
- `tools/threshold_test.py` — 阈值检测测试工具（Tkinter GUI）
- `pics/targets/` — 目标牌模板（触发自摸）
- `pics/distractors/` — 干扰牌模板（触发跳过）
- `pics/relaunch/` — 重连匹配模板（qyzz.png, continue.png）
- `pics/net_reset.png` — 网络断开画面模板
- `pics/precondition.png` — 先决条件模板（控制重试）
- `Tesseract-OCR/` — 本地 Tesseract 安装目录（已在 .gitignore）

## 约束
- **分辨率**: 仅支持 1920×1080 全屏，坐标硬编码
- **Tesseract 路径**: 硬编码为 `D:\workspace\maj-soul\Tesseract-OCR\tesseract.exe`
- **模板**: 模板图片必须保持原始像素尺寸，禁止缩放
- **停止**: 关闭控制台窗口可停止程序
- **暂停**: `Ctrl+.` 弹窗暂停；确定继续运行，取消退出程序

## 架构要点
- 启动弹窗（确定/取消），取消时 `os._exit(0)` 安全退出
- 主循环无限运行，`try/except BaseException` 包裹，异常后打印堆栈并 `os._exit(1)` 安全退出
- 每轮: 合并截屏(capture, 175×223) → 视图切片取牌面/分数 ROI → 卡住检测（与上轮截图比较，连续3次相同则悬停跳过按钮重截图，仍相同则播放10次警告音后触发重连(relaunch.run)；DEBUG 时从第2次起打印重复次数） → 先决条件检测(tile_matcher.check_precondition, TM_CCOEFF_NORMED，不满足时重试） → ORB BFMatcher(best_match, 无重试一次出结果） → 网络断连检测（记录识别结果，连续5次相同时截图对比 net_reset.png；匹配则重连） → OCR 分数检测(score_reader.check_number） → 自摸/跳过
- 重连模块 `relaunch.py`：依次点击刷新按钮、匹配 qyzz 画面、匹配 continue 画面、匹配先决条件，全部成功后继续主循环；任一步骤超限则回调 ui.alarm
- ORB nfeatures=200，检测器与 BFMatcher 在模块级缓存（`tile_matcher._ORB` / `tile_matcher._BF`），每圈不重复构造
- OCR 灰度图 2 倍放大 + Otsu 二值化后直出 Tesseract，PSM 7 + whitelist 0123456789/，分数大幅下降时连续两次一致即接受
- `ui.alarm`: 5 × Beep(660Hz, 200ms) + PlaySound("SystemExclamation")，消息框确定继续/取消退出；所有报警均含 `ALARM_TIMEOUT` 秒超时自动关闭游戏窗口（1890, 27 停留1s后点击）并退出
- 重试只由先决条件控制：不满足则跳过本轮；牌面识别无重试
- `--debug` 可选：开启 Tkinter 调试窗口（`ui.setup_debug_window`，右下角固定 550,770，260×160，Consolas 16 bold），实时显示先决分数/OCR分数/当前动作
- `Tesseract-OCR/`（已在 .gitignore）
- `pyproject.toml` 是唯一项目配置；无 formatter/linter 配置，格式自由
