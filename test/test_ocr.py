"""
OCR 识别测试 — 验证 RapidOCR 能否识别各副本名

用法:
    python test/test_ocr.py                         # 用默认截图
    python test/test_ocr.py --image 截图.png          # 指定截图
    python test/test_ocr.py --image 截图.png --debug  # 显示所有识别结果

输出:
    ✅ 每个目标副本名识别到 → 坐标 + 置信度
    ❌ 未识别的目标副本名
    ⚠ 全部识别结果（--debug）
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 目标副本名（按出现顺序）
TARGETS = ["探险", "调停", "避险", "驱逐", "驱离", "护送", "追缉", "扼守"]

# 辅助检查项（非目标，但能帮助判断页面状态）
EXTRA_TARGETS = ["委托", "灾厄", "铜币", "角色经验", "武器经验", "角色突破材料", "武器突破材料"]


def load_image(path):
    """加载图片，支持路径或 bytes"""
    import cv2
    img = cv2.imread(str(path))
    if img is None:
        print(f"❌ 无法读取图片: {path}")
        sys.exit(1)
    return img


def test_ocr(image_path, debug=False):
    from rapidocr_onnxruntime import RapidOCR

    print(f"📷 截图: {image_path}")
    print()

    engine = RapidOCR()
    img = load_image(image_path)
    result, elapse = engine(img)

    if not result:
        print("❌ OCR 未识别到任何文字")
        return False

    print(f"📝 OCR 识别到 {len(result)} 个文本块 (耗时 {elapse:.2f}s)")
    print()

    # 统计目标匹配
    found = {}
    detailed = []

    for box, text, score in result:
        text = text.strip()
        if not text:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        cx = int(sum(xs) / len(xs))
        cy = int(sum(ys) / len(ys))

        detailed.append((text, cx, cy, score))

        for t in TARGETS + EXTRA_TARGETS:
            if t in text and t not in found:
                found[t] = (cx, cy, score)

    # 输出目标副本匹配结果
    print("=== 目标副本 ===")
    all_ok = True
    for t in TARGETS:
        if t in found:
            cx, cy, score = found[t]
            status = "✅" if score >= 0.3 else "⚠️ 低置信度"
            print(f"  {status} {t} @ ({cx:>4}, {cy:>4}) 置信度={score:.3f}")
        else:
            print(f"  ❌ {t} — 未识别")
            all_ok = False

    print()
    print("=== 辅助信息 ===")
    for t in EXTRA_TARGETS:
        if t in found:
            cx, cy, score = found[t]
            print(f"  ℹ️  {t} @ ({cx:>4}, {cy:>4}) 置信度={score:.3f}")

    # debug 模式: 输出所有识别结果
    if debug:
        print()
        print("=== 全部识别结果 ===")
        for text, cx, cy, score in sorted(detailed, key=lambda x: -x[3]):
            print(f"  \"{text}\" @ ({cx:>4}, {cy:>4}) 置信度={score:.3f}")

    print()
    if all_ok:
        print("✅ 全部目标副本识别成功")
    else:
        print(f"❌ 部分目标副本未识别")
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR 识别测试")
    parser.add_argument("--image", default=None, help="截图路径")
    parser.add_argument("--debug", action="store_true", help="显示所有识别结果")
    args = parser.parse_args()

    # 如果没有指定图片，尝试默认路径
    image_path = args.image
    if image_path is None:
        default = PROJECT_ROOT / "test" / "screenshot.png"
        if default.exists():
            image_path = str(default)
        else:
            print("❌ 未指定截图，请用 --image 指定")
            print("使用示例: python test/test_ocr.py --image 截图.png")
            sys.exit(1)

    ok = test_ocr(image_path, args.debug)
    sys.exit(0 if ok else 1)