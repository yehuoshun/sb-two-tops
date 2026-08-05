"""
sb-two-tops 页面检测测试

用法:
    python test_detect.py                          # 用默认截图测试
    python test_detect.py --image 截图.png          # 指定截图
    python test_detect.py --image 截图.png --debug   # 显示匹配位置
"""

import argparse
import sys
import os
from pathlib import Path

import cv2
import numpy as np


# 模板目录
TEMPLATES_DIR = Path(__file__).parent / "templates"

# 检测配置
DETECT_CONFIG = {
    "battle": {
        "features": ["battle_tanxian", "battle_dangqianlunci"],
        "search_box": (0.02, 0.20, 0.30, 0.18),  # x, y, w, h (相对比例)
        "threshold": 170,
        "match_threshold": 0.7,
    }
}


class PageDetector:
    """基于模板匹配的页面检测器"""

    def __init__(self, templates_dir=TEMPLATES_DIR):
        self.templates = {}
        self._load_templates(templates_dir)

    def _load_templates(self, templates_dir):
        """加载 templates/ 下所有 png 作为模板"""
        if not templates_dir.exists():
            print(f"[WARN] 模板目录不存在: {templates_dir}")
            return

        for png in sorted(templates_dir.rglob("*.png")):
            name = png.stem
            img = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                self.templates[name] = img
                print(f"  [OK] 加载模板: {name} ({img.shape})")
            else:
                print(f"  [ERR] 加载失败: {png}")

    def detect(self, frame, page_name):
        """检测指定页面是否匹配当前帧

        Args:
            frame: OpenCV BGR 图像
            page_name: 页面名称 (对应 DETECT_CONFIG 的 key)

        Returns:
            (bool, dict): 是否匹配, 详细匹配信息
        """
        config = DETECT_CONFIG.get(page_name)
        if not config:
            return False, {"error": f"未知页面: {page_name}"}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]

        # 二值化
        _, binary = cv2.threshold(gray, config["threshold"], 255, cv2.THRESH_BINARY)

        # 搜索区域
        sx = int(w * config["search_box"][0])
        sy = int(h * config["search_box"][1])
        sw = int(w * config["search_box"][2])
        sh = int(h * config["search_box"][3])
        search_area = binary[sy:sy+sh, sx:sx+sw]

        results = {}
        all_ok = True

        for feat_name in config["features"]:
            template = self.templates.get(feat_name)
            if template is None:
                results[feat_name] = {"found": False, "error": "模板未加载"}
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

            # 全图搜索（仅用于误报分析）
            full_result = cv2.matchTemplate(binary, template, cv2.TM_CCOEFF_NORMED)
            matches = np.where(full_result >= config["match_threshold"])
            match_count = len(set(zip(matches[0], matches[1])))
            results[feat_name]["match_count"] = match_count

        return all_ok, results


def main():
    parser = argparse.ArgumentParser(description="页面检测测试")
    parser.add_argument("--image", default=None, help="截图路径 (默认用测试目录下的截图)")
    parser.add_argument("--debug", action="store_true", help="显示匹配标记")
    parser.add_argument("--page", default="battle", help="检测的页面 (默认: battle)")
    args = parser.parse_args()

    # 确定截图路径
    if args.image:
        image_path = args.image
    else:
        # 默认找 test_capture.png
        candidates = [
            "test_capture.png",
            "screenshot.png",
            "capture.png",
            "../test_capture.png",
        ]
        image_path = None
        for c in candidates:
            if os.path.exists(c):
                image_path = c
                break
        if not image_path:
            print("[ERR] 未指定截图，且未找到默认截图文件")
            print("用法: python test_detect.py --image 你的截图.png")
            sys.exit(1)

    # 加载截图
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[ERR] 无法加载截图: {image_path}")
        sys.exit(1)

    h, w = frame.shape[:2]
    print(f"截图: {image_path} ({w}x{h})")
    print()

    # 加载模板
    print("模板加载:")
    detector = PageDetector()
    print()

    # 检测
    print(f"检测页面: {args.page}")
    print("-" * 50)
    matched, results = detector.detect(frame, args.page)

    for feat_name, info in results.items():
        if "error" in info:
            print(f"  [{feat_name}] {info['error']}")
            continue
        status = "✅" if info["found"] else "❌"
        print(f"  {status} {feat_name}: 置信度={info['confidence']:.4f}")
        print(f"     位置: ({info['position'][0]}, {info['position'][1]})")
        print(f"     全图匹配数: {info['match_count']}")

    print("-" * 50)
    if matched:
        print(f"  ✅ 判定为 {args.page} 页面")
    else:
        print(f"  ❌ 不是 {args.page} 页面")

    # Debug: 保存标记图
    if args.debug:
        debug = cv2.cvtColor(
            cv2.threshold(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                          170, 255, cv2.THRESH_BINARY)[1],
            cv2.COLOR_GRAY2BGR
        )
        config = DETECT_CONFIG[args.page]
        sx = int(w * config["search_box"][0])
        sy = int(h * config["search_box"][1])
        sw = int(w * config["search_box"][2])
        sh = int(h * config["search_box"][3])
        cv2.rectangle(debug, (sx, sy), (sx+sw, sy+sh), (0, 255, 255), 2)

        for feat_name, info in results.items():
            if info.get("found"):
                x, y = info["position"]
                template = detector.templates.get(feat_name)
                if template is not None:
                    th, tw = template.shape
                    cv2.rectangle(debug, (x, y), (x+tw, y+th), (0, 255, 0), 2)
                    cv2.putText(debug, f"{feat_name} {info['confidence']:.2f}",
                                (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        debug_path = "detect_debug.png"
        cv2.imwrite(debug_path, debug)
        print(f"\n调试图已保存: {debug_path}")


if __name__ == "__main__":
    main()