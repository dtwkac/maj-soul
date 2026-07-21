# 雀魂青云之志S4自动刷分脚本

1920x1080 分辨率下自动识别牌面、匹配目标牌、点击自摸/跳过的 Python 脚本。

## 入口文件

| 文件 | 用途 |
|------|------|
| `tsumo19d.py` | 自摸特殊牌（1m/9m/1p/9p/9s/dong），其余跳过 |
| `auto_clicker.py` | 无条件自摸连点器，OCR检测卡住自动重启+CE加速 |
| `zi.py` | 字牌自摸/跳过，通过"文房四宝"完成魂牌染色 |
| `cloud_bottle.py` | 刷印章连点器：按 w 开始/停止，手动控制摸牌，通过"云朵药水"精确添加印章 |

## 环境要求

- Python >=3.14
- Windows（`winsound`、`ctypes`、`keyboard` 等 Windows 特有库）
- Tesseract-OCR 5.4.0+
- 屏幕分辨率 **1920x1080**，游戏窗口全屏
- Cheat Engine 放置于项目目录下 `Cheat Engine/` 文件夹

### 安装依赖

```bash
uv sync
```

手动安装 Tesseract-OCR：
https://github.com/UB-Mannheim/tesseract/releases
7-Zip解压后重命名为 Tesseract-OCR

## 使用

```bash
uv run python tsumo19d.py              # 静默运行
uv run python tsumo19d.py --debug      # 显示调试信息窗口
uv run python auto_clicker.py          # 连点器（自动重启）
uv run python auto_clicker.py --debug  # 连点器（带调试日志）
uv run python zi.py                    # 字牌自摸/跳过
uv run python zi.py --debug            # 字牌自摸/跳过（带调试日志）
uv run python cloud_bottle.py          # 刷印章连点器（w 键开始/停止）
```

运行后弹出确认窗口，点击"确定"开始运行，"取消"则安全退出。

### 控制

| 按键 | 功能 |
|------|------|
| `Ctrl+.` | tsumo19d/zi 暂停（弹窗确定继续 / 取消退出） |
| `Ctrl+.` | auto_clicker 暂停/恢复（非阻塞） |
| `w` | cloud_bottle 开始/停止 |
| 关闭控制台窗口 | 停止程序 |

## 项目结构

```
tsumo19d.py          # 入口1：自摸特殊牌，其余跳过
auto_clicker.py      # 入口2：无条件自摸连点器
zi.py                # 入口3：字牌自摸/跳过（文房四宝魂牌染色）
cloud_bottle.py      # 入口4：刷印章连点器（w 键开始/停止，云朵药水）

common/              # 共享模块
  consts.py          # 全部常量（坐标、阈值、路径）
  capture.py         # 截屏（mss，合并截取牌面+分数区域）
  tile_matcher.py    # 牌型匹配（ORB特征+BFMatcher，模板加载）+ 先决条件检测
  score_reader.py    # 分数检测（Tesseract OCR，含debug截图）
  actions.py         # 点击动作（自摸/跳过）
  relaunch.py        # 重连模块（卡住时刷新游戏并等待回归）
  ui.py              # 用户交互（报警、暂停弹窗、debug窗口）
  speedhack.py       # CE加速模块（自动打开CE，OCR匹配firefox PID，设置5倍速）

tools/               # 辅助工具
  mouse_pos.py       # 坐标捕获工具
  threshold_test.py  # 阈值检测测试工具
  tile_capture.py    # 牌面截图工具

pics/
  targets/           # 目标牌模板（触发自摸）：1m, 1p, 9m, 9p, 9s, dong
  distractors/       # 干扰牌模板（触发跳过）：7p, 7s
  zi/                # 字牌模板（触发跳过）：东南西北白中发
  relaunch/          # 重连匹配模板：qyzz1.png, qyzz2.png, continue.png
  net_reset.png      # 网络断开画面模板
  precondition.png   # 先决条件模板（tsumo19d控制重试）
  pre1.png           # 先决条件模板1（zi/auto_clicker）
  pre2.png           # 先决条件模板2（zi/auto_clicker，任一匹配即通过）
```

## tsumo19d 原理

