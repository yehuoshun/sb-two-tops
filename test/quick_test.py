"""
离线验证 — 无需游戏窗口，验证所有模块导入和基础逻辑

用法:
  python test/quick_test.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_imports():
    """测试所有模块导入"""
    print("=== 模块导入测试 ===")
    modules = [
        ("src.core.config", "Config"),
        ("src.core.recognizer", "Recognizer"),
        ("src.pages.base", "BasePage"),
        ("src.pages.home", "HomePage"),
        ("src.pages.dungeon", "DungeonSelectPage"),
        ("src.pages.dungeon", "ConfirmPage"),
        ("src.pages.battle", "BattlePage"),
        ("src.pages.battle", "SettlementPage"),
    ]
    for mod_name, cls_name in modules:
        try:
            mod = __import__(mod_name, fromlist=[cls_name])
            getattr(mod, cls_name)
            print(f"  ✅ {mod_name}.{cls_name}")
        except Exception as e:
            print(f"  ❌ {mod_name}.{cls_name}: {e}")
            return False
    return True


def test_config():
    """测试配置加载"""
    print("\n=== 配置加载测试 ===")
    from src.core.config import Config
    try:
        cfg = Config("config.json")
        print(f"  ✅ 窗口标题: {cfg.window_title}")
        print(f"  ✅ 基准分辨率: {cfg.scale}")
        print(f"  ✅ 点击等待: {cfg.post_click_wait_ms}ms")
        print(f"  ✅ 目标副本: {cfg.get('dungeon', 'target')}")
        print(f"  ✅ 最大次数: {cfg.get('dungeon', 'max_runs')}")
        return True
    except Exception as e:
        print(f"  ❌ 配置加载失败: {e}")
        return False


def test_recognizer():
    """测试识别器初始化"""
    print("\n=== 识别器测试 ===")
    from src.core.recognizer import Recognizer
    try:
        rec = Recognizer("templates")
        print(f"  ✅ 模板目录: {rec.templates_dir}")
        print(f"  ✅ 缓存: {len(rec._template_cache)} 个模板")
        return True
    except Exception as e:
        print(f"  ❌ 识别器初始化失败: {e}")
        return False


def test_page_classes():
    """测试页面类实例化"""
    print("\n=== 页面类测试 ===")
    from src.core.recognizer import Recognizer
    from src.pages.home import HomePage
    from src.pages.dungeon import DungeonSelectPage, ConfirmPage
    from src.pages.battle import BattlePage, SettlementPage

    rec = Recognizer("templates")
    cfg = {}
    pages = [
        ("HomePage", HomePage(rec, cfg)),
        ("DungeonSelectPage", DungeonSelectPage(rec, cfg)),
        ("ConfirmPage", ConfirmPage(rec, cfg)),
        ("BattlePage", BattlePage(rec, cfg)),
        ("SettlementPage", SettlementPage(rec, cfg)),
    ]
    for name, page in pages:
        print(f"  ✅ {name}: TEMPLATE={page.TEMPLATE}")
        if hasattr(page, "SEARCH_REGION"):
            print(f"       SEARCH_REGION={page.SEARCH_REGION}")
    return True


def test_template_files():
    """检查模板文件是否存在"""
    print("\n=== 模板文件检查 ===")
    from pathlib import Path
    templates = [
        "templates/battle/btn_exit.png",
        "templates/battle/btn_exit_v2.png",
    ]
    for t in templates:
        if Path(t).exists():
            print(f"  ✅ {t}")
        else:
            print(f"  ⚠️ {t} (不存在，需在 Windows 上采集)")
    return True


def main():
    passed = 0
    failed = 0

    tests = [
        test_imports,
        test_config,
        test_recognizer,
        test_page_classes,
        test_template_files,
    ]

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*40}")
    print(f"结果: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)