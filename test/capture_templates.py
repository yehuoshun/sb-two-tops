"""
模板采集 — 捕获各页面的全屏截图，用于后续裁剪特征模板

用法:
  python test/capture_templates.py

输出:
  templates/home_full.png      — 主城页面截图
  templates/dungeon_full.png   — 副本选择页面截图
  templates/confirm_full.png   — 确认进入页面截图
  templates/battle_full.png    — 战斗页面截图
  templates/settlement_full.png — 结算页面截图

操作:
  - 按 SPACE 捕获当前页面截图
  - 按 S 跳过当前页面
  - 按 Q 退出
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
from src.core.screenshot import Screenshot

PAGES = [
    ("home", "主城"),
    ("dungeon", "副本选择"),
    ("confirm", "确认进入"),
    ("battle", "战斗中"),
    ("settlement", "结算"),
]


def main():
    cap = Screenshot("二重螺旋")
    if not cap.find_window():
        print("❌ 未找到游戏窗口")
        return False

    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    os.makedirs(templates_dir, exist_ok=True)

    print("=" * 50)
    print("模板采集工具")
    print("=" * 50)
    print("操作指南:")
    print("  SPACE → 捕获当前页面截图")
    print("  S     → 跳过当前页面")
    print("  Q     → 退出")
    print("=" * 50)

    captured = []
    for name, desc in PAGES:
        print(f"\n📸 等待 {desc} 页面 ({name})...")
        print(f"   切换到游戏窗口的「{desc}」页面，然后按 SPACE 捕获")

        while True:
            key = input("   [SPACE=捕获 / S=跳过 / Q=退出] ").strip().lower()
            if key == "":
                # SPACE = 空输入
                img = cap.capture()
                if img is None:
                    print("   ❌ 截图失败，重试")
                    continue
                path = os.path.join(templates_dir, f"{name}_full.png")
                cv2.imwrite(path, img)
                print(f"   ✅ 已保存: {path} ({img.shape[1]}x{img.shape[0]})")
                captured.append(name)
                break
            elif key == "s":
                print(f"   ⏭️ 跳过 {desc}")
                break
            elif key == "q":
                print("   👋 退出")
                break
            else:
                print("   无效输入，请按 SPACE / S / Q")

        if key == "q":
            break

    print(f"\n📊 采集完成: {len(captured)}/{len(PAGES)} 个页面")
    if captured:
        print(f"   已采集: {', '.join(captured)}")
        print(f"\n下一步: 运行 python test/crop_template.py 裁剪特征模板")

    return True


if __name__ == "__main__":
    main()