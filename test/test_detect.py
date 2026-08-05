"""
sb-two-tops 战斗页面检测测试（自包含，无需外部截图）

用法:
    python test/test_detect.py
    python test/test_detect.py --debug   # 保存调试图

测试内容:
    1. 模板加载验证
    2. 合成图像匹配测试（将模板嵌入黑底图）
    3. 噪声图像误报测试（确保不误匹配）
"""

import sys
import math
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

DETECT_CONFIG = {
    "battle": {
        "features": ["battle_tanxian", "battle_dangqianlunci"],
        "search_box": (0.02, 0.20, 0.30, 0.18),
        "threshold": 170,
        "match_threshold": 0.7,
    }
}


class PageDetector:
    def __init__(self, templates_dir=TEMPLATES_DIR):
        self.templates = {}
        self._load_templates(templates_dir)

    def _load_templates(self, templates_dir):
        if not templates_dir.exists():
            return
        for png in sorted(templates_dir.rglob("*.png")):
            name = png.stem
            img = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                self.templates[name] = img

    def detect(self, frame, page_name):
        config = DETECT_CONFIG.get(page_name)
        if not config:
            return False, {}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]
        _, binary = cv2.threshold(gray, config["threshold"], 255, cv2.THRESH_BINARY)

        sx = int(w * config["search_box"][0])
        sy = int(h * config["search_box"][1])
        sw = int(w * config["search_box"][2])
        sh = int(h * config["search_box"][3])
        search_area = binary[sy:sy + sh, sx:sx + sw]

        results = {}
        all_ok = True

        for feat_name in config["features"]:
            template = self.templates.get(feat_name)
            if template is None:
                results[feat_name] = {"found": False, "error": "no_template"}
                all_ok = False
                continue

            result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            found = max_val >= config["match_threshold"]
            results[feat_name] = {
                "found": found,
                "confidence": float(max_val),
                "position": (sx + max_loc[0], sy + max_loc[1]),
            }
            if not found:
                all_ok = False

        return all_ok, results


def test_templates_load():
    print("测试 1: 模板加载...", end=" ")
    detector = PageDetector()
    expected = {"battle_tanxian", "battle_dangqianlunci"}
    loaded = set(detector.templates.keys())
    missing = expected - loaded
    if missing:
        print(f"❌ 缺少模板: {missing}")
        return False
    print(f"✅ ({len(loaded)} 个模板)")
    for name, img in detector.templates.items():
        print(f"     {name}: {img.shape}")
    return True


def test_synthetic_match():
    print("测试 2: 合成图像匹配...", end=" ")
    detector = PageDetector()
    if not detector.templates:
        print("⏭ 跳过（无模板）")
        return True

    # 构建一张 1920x1080 黑底图
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # 搜索区域
    sx = int(1920 * DETECT_CONFIG["battle"]["search_box"][0])
    sy = int(1080 * DETECT_CONFIG["battle"]["search_box"][1])

    # 把所有模板都贴到搜索区域内，模拟真实场景
    for feat_name in DETECT_CONFIG["battle"]["features"]:
        tpl = detector.templates.get(feat_name)
        if tpl is None:
            print(f"⏭ 跳过（无 {feat_name} 模板）")
            return True
        th, tw = tpl.shape
        # 按顺序排列，不重叠
        px = sx + 50 + (200 if feat_name != DETECT_CONFIG["battle"]["features"][0] else 0)
        py = sy + 50
        frame[py:py + th, px:px + tw] = cv2.cvtColor(tpl, cv2.COLOR_GRAY2BGR)

    # 检测
    matched, results = detector.detect(frame, "battle")
    if not matched:
        print("❌ 未检测到嵌入的模板")
        return False

    for name, info in results.items():
        print(f"\n     {name}: 置信度={info['confidence']:.4f} ✅")
    return True


def test_noise_false_positive():
    print("测试 3: 噪声误报检测...", end=" ")
    detector = PageDetector()
    if not detector.templates:
        print("⏭ 跳过（无模板）")
        return True

    # 纯随机噪声图
    for seed in [1, 42, 99]:
        rng = np.random.RandomState(seed)
        noise = rng.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
        matched, results = detector.detect(noise, "battle")
        if matched:
            print(f"❌ 随机噪声被误判为匹配 (seed={seed})")
            return False
    print("✅ 噪声未误判")
    return True


def test_small_template_wont_match():
    print("测试 4: 小尺寸模板不误匹配...", end=" ")
    detector = PageDetector()
    if not detector.templates:
        print("⏭ 跳过（无模板）")
        return True

    # 纯色灰度图（不应该匹配到任何文字模板）
    for color in [0, 64, 128, 200]:
        solid = np.full((1080, 1920, 3), color, dtype=np.uint8)
        matched, _ = detector.detect(solid, "battle")
        if matched:
            print(f"❌ 纯色图被误判 (color={color})")
            return False
    print("✅ 纯色未误判")
    return True


def all_tests():
    tests = [
        ("模板加载", test_templates_load),
        ("合成匹配", test_synthetic_match),
        ("误报检测", test_noise_false_positive),
        ("纯色防误判", test_small_template_wont_match),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            if fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  💥 异常: {e}")
            failed += 1
        print()

    total = passed + failed
    print(f"{'='*40}")
    print(f"结果: {passed}/{total} 通过", end="")
    if failed == 0:
        print(" ✅")
    else:
        print(f" ❌ ({failed} 失败)")
    return failed == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="sb-two-tops 页面检测测试")
    parser.add_argument("--debug", action="store_true", help="保存调试图")
    args = parser.parse_args()

    ok = all_tests()
    sys.exit(0 if ok else 1)