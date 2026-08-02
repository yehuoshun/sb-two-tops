"""模板采集工具 — 在 Windows 上运行，截取各页面特征图"""

import sys
import time
from pathlib import Path

# 在 Windows 上运行时导入
try:
    from src.capturer import Capturer
    import cv2
    import numpy as np
    HAS_WIN = True
except ImportError:
    HAS_WIN = False


def main():
    if not HAS_WIN:
        print("此工具需要在 Windows 上运行")
        print("运行方式: python -m src.collect_templates")
        sys.exit(1)

    cap = Capturer()
    if not cap.find_game_window():
        print("未找到游戏窗口，请确保游戏正在运行")
        sys.exit(1)

    base = Path("templates")
    print("=== 模板采集工具 ===")
    print("按 ENTER 截取当前画面，输入状态名保存为模板")
    print("输入 q 退出")
    print()

    while True:
        cmd = input("> ").strip()
        if cmd.lower() == "q":
            break

        if cmd == "":
            # 截图预览
            img = cap.capture()
            if img is None:
                print("截图失败")
                continue
            cv2.imshow("Preview", cv2.cvtColor(img, cv2.COLOR_BGRA2BGR))
            cv2.waitKey(1)
            print("截图已捕获，输入状态名保存 (如 main_city, dungeon_enter, confirm 等)")
            continue

        # 输入状态名，保存模板
        state_name = cmd.replace(" ", "_").lower()
        img = cap.capture()
        if img is None:
            print("截图失败")
            continue

        # 保存到 templates/<state_name>/
        save_dir = base / state_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # 计算文件名序号
        existing = list(save_dir.glob("*.png"))
        idx = len(existing) + 1
        save_path = save_dir / f"{idx:02d}.png"

        cv2.imwrite(str(save_path), cv2.cvtColor(img, cv2.COLOR_BGRA2BGR))
        print(f"已保存: {save_path}")

        # 可选裁剪区域
        print("如需裁剪区域，输入 x,y,w,h (留空表示整张)")
        crop = input("  crop> ").strip()
        if crop:
            try:
                x, y, w, h = map(int, crop.split(","))
                cropped = img[y:y+h, x:x+w]
                crop_path = save_dir / f"{idx:02d}_crop.png"
                cv2.imwrite(str(crop_path), cv2.cvtColor(cropped, cv2.COLOR_BGRA2BGR))
                print(f"已保存裁剪版: {crop_path}")
            except:
                print("裁剪格式错误，跳过")

    cv2.destroyAllWindows()
    cap.close()
    print("采集完成")


if __name__ == "__main__":
    main()