1. **截图** - 每轮合并截取牌面+分数区域（175x223），mss 直接返回 ndarray 后切片取出两个 ROI
2. **卡住检测** - 每轮比较当前牌面截图与上一轮，连续 3 次相同则悬停跳过按钮重截图，仍相同则播放 10 次警告音后触发重连
3. **先决条件检测** - `cv2.matchTemplate(TM_CCOEFF_NORMED)` 匹配 `precondition.png`，不满足时跳过本轮
4. **ORB 特征匹配** - 对牌面 ROI 提取 ORB 特征点，与预设模板 BFMatcher 交叉匹配，取好匹配数最多者
5. **网络断连检测** - ORB 识别结果连续 5 次相同时截图对比 `net_reset.png`，匹配则重连
6. **决策** - 最佳模板匹配数 >= 阈值(20) 且是目标牌 -> 自摸；否则跳过
7. **分数检测** - Tesseract OCR 读取分数，低于 `NUM_ALARM(81)` 时报警
8. **连点** - 自摸后连点屏幕中心跳过结算页面

## auto_clicker 原理

1. **启动** - 自动执行重启+CE加速，等待游戏就绪
2. **循环点击** - 0.2s 间隔持续点击自摸按钮（带随机偏移 +-5px）
3. **卡住检测** - 每 5s 截取画面区域，与上一轮匹配度>=0.99 连续 5 次 -> 确认卡住，自动重启+加速
4. **异常处理** - 重启失败持续重试，直到成功

## 阈值说明

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `THRESHOLD_DEFAULT` | 20 | 全局匹配数阈值 |
| `NUM_ALARM` | 81 | 分数低于该值时报警 |
| `RETRY_LIMIT` | 10 | OCR 分数异常/重连匹配重试上限 |
| `LOOP_SLEEP` | 1.0 | 每轮循环间隔（秒） |
| `SLEEP_INTERVAL` | 0.2 | 检测/重试刷新间隔（秒） |
| `PRECONDITION_THRESHOLD` | 0.9 | 先决条件匹配阈值（TM_CCOEFF_NORMED） |
| `RELAUNCH_THRESHOLD` | 0.9 | 重连画面匹配阈值 |
| `NET_RESET_THRESHOLD` | 0.9 | 网络断连画面匹配阈值 |

## 坐标配置

所有坐标基于 **1920x1080** 全屏：

| 常量 | 坐标 | 说明 |
|------|------|------|
| `TILE_REGION` | (450, 885, 90, 140) | 牌面截图区域 (left, top, width, height) |
| `NUM_REGION` | (365, 805, 125, 30) | 分数数字区域 |
| `CENTER` | (960, 540) | 屏幕中心（连点/鼠标复位） |
| `TSUMO_BTN` | (1200, 815) | 自摸按钮 |
| `SKIP_BTN` | (500, 950) | 跳过按钮 |
| `RELAUNCH_QYZZ_REGION` | [(1635, 600, 110, 100), (1635, 720, 110, 100)] | qyzz 检测区域（多区域） |
| `RELAUNCH_CONTINUE_REGION` | (795, 860, 330, 90) | continue 检测区域 |
| `RELAUNCH_PRECOND_REGION` | (475, 885, 35, 20) | 重连完成先决条件检测区域 |
| `NET_RESET_REGION` | (645, 405, 630, 360) | 网络断连检测区域 |

## 详细流程（tsumo19d）

```
+--------------+
| 加载模板      |  读取 targets/ 和 distractors/，
| 提取特征点    |  用 ORB 提取特征描述子
+-------+------+
        |
+-------v------+
| 弹窗确认      |  点击确认后开始运行
+-------+------+
        |
+-------v------+  --- 循环开始 ---
| 鼠标移至中心  |  (960,540)
+--------------+
| 合并截屏      |  175x223 (mss), 切片取牌面 + 分数 ROI
+--------------+
| 卡住检测      |  与上一轮截图比较, 连续3次时悬停
|              |  跳过按钮重截图; 仍相同则播放10次警告音后重连
+--------------+
| 先决条件检测  |  TM_CCOEFF_NORMED 匹配
|              |  不满足 -> 跳过本轮 (重试)
+--------------+
| ORB 特征匹配  |  对所有模板计算好匹配数, 取最高者
|              |  无重试, 一次出结果
+--------------+
| 网络断连检测  |  记录识别结果, 连续5次相同时
|              |  截图对比 net_reset.png; 匹配则重连
+--------------+
| OCR 读取分数  |  格式 abc/{total}, 2倍放大+Otsu二值化
|              |  分数大幅下降时等待稳定 (连续两次相同)
|              |  < NUM_ALARM -> 报警
+--------------+
| 决策          |  最佳模板是目标 且 匹配数>=阈值(20)
|              |  -> 自摸        -> 跳过
+-------+------+  +-------+------+
        |                   |
        | 1. 移到自摸按钮    | 1. 移到跳过按钮
        | 2. 点击(随机偏移)  | 2. 点击
        | 3. 连点屏幕中心    | 3. 鼠标复位中心
        +-------------------+
        |
      休眠 1.0 秒 -> 循环继续
```
