# 开发进度 — sb-two-tops

> 最后更新: 2026-08-04

## 完成情况

### ✅ Phase 1：基础框架（已完成）
- PrintWindow 后台截图 (screenshot.py)
- OpenCV 模板匹配 (recognizer.py)
- PostMessage 后台点击/键盘 (clicker.py)
- 页面识别器基类 + 各页面桩 (pages/)
- 主循环 + 状态管理 (main.py)
- 配置管理 (config.py)

### 🚧 Phase 2：模板采集 + 流程联调（进行中）

#### 已修复的问题
- `cv2 DLL load failed` — 32-bit Python 安装了 64-bit opencv-python，重装解决
- `PYTHONPATH` 污染 — 系统环境变量 `E:\DevelopmentEnvironment\python-packages` 抢了 venv 优先级，需删掉
- `EnumWindows LPARAM` 传参错误 — 传了 Python list 而非整数，改用 `self._hwnds` 存储
- 5 个页面方法缺 `self` 参数 — 全部补全 (home, dungeon, battle)
- 所有 PyCharm 零警告已达成

#### 已实现的功能
- 战斗页检测代码：`TEMPLATE + SEARCH_REGION` 模式，限定左上角 200x200 搜索
- 模板裁剪脚本：`test/crop_template.py` — 交互式框选
- 匹配验证脚本：`test/test_match.py` — 测试模板匹配效果
- 战斗页模板：`templates/battle/btn_exit.png` (12x33)

#### 待完成
- [ ] **战斗页检测未经测试** — 代码已写但未在 Windows 上运行验证（明天第一件事）
- [ ] 采集主城/副本选择/确认/结算页模板
- [ ] 填入各页面点击坐标
- [ ] 跑通全流程

### ⏳ Phase 3：打包（未开始）
- PyInstaller 编译为 sihost.exe
- 使用文档

## 环境问题

### Windows 开发环境
- **Python**: 3.13 32-bit — 建议换 64-bit
- **pip 配置**: 已删除 `global.target`，包装到 venv
- **PYTHONPATH**: 系统变量 `E:\DevelopmentEnvironment\python-packages` 需手动删除
- **GitHub**: 网络隔离，无法直接 git push/pull，需通过 API 推送

### 习惯
- 修改文件后必须汇报改了什么
- 删除/大幅修改前先询问
- 不允许说"建议""好的""没问题"等废话