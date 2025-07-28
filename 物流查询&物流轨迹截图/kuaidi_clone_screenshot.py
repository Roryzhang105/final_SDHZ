#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  kuaidi_clone_screenshot.py

  功能：
  1) 优先读取 ./cache/<com>_<tracking_no>.json，本地缓存未过期直接用
  2) 否则调用 query_express（会刷新缓存）
  3) 把物流数据渲染成 EMS 风格 HTML → headless Chrome 截图 PNG
     ‑ 图片宽度已加长：容器 1000 px，浏览器窗口 1280 px

  用法：python kuaidi_clone_screenshot.py <tracking_no> [company]
  依赖：pip install selenium webdriver-manager requests
"""
import sys, os, json, datetime, time, tempfile
from pathlib import Path
from kuaidi_query import query_express, CACHE_DIR, CACHE_TTL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ───────────────── HTML 模板（容器宽改为 1000px） ──────────────────
HTML_TEMPLATE = r'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>邮件轨迹</title>
<style>
  * {{margin:0;padding:0;box-sizing:border-box;}}
  body {{font-family:"Helvetica Neue",Arial,sans-serif;background:#f5f5f5;color:#333;}}
  .container {{width:1000px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);}}
  .tracking-no,.status {{padding:16px 24px;border-bottom:1px solid #eee;font-size:16px;display:flex;align-items:center;}}
  .tracking-no strong {{margin-left:4px;}}
  .status .label {{font-weight:bold;margin-right:8px;}}
  .timeline {{padding:16px 24px;}}
  .timeline-item {{position:relative;padding-left:40px;margin-bottom:24px;}}
  .timeline-item:last-child {{margin-bottom:0;}}
  .timeline-item::before {{content:'';position:absolute;left:16px;top:0;width:8px;height:8px;background:#0074c8;border-radius:50%;}}
  .timeline-item::after  {{content:'';position:absolute;left:19px;top:8px;width:2px;bottom:-16px;background:#ddd;}}
  .timeline-item:last-child::after {{display:none;}}
  .time {{font-size:14px;color:#666;margin-bottom:4px;}}
  .desc {{font-size:15px;line-height:1.4;}}
</style></head><body>
  <div class="container" id="capture-container">
    <div class="tracking-no">邮件号：<strong>{tracking_no}</strong></div>
    <div class="status"><span class="label">当前状态：</span><span>{status}</span>
      <span style="margin-left:auto;font-size:14px;color:#999;">签收时间：<span>{sign_time}</span></span>
    </div>
    <div class="timeline">{timeline_items}</div>
  </div></body></html>'''
ITEM_TEMPLATE = '<div class="timeline-item"><div class="time">{time}</div><div class="desc">{desc}</div></div>'
# ───────────────────────────────────────────────────────────────

def load_cached_json(nu: str, com: str):
    p = Path(CACHE_DIR)/f"{com}_{nu}.json"
    if p.exists() and time.time() - p.stat().st_mtime < CACHE_TTL:
        with p.open('r', encoding='utf-8') as f: return json.load(f)
    return None

def render_html(nu: str, status: str, sign_time: str, traces: list) -> str:
    items = '\n'.join(ITEM_TEMPLATE.format(time=t.get('time','—'), desc=t.get('context','—')) for t in traces)
    html = HTML_TEMPLATE.format(tracking_no=nu, status=status, sign_time=sign_time or '—', timeline_items=items)
    fd, path = tempfile.mkstemp(suffix='.html', text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f: f.write(html)
    return path

def html_to_png(html_path: str, out_png: str):
    opts = Options(); opts.add_argument('--headless=new'); opts.add_argument('--window-size=1280,1600')
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    try:
        drv.get('file:///' + os.path.abspath(html_path)); drv.implicitly_wait(5)
        with open(out_png, 'wb') as f: f.write(drv.find_element('id','capture-container').screenshot_as_png)
    finally:
        drv.quit()

def main():
    if len(sys.argv) < 2:
        print('用法: python kuaidi_clone_screenshot.py <tracking_no> [company]'); return
    nu = sys.argv[1]; com = (sys.argv[2] if len(sys.argv)>2 else '').lower() or 'ems'

    cache_json = load_cached_json(nu, com)
    if cache_json:
        state = cache_json.get('state'); traces = cache_json.get('data', [])
        signed = state == '3'; sign_time = traces[0]['time'] if signed and traces else ''
    else:
        signed, sign_time, traces = query_express(nu, com)

    status = '✅ 已签收' if signed else '🚚 运输中'
    html_path = render_html(nu, status, sign_time, traces)
    out_png = f'tracking_{nu}_{datetime.datetime.now():%Y%m%d_%H%M%S}.png'
    try:
        html_to_png(html_path, out_png); print('✅ 已生成', out_png)
    except Exception as e:
        print('❌ HTML 截图失败:', e)

if __name__ == '__main__':
    main()
