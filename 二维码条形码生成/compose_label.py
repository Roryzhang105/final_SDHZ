#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compose_label.py  –  把二维码、条形码叠到模板图指定位置

用法示例
--------
python compose_label.py template.jpg qr.png barcode.png \
    --qr-x 60  --qr-y 80   \
    --bc-x 60  --bc-y 320  \
    --output final_label.png
"""

import argparse
from pathlib import Path
from PIL import Image


def paste_with_alpha(base: Image.Image,
                     overlay: Image.Image,
                     pos: tuple[int, int]) -> None:
    """把 overlay 按透明度贴到 base 指定位置"""
    base.paste(overlay, pos, overlay)  # PIL 支持用自身 alpha 作为 mask


def main() -> None:
    parser = argparse.ArgumentParser(
        description="把二维码、条形码贴到模板图上")
    parser.add_argument("template", help="模板图路径")
    parser.add_argument("qr", help="二维码 PNG 路径")
    parser.add_argument("barcode", help="条形码 PNG 路径")
    parser.add_argument("--qr-x", type=int, default=80, help="二维码左上角 X 坐标")
    parser.add_argument("--qr-y", type=int, default=260, help="二维码左上角 Y 坐标")
    parser.add_argument("--bc-x", type=int, default=365, help="条形码左上角 X 坐标")
    parser.add_argument("--bc-y", type=int, default=30, help="条形码左上角 Y 坐标")
    parser.add_argument("-o", "--output", default="composed.png",
                        help="输出文件名")
    args = parser.parse_args()

    # 1) 打开图片
    template = Image.open(args.template).convert("RGBA")
    qr_img = Image.open(args.qr).convert("RGBA")
    bc_img = Image.open(args.barcode).convert("RGBA")

    # 2) 贴图
    paste_with_alpha(template, qr_img, (args.qr_x, args.qr_y))
    paste_with_alpha(template, bc_img, (args.bc_x, args.bc_y))

    # 3) 保存
    out_path = Path(args.output)
    template.save(out_path)
    print(f"✅ 已输出 {out_path.resolve()}")


if __name__ == "__main__":
    main()
