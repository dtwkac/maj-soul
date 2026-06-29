# maj-soul — 雀魂青云之志S4自动刷分脚本

## 技术栈
- **语言/运行环境**: Python ≥3.14（`.python-version` / `pyproject.toml`）
- **包管理器**: `uv`（`uv.lock` 锁定）
- **平台**: Windows only（`winsound`、`ctypes`、`keyboard`）

## 关键命令
```bash
uv sync                    # 安装依赖
uv run python main.py      # 运行主脚本
uv run python tools/mouse_pos.py        # 坐标捕获工具（右键退出）
uv run python tools/threshold_test.py   # 阈值检测测试工具
# 无测试 / 无 lint / 无 typecheck / 无 CI
```

## 提交规则
- **commit 前先同步 README.md 和 AGENTS.md**，确保代码变更对应的文档（常量值、快捷键、流程图等）已更新

## 项目结构
- `main.py` — 唯一生产入口，所有核心逻辑在此
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
- 主循环无限运行，`try/except BaseException` 包裹，异常后 5s 自动继续
- 每轮: 截图(90×153) → ORB BFMatcher(crossCheck, Hamming<50, 无特征点重试) → 最佳模板决策 → OCR 分数检测（分数大幅下降时连续两次一致即接受） → 自摸/跳过
- 忽略 `mahjong_auto_ORB_*.py`、`auto_ORB_*.py`、`mouse_tracker.py`（.gitignore 排除的旧文件）
- `pyproject.toml` 是唯一项目配置；无 formatter/linter 配置，格式自由
