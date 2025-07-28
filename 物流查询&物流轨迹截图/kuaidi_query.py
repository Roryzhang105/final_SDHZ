#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kuaidi_query.py — EMS 实时查询 + 本地缓存
"""

from __future__ import annotations
import hashlib, json, sys, requests, os, time
from typing import Dict, List, Tuple

# -- 授权信息 -----------------------------------------------------------------
KUAIDI_KEY      = "GUpgAlsJ4403"
KUAIDI_CUSTOMER = "5813A47FED91DD26A0EF340F2A194938"

# -- 缓存设置 -----------------------------------------------------------------
CACHE_DIR   = "cache"          # 子目录名
CACHE_TTL   = 30 * 60          # 单号缓存有效期（秒）→ 30 分钟

# ---------------------------------------------------------------------------
def _md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest().upper()

def _sign(param_str: str) -> str:
    return _md5(param_str + KUAIDI_KEY + KUAIDI_CUSTOMER)

def _cache_path(nu: str, com: str) -> str:
    fname = f"{com}_{nu}.json"
    return os.path.join(CACHE_DIR, fname)

def _load_cache(nu: str, com: str) -> Dict | None:
    path = _cache_path(nu, com)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _save_cache(nu: str, com: str, data: Dict) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(nu, com), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------- 主函数 ----------------------------------------
def query_express(nu: str, com: str = "") -> Tuple[bool, str, List[Dict]]:
    """
    :return: (是否已签收, 签收时间, 轨迹列表)
    """
    com = com.strip().lower() or "ems"

    # 1. 尝试读取缓存
    cached = _load_cache(nu, com)
    if cached:
        res_json = cached
    else:
        # 2. 请求接口
        param = {
            "com": com, "num": nu, "phone": "",
            "from": "", "to": "", "resultv2": "1", "show": "0", "order": "desc"
        }
        param_str = json.dumps(param, ensure_ascii=False)
        payload = {
            "customer": KUAIDI_CUSTOMER,
            "param":    param_str,
            "sign":     _sign(param_str),
        }
        url = "https://poll.kuaidi100.com/poll/query.do"
        res_json = requests.post(url, data=payload, timeout=10).json()

        # 3. 写入缓存
        _save_cache(nu, com, res_json)

    # 4. 解析
    state = res_json.get("state")
    data  = res_json.get("data", [])
    signed = state == "3"
    sign_time = data[0]["time"] if signed and data else ""

    return signed, sign_time, data

# ---------------------------- CLI 测试 --------------------------------------
if __name__ == "__main__":
    try:
        nu  = input("请输入运单号：").strip()
        com = input("快递公司编码（留空默认 ems）：").strip()

        ok, d_time, traces = query_express(nu, com)

        print("\n=== 查询结果 ===")
        print("是否已签收 :", "✅ 已签收" if ok else "🚚 未签收")
        if d_time:
            print("签收时间   :", d_time)

        print("\n--- 全部轨迹（最新在前） ---")
        for item in traces:
            print(f"{item['time']} | {item['context']}")

    except requests.RequestException as e:
        print("网络请求失败:", e)
        sys.exit(1)
    except Exception as e:
        print("查询异常:", e)
        sys.exit(1)
