"""
调试可视化 — 在截图上叠加模板匹配结果，验证检测效果

用法:
  python test/debug_match.py [截图路径] [模板路径]

示例:
  python test/debug_match.py test_capture.png templates/battle/btn_exit_v2.png

输出:
  debug_match.png — 标记了匹配位置的截图（绿色框=高置信度，黄色=中等，红色=低）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np


def main():
    if len(sys.argv) < 3:
        print("用法: python test/debug_match.py <截图> <模板>")
        print("示例: python test/debug_match.py test_capture.png templates/battle/btn_exit_v2.png")
        return

    screenshot_path = sys.argv[1]
    template_path = sys.argv[2]

    screenshot = cv2.imread(screenshot_path)
    if screenshot is None:
        print(f"❌ 无法读取截图: {screenshot_path}")
        return

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"❌ 无法读取模板: {template_path}")
        return

    h, w = screenshot.shape[:2]
    th, tw = template.shape
    print(f"截图: {w}x{h}  模板: {tw}x{th}")

    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    print(f"\n最高置信度: {max_val:.4f}  位置: ({max_loc[0]}, {max_loc[1]})")

    # 绘制所有匹配位置（不同阈值用不同颜色）
    output = screenshot.copy()
    thresholds = [(0.9, (0, 255, 0), "高"), (0.8, (0, 255, 255), "中"), (0.7, (0, 0, 255), "低")]

    for threshold, color, label in thresholds:
        locations = np.where(result >= threshold)
        count = len(locations[0])
        if count > 0:
            print(f"阈值 ≥ {threshold:.1f} ({label}): {count} 个位置")
            for pt in zip(*locations):
                cv2.rectangle(output, (pt[1], pt[0]), (pt[1] + tw, pt[0] + th), color, 2)
                if count <= 20:  # 太多时不标文字
                    cv2.putText(output, f"{result[pt[0], pt[1]]:.2f}",
                                (pt[1], pt[0] - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # 标出最佳匹配
    cv2.rectangle(output, max_loc, (max_loc[0] + tw, max_loc[1] + th), (0, 255, 0), 3)
    cv2.putText(output, f"BEST: {max_val:.3f}",
                (max_loc[0], max_loc[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    out_path = "debug_match.png"
    cv2.imwrite(out_path, output)
    print(f"\n✅ 可视化结果已保存: {out_path}")
    print("   绿色框=置信度≥0.9  黄色=≥0.8  红色=≥0.7")


if __name__ == "__main__":
    main()