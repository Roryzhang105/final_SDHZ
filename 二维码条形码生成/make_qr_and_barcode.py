#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_qr_and_barcode.py

• 生成 200×200 px 透明背景二维码  
• 生成 400×100 px 条形区 + 数字区，总高 140 px，
    - 数字使用微软雅黑、字号 35、字间距 10
    - 数字紧贴条形码，透明背景

用法:
    python make_qr_and_barcode.py "<URL>"

依赖:
    pip install qrcode[pil] python-barcode Pillow
"""

import re
import sys
from pathlib import Path

import qrcode
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont


def make_qr(url: str, out_path: Path, size: int = 240) -> None:
    """生成 200×200 透明背景二维码"""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # 将白色背景设为透明
    datas = [
        (255, 255, 255, 0) if (r > 250 and g > 250 and b > 250) else (r, g, b, 255)
        for (r, g, b, *_) in img.getdata()
    ]
    img.putdata(datas)

    img = img.resize((size, size), Image.NEAREST)
    img.save(out_path)


def make_barcode(code: str,
                 out_path: Path,
                 bar_w: int = 400,
                 bar_h: int = 100,
                 total_h: int = 140,
                 font_size: int = 35,
                 letter_spacing: int = 9,
                 gap: int = 2) -> None:
    """
    生成 Code-128 条形码：
      • 条形区 400×100 px
      • 数字区总高 (total_h - bar_h) px，高度共 40 px
      • 数字用微软雅黑、字号 font_size、字间距 letter_spacing
      • 数字紧贴条形码，上方留 gap px 间距
      • 背景透明
    """
    # 1) 生成只有条形区（不含文字）
    Code128 = get_barcode_class("code128")
    module_w = bar_w / (11 + 2 * len(code))
    bar_img = Code128(
        code,
        writer=ImageWriter()
    ).render({
        "write_text": False,
        "module_width": module_w,
        "module_height": bar_h,
        "quiet_zone": 0,
        "background": "white",
    }).convert("RGBA")
    bar_img = bar_img.resize((bar_w, bar_h), Image.NEAREST)

    # 2) 新建 400×140 透明画布，贴条形区
    canvas = Image.new("RGBA", (bar_w, total_h), (255, 255, 255, 0))
    canvas.paste(bar_img, (0, 0))

    # 3) 绘制下方数字，微软雅黑、字号35、字间距10，紧贴条形码
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", size=font_size)
    except Exception:
        font = ImageFont.load_default()

    # 计算每个字符宽高
    char_sizes = []
    for ch in code:
        try:
            w, h = font.getsize(ch)
        except AttributeError:
            bbox = draw.textbbox((0, 0), ch, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        char_sizes.append((w, h))

    total_text_w = sum(w for w, _ in char_sizes) + letter_spacing * (len(code) - 1)
    max_char_h = max(h for _, h in char_sizes)

    # 起始坐标：水平居中，垂直为条形码底部 + gap
    x = (bar_w - total_text_w) // 2
    y = bar_h + gap

    # 绘制每个字符并应用字间距
    for (w, _), ch in zip(char_sizes, code):
        draw.text((x, y), ch, fill=(0, 0, 0, 255), font=font)
        x += w + letter_spacing

    # 4) 将剩余白色像素置为透明
    datas = [
        (r, g, b, 0) if (r > 250 and g > 250 and b > 250) else (r, g, b, 255)
        for (r, g, b, *_) in canvas.getdata()
    ]
    canvas.putdata(datas)
    canvas.save(out_path)


def main():
    if len(sys.argv) != 2:
        print("用法: python make_qr_and_barcode.py <URL>")
        sys.exit(1)

    url = sys.argv[1].strip()
    m = re.search(r"(\d+)(?:/)?$", url)
    if not m:
        print("❌ 未在 URL 尾部找到数字串")
        sys.exit(1)
    code = m.group(1)

    qr_path = Path(f"qr_{code}.png")
    bar_path = Path(f"barcode_{code}.png")

    make_qr(url, qr_path)
    make_barcode(code, bar_path)

    print(f"✅ 生成完成：{qr_path.name}, {bar_path.name}")


if __name__ == "__main__":
    main()
