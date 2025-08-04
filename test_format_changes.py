#!/usr/bin/env python3
"""
测试送达回证格式修改功能
"""

import requests
import json

# API基础配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def login_and_get_token():
    """登录并获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("🔐 正在登录...")
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success") and result.get("data"):
            token = result["data"]["access_token"]
            print(f"✅ 登录成功，获取到token")
            return token
        else:
            print(f"❌ 登录响应格式错误: {result}")
            return None
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def test_format_changes(token):
    """测试格式修改功能"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试不同的案号和时间格式
    test_cases = [
        {
            "name": "纯数字案号 + 带时间的日期",
            "data": {
                "tracking_number": "1151242358360",
                "document_type": "补正通知书",
                "case_number": "1129",  # 纯数字
                "recipient_type": "申请人",
                "recipient_name": "张三",
                "delivery_time": "2025/07/09 09:00:45",  # 带时间
                "delivery_address": "上海市松江区某某街道123号",
                "sender": "测试送达人"
            }
        },
        {
            "name": "已格式化案号 + 纯日期",
            "data": {
                "tracking_number": "1151242358360",
                "document_type": "申请告知书",
                "case_number": "沪松府复字（2025）第888号",  # 已格式化
                "recipient_type": "被申请人",
                "recipient_name": "李四",
                "delivery_time": "2025/08/05",  # 纯日期
                "delivery_address": "上海市松江区测试地址456号",
                "sender": ""
            }
        },
        {
            "name": "复合案号 + 复杂时间",
            "data": {
                "tracking_number": "1151242358360",
                "document_type": "决定书",
                "case_number": "2024-第999号",  # 包含数字的复合格式
                "recipient_type": "第三人",
                "recipient_name": "王五",
                "delivery_time": "2025年08月05日 14:30:15",  # 中文时间格式
                "delivery_address": "上海市松江区新桥镇789号",
                "sender": "行政复议办公室"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {test_case['name']}")
        print(f"输入数据:")
        for key, value in test_case['data'].items():
            print(f"  - {key}: '{value}'")
        
        response = requests.post(
            f"{API_BASE}/delivery-receipts/generate-smart",
            headers=headers,
            json=test_case['data']
        )
        
        print(f"\n📊 API响应:")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 生成成功!")
            print(f"生成文件: {result['data']['doc_filename']}")
            print(f"文件大小: {result['data']['file_size']} bytes")
        else:
            print(f"❌ 生成失败: {response.text}")
        
        print("-" * 50)

def main():
    print("🚀 开始测试送达回证格式修改功能")
    print("=" * 70)
    
    # 1. 登录获取token
    token = login_and_get_token()
    if not token:
        print("❌ 无法获取认证token，退出测试")
        return
    
    # 2. 测试格式修改
    test_format_changes(token)
    
    print("\n" + "=" * 70)
    print("📋 测试说明:")
    print("1. 案号格式化:")
    print("   - 输入: '1129' → 输出: '沪松府复字（2025）第1129号'")
    print("   - 输入: '沪松府复字（2025）第888号' → 输出: '沪松府复字（2025）第888号' (不变)")
    print("   - 输入: '2024-第999号' → 输出: '沪松府复字（2025）第999号'")
    print("")
    print("2. 时间格式化:")
    print("   - 输入: '2025/07/09 09:00:45' → 输出: '2025/07/09'")
    print("   - 输入: '2025/08/05' → 输出: '2025/08/05' (不变)")
    print("   - 输入: '2025年08月05日 14:30:15' → 输出: '2025年08月05日'")

if __name__ == "__main__":
    main()