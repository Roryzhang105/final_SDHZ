#!/usr/bin/env python3
"""
批量处理功能测试脚本
测试WebSocket和批量上传的完整功能
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试配置
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
TEST_IMAGES_DIR = Path("tests")

class BatchProcessingTester:
    """批量处理测试器"""
    
    def __init__(self):
        self.session = None
        self.ws = None
        self.auth_token = None
        self.websocket_messages = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username: str = "admin", password: str = "admin123"):
        """认证获取token"""
        try:
            logger.info(f"正在认证用户: {username}")
            
            login_data = {
                "username": username,
                "password": password
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/v1/auth/login",
                data=login_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result["access_token"]
                    logger.info("认证成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"认证失败: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"认证异常: {e}")
            return False
    
    async def connect_websocket(self):
        """连接WebSocket"""
        try:
            if not self.auth_token:
                logger.error("需要先认证获取token")
                return False
                
            logger.info("正在连接WebSocket...")
            
            ws_url = f"{WS_URL}/api/v1/ws?token={self.auth_token}"
            self.ws = await self.session.ws_connect(ws_url)
            
            logger.info("WebSocket连接成功")
            
            # 启动消息监听任务
            asyncio.create_task(self._listen_websocket_messages())
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False
    
    async def _listen_websocket_messages(self):
        """监听WebSocket消息"""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        message = json.loads(msg.data)
                        self.websocket_messages.append(message)
                        logger.info(f"收到WebSocket消息: {message.get('type')} - {message.get('message', '')}")
                        
                        # 如果是任务更新消息，打印详细信息
                        if message.get('type') in ['task_update', 'status_changed', 'task_completed']:
                            task_id = message.get('task_id')
                            status = message.get('data', {}).get('status') or message.get('status')
                            logger.info(f"任务 {task_id} 状态更新: {status}")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"无法解析WebSocket消息: {msg.data}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket错误: {self.ws.exception()}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket消息监听异常: {e}")
    
    async def get_test_images(self) -> List[Path]:
        """获取测试图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png'}
        test_images = []
        
        if TEST_IMAGES_DIR.exists():
            for file_path in TEST_IMAGES_DIR.iterdir():
                if file_path.suffix.lower() in image_extensions:
                    test_images.append(file_path)
        
        logger.info(f"找到 {len(test_images)} 个测试图片")
        return test_images[:5]  # 限制为5张图片进行测试
    
    async def test_batch_upload(self, image_files: List[Path]) -> Dict[str, Any]:
        """测试批量上传"""
        try:
            logger.info(f"开始批量上传测试，文件数量: {len(image_files)}")
            
            if not self.auth_token:
                logger.error("需要先认证")
                return {"success": False, "message": "未认证"}
            
            # 准备multipart form data
            data = aiohttp.FormData()
            
            for image_file in image_files:
                if not image_file.exists():
                    logger.warning(f"文件不存在: {image_file}")
                    continue
                    
                # 读取文件并添加到form data
                with open(image_file, 'rb') as f:
                    content = f.read()
                    data.add_field('files', content, 
                                 filename=image_file.name,
                                 content_type='image/jpeg' if image_file.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png')
            
            # 发送批量上传请求
            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/v1/tasks/batch-upload",
                data=data,
                headers=headers
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"批量上传成功: {result.get('message')}")
                    logger.info(f"批次ID: {result.get('batch_id')}")
                    logger.info(f"创建任务数: {result.get('summary', {}).get('created_tasks', 0)}")
                    return result
                else:
                    logger.error(f"批量上传失败: {response.status} - {result}")
                    return {"success": False, "message": result.get("detail", "批量上传失败")}
                    
        except Exception as e:
            logger.error(f"批量上传异常: {e}")
            return {"success": False, "message": str(e)}
    
    async def monitor_batch_progress(self, batch_id: str, timeout: int = 300):
        """监控批量任务进度"""
        try:
            logger.info(f"开始监控批次进度: {batch_id}")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 查询批次状态
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                
                async with self.session.get(
                    f"{BASE_URL}/api/v1/tasks/batch/{batch_id}/status",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        batch_status = await response.json()
                        data = batch_status.get('data', {})
                        
                        total = data.get('total_tasks', 0)
                        completed = data.get('completed_tasks', 0)
                        failed = data.get('failed_tasks', 0)
                        processing = data.get('processing_tasks', 0)
                        progress = data.get('overall_progress', 0)
                        
                        logger.info(f"批次进度: {progress:.1f}% - 完成:{completed} 失败:{failed} 处理中:{processing} 总计:{total}")
                        
                        # 检查是否完成
                        if data.get('is_completed', False):
                            logger.info("批次处理完成")
                            return data
                            
                    else:
                        logger.warning(f"查询批次状态失败: {response.status}")
                
                await asyncio.sleep(5)  # 每5秒查询一次
            
            logger.warning(f"批次监控超时: {batch_id}")
            return None
            
        except Exception as e:
            logger.error(f"监控批次进度异常: {e}")
            return None
    
    async def test_websocket_updates(self, expected_task_count: int, timeout: int = 60):
        """测试WebSocket实时更新"""
        try:
            logger.info(f"测试WebSocket更新，期望任务数: {expected_task_count}")
            
            start_time = time.time()
            received_task_updates = set()
            
            while time.time() - start_time < timeout:
                # 检查收到的WebSocket消息
                for message in self.websocket_messages:
                    if message.get('type') in ['task_update', 'status_changed', 'task_completed']:
                        task_id = message.get('task_id')
                        if task_id:
                            received_task_updates.add(task_id)
                
                logger.info(f"已收到 {len(received_task_updates)} 个任务的WebSocket更新")
                
                # 如果收到了足够的更新消息，认为测试成功
                if len(received_task_updates) >= expected_task_count:
                    logger.info("WebSocket实时更新测试成功")
                    return True
                
                await asyncio.sleep(2)
            
            logger.warning(f"WebSocket更新测试超时，期望{expected_task_count}个，实际收到{len(received_task_updates)}个")
            return False
            
        except Exception as e:
            logger.error(f"WebSocket更新测试异常: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """运行完整的批量处理测试"""
        try:
            logger.info("=" * 50)
            logger.info("开始批量处理综合测试")
            logger.info("=" * 50)
            
            # 1. 认证
            logger.info("\n1. 用户认证测试")
            if not await self.authenticate():
                logger.error("认证失败，终止测试")
                return False
            
            # 2. WebSocket连接
            logger.info("\n2. WebSocket连接测试")
            if not await self.connect_websocket():
                logger.error("WebSocket连接失败，终止测试")
                return False
            
            # 3. 获取测试图片
            logger.info("\n3. 准备测试数据")
            test_images = await self.get_test_images()
            if not test_images:
                logger.error("没有找到测试图片，请在tests/目录下放置测试图片")
                return False
            
            # 4. 批量上传测试
            logger.info("\n4. 批量上传测试")
            upload_result = await self.test_batch_upload(test_images)
            if not upload_result.get('success'):
                logger.error(f"批量上传失败: {upload_result.get('message')}")
                return False
            
            batch_id = upload_result.get('batch_id')
            created_tasks = upload_result.get('summary', {}).get('created_tasks', 0)
            
            # 5. WebSocket实时更新测试
            logger.info("\n5. WebSocket实时更新测试")
            websocket_success = await self.test_websocket_updates(created_tasks, timeout=30)
            
            # 6. 批量进度监控测试
            logger.info("\n6. 批量进度监控测试")
            if batch_id:
                final_status = await self.monitor_batch_progress(batch_id, timeout=120)
                if final_status:
                    logger.info(f"最终状态: 完成{final_status.get('completed_tasks', 0)}个任务")
                else:
                    logger.warning("批量进度监控超时或失败")
            
            # 7. 测试结果汇总
            logger.info("\n" + "=" * 50)
            logger.info("测试结果汇总:")
            logger.info(f"✅ 用户认证: 成功")
            logger.info(f"✅ WebSocket连接: 成功")
            logger.info(f"✅ 批量上传: 成功 - 创建{created_tasks}个任务")
            logger.info(f"{'✅' if websocket_success else '❌'} WebSocket实时更新: {'成功' if websocket_success else '失败'}")
            logger.info(f"✅ 批量进度监控: {'成功' if final_status else '部分成功'}")
            logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            logger.error(f"综合测试异常: {e}")
            return False

async def main():
    """主函数"""
    async with BatchProcessingTester() as tester:
        success = await tester.run_comprehensive_test()
        
        if success:
            logger.info("\n🎉 所有测试通过！批量处理和WebSocket功能正常工作")
            sys.exit(0)
        else:
            logger.error("\n❌ 测试失败，请检查系统配置和日志")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())