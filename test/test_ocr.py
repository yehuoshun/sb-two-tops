"""
OCR 识别测试 — 对游戏截图进行 OCR，验证各副本名识别效果

用法:
    python test/test_ocr.py                        # 截图并识别
    python test/test_ocr.py --image 截图.png         # 指定截图
    python test/test_ocr.py --debug                  # 显示所有识别结果
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 目标副本名
TARGETS = ["探险", "调停", "避险", "驱逐", "驱离", "护送", "追缉", "扼守"]
EXTRA_TARGETS = ["委托", "灾厄", "铜币", "角色经验", "武器经验", "角色突破材料", "武器突破材料"]


def _capture_live():
    """用游戏截图模块实时截图"""
    from src.core.config import Config
    from src.core.screenshot import Screenshot

    cfg = Config(str(PROJECT_ROOT / "config.json"))
    ss = Screenshot(window_title=cfg.window_title, window_class=cfg.window_class)
    if not ss.find_window():
        print("❌ 未找到游戏窗口，请确认游戏已启动")
        sys.exit(1)

    img = ss.capture()
    if img is None:
        print("❌ 截图失败")
        sys.exit(1)
    print(f"📷 实时截图成功 ({ss.width}x{ss.height})")
    return img


def _load_image(path):
    import cv2
    img = cv2.imread(str(path))
    if img is None:
        print(f"❌ 无法读取图片: {path}")
        sys.exit(1)
    return img


def test_ocr(image, debug=False):
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    result, _ = engine(image)

    if not result:
        print("❌ OCR 未识别到任何文字")
        return False

    print(f"📝 OCR 识别到 {len(result)} 个文本块\n")

    # 匹配目标
    found = {}
    for box, text, score in result:
        text = text.strip()
        if not text:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        cx = int(sum(xs) / len(xs))
        cy = int(sum(ys) / len(ys))

        for t in TARGETS + EXTRA_TARGETS:
            if t in text and t not in found:
                found[t] = (cx, cy, score)

    # 目标副本
    print("=== 目标副本 ===")
    all_ok = True
    for t in TARGETS:
        if t in found:
            cx, cy, s = found[t]
            flag = "✅" if s >= 0.3 else "⚠️ 低置信度"
            print(f"  {flag} {t} @ ({cx:>4}, {cy:>4}) 置信度={s:.3f}")
        else:
            print(f"  ❌ {t} — 未识别")
            all_ok = False

    # 辅助信息
    print("\n=== 辅助信息 ===")
    for t in EXTRA_TARGETS:
        if t in found:
            cx, cy, s = found[t]
            print(f"  ℹ️  {t} @ ({cx:>4}, {cy:>4}) 置信度={s:.3f}")

    # 全部结果
    if debug:
        all_results = [(text, cx, cy, score) for box, text, score in result
                       if (text := text.strip())]
        all_results.sort(key=lambda x: -x[3])
        print("\n=== 全部识别结果 ===")
        for text, cx, cy, score in all_results:
            print(f"  \"{text}\" @ ({cx:>4}, {cy:>4}) 置信度={score:.3f}")

    print()
    print("✅ 全部目标副本识别成功" if all_ok else "❌ 部分目标副本未识别")
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR 识别测试")
    parser.add_argument("--image", default=None, help="截图路径，不指定则实时截图")
    parser.add_argument("--debug", action="store_true", help="显示所有识别结果")
    args = parser.parse_args()

    img = _load_image(args.image) if args.image else _capture_live()
    ok = test_ocr(img, args.debug)
    sys.exit(0 if ok else 1)