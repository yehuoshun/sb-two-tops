"""
模板裁剪 — 从截图中框选特征区域，保存为模板

用法:
  1. 先截取页面全屏图: python test/capture_templates.py
  2. 裁剪模板:      python test/crop_template.py

操作:
  - 鼠标框选特征区域，按 SPACE/ENTER 确认
  - 按 R 重新选择，按 ESC 跳过
  - 输入模板名称保存
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2


def main():
    # 列出已有全屏截图
    templates_dir = "templates"
    os.makedirs(templates_dir, exist_ok=True)

    fulls = [f for f in os.listdir(templates_dir) if f.endswith("_full.png")]
    if not fulls:
        print("❌ 没有找到 templates/*_full.png，请先运行 test/capture_templates.py")
        return

    print("可用的全屏截图:")
    for i, f in enumerate(fulls):
        print(f"  [{i}] {f}")

    idx = input("\n选择编号: ").strip()
    if not idx.isdigit() or int(idx) >= len(fulls):
        print("❌ 无效选择")
        return

    img_path = os.path.join(templates_dir, fulls[int(idx)])
    img = cv2.imread(img_path)
    if img is None:
        print(f"❌ 无法读取: {img_path}")
        return

    print("\n操作指南:")
    print("  🖱️  框选特征区域")
    print("  ␣ SPACE/ENTER → 确认裁剪")
    print("  R → 重新选择")
    print("  ESC → 跳过")
    print("  按 q 退出\n")

    while True:
        roi = cv2.selectROI(f"裁剪 - {fulls[int(idx)]}", img, showCrosshair=True)
        cv2.destroyAllWindows()

        if roi[2] == 0 or roi[3] == 0:
            print("  ⏭️  跳过")
            break

        x, y, w, h = [int(v) for v in roi]
        cropped = img[y:y + h, x:x + w]

        # 显示裁剪结果
        cv2.imshow("裁剪结果 (按 SPACE 保存 / R 重选 / ESC 取消)", cropped)
        key = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if key == 27:  # ESC
            print("  ⏭️  跳过")
            break
        elif key == ord('r') or key == ord('R'):
            continue
        else:
            name = input("模板名称 (如 btn_exit): ").strip()
            if not name:
                name = "template"
            save_path = os.path.join(templates_dir, f"{name}.png")
            cv2.imwrite(save_path, cropped)
            print(f"  ✅ 已保存: {save_path} ({w}x{h})")
            print(f"  坐标: x={x}, y={y}, w={w}, h={h}")
            break


if __name__ == "__main__":
    main()