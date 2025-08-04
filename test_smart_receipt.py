#!/usr/bin/env python3
"""
测试智能填充送达回证生成功能
"""

import requests
import json
from datetime import datetime

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

def test_smart_receipt_generation(token):
    """测试智能填充送达回证生成"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试数据
    test_data = {
        "tracking_number": "1151242358360",  # 使用现有的快递单号
        "document_type": "补正通知书",
        "case_number": "松政复议〔2024〕第001号",
        "recipient_type": "申请人",
        "recipient_name": "张三",
        "delivery_time": "2024年08月05日",
        "delivery_address": "上海市松江区某某街道123号",
        "sender": ""
    }
    
    print("\n📝 测试智能填充送达回证生成...")
    print(f"测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(
        f"{API_BASE}/delivery-receipts/generate-smart",
        headers=headers,
        json=test_data
    )
    
    print(f"\n📊 API响应:")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 智能填充送达回证生成成功!")
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"❌ 生成失败: {response.text}")
        return None

def test_traditional_generation(token):
    """测试传统送达回证生成进行对比"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 传统格式数据
    traditional_data = {
        "tracking_number": "1151242358360",
        "doc_title": "行政复议补正通知书\n松政复议〔2024〕第001号",
        "sender": "",
        "send_time": "2024年08月05日",
        "send_location": "上海市松江区某某街道123号",
        "receiver": "张三"
    }
    
    print("\n📝 测试传统送达回证生成（对比）...")
    print(f"传统数据: {json.dumps(traditional_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(
        f"{API_BASE}/delivery-receipts/generate",
        headers=headers,
        json=traditional_data
    )
    
    print(f"\n📊 传统API响应:")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 传统送达回证生成成功!")
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"❌ 传统生成失败: {response.text}")
        return None

def main():
    print("🚀 开始测试智能填充送达回证生成功能")
    print("=" * 60)
    
    # 1. 登录获取token
    token = login_and_get_token()
    if not token:
        print("❌ 无法获取认证token，退出测试")
        return
    
    # 2. 测试智能填充生成
    smart_result = test_smart_receipt_generation(token)
    
    # 3. 测试传统生成（对比）
    traditional_result = test_traditional_generation(token)
    
    # 4. 结果比较
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")
    
    if smart_result:
        print("✅ 智能填充功能: 正常工作")
        print(f"   - 生成文件: {smart_result['data']['doc_filename']}")
        print(f"   - 文件大小: {smart_result['data']['file_size']} bytes")
    else:
        print("❌ 智能填充功能: 存在问题")
    
    if traditional_result:
        print("✅ 传统生成功能: 正常工作")
        print(f"   - 生成文件: {traditional_result['data']['doc_filename']}")
        print(f"   - 文件大小: {traditional_result['data']['file_size']} bytes")
    else:
        print("❌ 传统生成功能: 存在问题")
    
    if smart_result and traditional_result:
        print("\n🎉 所有功能测试通过! 智能填充API已就绪")
    else:
        print("\n⚠️  部分功能存在问题，需要进一步调试")

if __name__ == "__main__":
    main()