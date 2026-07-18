# maj-soul — 雀魂青云之志S4自动刷分脚本

## 技术栈
- **语言/运行环境**: Python ≥3.14（`.python-version` / `pyproject.toml`）
- **包管理器**: `uv`（`uv.lock` 锁定）
- **平台**: Windows only（`winsound`、`ctypes`、`keyboard`、`mss`）

## 关键命令
```bash
uv sync                    # 安装依赖
uv run python tsumo19d.py              # 静默运行（无 GUI 窗口）
uv run python tsumo19d.py --debug      # 显示调试信息窗口
uv run python zi.py                    # 字牌自摸/跳过（无 GUI 窗口）
uv run python zi.py --debug            # 字牌自摸/跳过（带调试日志）
uv run python auto_clicker.py          # 连点器（自动重启）
uv run python cloud_bottle.py          # 刷印章连点器（w 键暂停）
uv run python tools/mouse_pos.py       # 坐标捕获工具（右键退出）
uv run python tools/threshold_test.py  # 阈值检测测试工具
# 无测试 / 无 lint / 无 typecheck / 无 CI
```

## 提交规则
- **commit 前先同步 README.md 和 AGENTS.md**，确保代码变更对应的文档（常量值、快捷键、流程图等）已更新

## 项目结构
- `consts.py` — 全部常量（坐标、阈值、路径）
- `capture.py` — 截屏（mss，合并 175×223 区域）
- `tile_matcher.py` — 牌型匹配（ORB 特征 + BFMatcher，模板加载）+ 先决条件检测
- `score_reader.py` — 分数检测（Tesseract OCR，含 debug 截图）
- `actions.py` — 点击动作（自摸/跳过）
- `relaunch.py` — 重连模块（卡住时刷新游戏并等待回归）
- `ui.py` — 用户交互（报警、暂停弹窗、debug 窗口）
- `tsumo19d.py` — 入口，主循环（仅自摸1/9序数牌和dong）
- `zi.py` — 字牌自摸/跳过（匹配 pics/zi* 则跳过，否则自摸）
- `auto_clicker.py` — 连点器（OCR检测卡住触发重启，5s间隔，连续5次check确认卡住后重启，失败自动重试，含先决条件判定）
- `speedhack.py` — CE加速模块（自动打开CE，OCR精确匹配firefox PID，设置5倍速；返回bool，含CE进程检测/关闭）
- `cloud_bottle.py` — 刷印章连点器（w 键暂停/恢复，暂停时悬停自摸坐标）
- `tools/mouse_pos.py` — 获取屏幕坐标的辅助工具（Tkinter 悬浮窗）
- `tools/threshold_test.py` — 阈值检测测试工具（Tkinter GUI）
- `pics/targets/` — 目标牌模板（触发自摸）
- `pics/distractors/` — 干扰牌模板（触发跳过）
- `pics/zi/` — 字牌模板（触发跳过：东南西北白中发）
- `pics/relaunch/` — 重连匹配模板（qyzz1.png, qyzz2.png, continue.png）
- `pics/net_reset.png` — 网络断开画面模板
- `pics/precondition.png` — 先决条件模板（tsumo19d 控制重试）
- `pics/pre1.png` — 先决条件模板1（zi/auto_clicker 使用）
- `pics/pre2.png` — 先决条件模板2（zi/auto_clicker 使用，任一匹配即通过）
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
- 每轮: 合并截屏(capture, 175×223) → 视图切片取牌面/分数 ROI → 卡住检测（与上轮截图比较，连续3次相同则悬停跳过按钮重截图，仍相同则播放10次警告音后触发重连(relaunch.run)；仅 DEBUG 打印重复次数） → 先决条件检测(tile_matcher.check_precondition, TM_CCOEFF_NORMED，不满足时重试） → ORB BFMatcher(best_match, 无重试一次出结果） → 网络断连检测（记录识别结果，连续5次相同时截图对比 net_reset.png；匹配则重连） → OCR 分数检测(score_reader.check_number） → 自摸/跳过
- 重连模块 `relaunch.py`：`run()` 时打印 `[HH:MM:SS]` 时刻，模块级 `RESTART_COUNT` / `LAST_RESTART` 追踪；依次新建标签页、匹配 qyzz 画面（静音）、匹配 continue 画面、匹配先决条件；DEBUG 模式打印匹配进度和「警告音 x/10」。全部成功后返回 True；任一步骤超限返回 False
- ORB nfeatures=200，检测器与 BFMatcher 在模块级缓存（`tile_matcher._ORB` / `tile_matcher._BF`），每圈不重复构造
- OCR 灰度图 8 倍放大 + 阈值180二值化后直出 Tesseract，PSM 7 + whitelist 0123456789/，分数大幅下降时连续两次一致即接受；诊断日志（不匹配详情/等待稳定）仅 DEBUG 打印
- `ui.alarm`: 5 × Beep(660Hz, 200ms) + PlaySound("SystemExclamation")，消息框确定继续/取消退出；所有报警均含 `ALARM_TIMEOUT` 秒超时自动关闭游戏窗口（1890, 27 停留1s后点击）并退出
- 重试只由先决条件控制：不满足则跳过本轮；牌面识别无重试
- `--debug` 可选：开启 Tkinter 调试窗口（`ui.setup_debug_window`，右下角固定，260×280，Consolas bold），判决后点击前更新实时信息（已运行时间/重启次数/上次重启/先决分数/OCR分数/牌面识别结果）
- 常规日志仅保留时间戳标注的关键事件：卡住确认（先决条件前的悬停重连）、网络断连匹配、重连触发流程、重连完成；其余诊断信息（牌面匹配特征、OCR 重试详情、匹配进度、分隔线等）均仅在 DEBUG 模式输出
- `Tesseract-OCR/`（已在 .gitignore）
- `pyproject.toml` 是唯一项目配置；无 formatter/linter 配置，格式自由

### auto_clicker 卡住检测
- 每轮截取 `_CHECK_REGION`(830,450)-(1025,600) 灰度图
- OCR值连续2次相同时，比较本轮与上一轮check区域匹配度（TM_CCOEFF_NORMED）
- 匹配度≥`PRECONDITION_THRESHOLD`(0.9) → check_count+1，否则归零
- check_count连续≥5 → 确认卡住，执行重启
- OCR值变化时全部归零

### speedhack 流程
- `restart_with_speedhack()` 封装循环：`do_restart()` 失败持续重试，成功后调用 `speedhack()`，失败则重新 `do_restart()`
- `do_restart()` 返回 bool：依次新建标签页、匹配 qyzz/continue/先决条件，失败打印日志返回 False，成功返回 True
- `speedhack()` 返回 bool：启动前调用 `kill_ce()`（sleep 1s）关闭已有 CE 进程（进程名 `cheatengine-x86_64-SSE4-AVX2.exe`）
- 步骤：tasklist 获取最大内存 firefox PID → 转8位hex → 命令行启动CE（`Cheat Engine.exe`，检测实际进程是否运行） → OCR识别进程列表（截屏区域 left=827） → 逐字符比对pid16精确匹配（无容差） → 页翻找（pagedown×3到底，pageup最多5次，每页重试2次，每次等待1s） → 点击Open → Enable Speedhack → Ctrl+A全选+Backspace清除+输入5 → 悬停1s → Apply → firefox回前台
