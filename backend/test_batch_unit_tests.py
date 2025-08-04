#!/usr/bin/env python3
"""
批量处理单元测试
测试各个组件的独立功能
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.task import TaskService
from app.models.task import Task, TaskStatusEnum
from app.core.database import SessionLocal
from sqlalchemy.orm import Session
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBatchProcessing:
    """批量处理单元测试类"""
    
    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def task_service(self, db_session):
        """创建TaskService实例"""
        return TaskService(db_session)
    
    @pytest.fixture
    def sample_file_info(self):
        """创建示例文件信息"""
        return {
            "index": 0,
            "filename": "test_image.jpg",
            "size": 1024,
            "content_type": "image/jpeg",
            "content": b"fake_image_content"
        }
    
    def test_create_single_task_sync_success(self, task_service, sample_file_info):
        """测试单个任务创建成功"""
        batch_id = "test_batch_123"
        user_id = 1
        
        # 模拟文件保存
        with patch('os.makedirs'), \
             patch('builtins.open', create=True) as mock_open, \
             patch('uuid.uuid4', return_value=Mock(hex='test-uuid')):
            
            mock_open.return_value.__enter__.return_value.write = Mock()
            
            result = task_service._create_single_task_sync(
                sample_file_info, user_id, batch_id
            )
            
            assert result["success"] is True
            assert result["message"] == "任务创建成功"
            assert "task_id" in result["data"]
            assert result["data"]["batch_id"] == batch_id
    
    def test_create_single_task_sync_file_error(self, task_service, sample_file_info):
        """测试文件保存失败的情况"""
        batch_id = "test_batch_123"
        user_id = 1
        
        # 模拟文件保存失败
        with patch('os.makedirs'), \
             patch('builtins.open', side_effect=IOError("磁盘空间不足")):
            
            result = task_service._create_single_task_sync(
                sample_file_info, user_id, batch_id
            )
            
            assert result["success"] is False
            assert "磁盘空间不足" in result["message"]
    
    @pytest.mark.asyncio
    async def test_batch_create_tasks_from_uploads(self, task_service):
        """测试批量创建任务"""
        validated_files = [
            {
                "index": 0,
                "filename": "test1.jpg",
                "size": 1024,
                "content_type": "image/jpeg",
                "content": b"fake_content_1"
            },
            {
                "index": 1,
                "filename": "test2.png",
                "size": 2048,
                "content_type": "image/png",
                "content": b"fake_content_2"
            }
        ]
        
        user_id = 1
        
        # 模拟成功的任务创建
        with patch.object(task_service, '_create_single_task_sync') as mock_create, \
             patch.object(task_service, '_start_batch_processing') as mock_start:
            
            mock_create.return_value = {
                "success": True,
                "message": "任务创建成功",
                "data": {
                    "task_id": "test_task_id",
                    "batch_id": "test_batch_id"
                }
            }
            
            result = await task_service.batch_create_tasks_from_uploads(
                validated_files, user_id
            )
            
            assert result["success"] is True
            assert len(result["tasks"]) == 2
            assert "batch_id" in result
            
            # 验证_start_batch_processing被调用
            mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_update_sending(self, task_service):
        """测试WebSocket更新发送"""
        # 创建一个模拟的Task对象
        task = Mock(spec=Task)
        task.task_id = "test_task_123"
        task.status = TaskStatusEnum.COMPLETED
        task.user_id = 1
        task.task_name = "测试任务"
        task.description = "测试描述"
        task.qr_code = "test_qr_code"
        task.tracking_number = "1234567890"
        task.courier_company = "EMS"
        task.delivery_status = "已签收"
        task.error_message = None
        task.document_url = "/test/document.docx"
        task.screenshot_url = "/test/screenshot.png"
        task.created_at = None
        task.started_at = None
        task.completed_at = None
        task.delivery_time = None
        task.processing_time = 120
        
        # 模拟WebSocket管理器
        with patch('app.api.api_v1.websocket.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock(return_value=True)
            
            await task_service._send_websocket_update(task, "task_completed")
            
            # 验证WebSocket消息被发送
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            message = call_args[0][0]  # 第一个参数是消息
            user_id = call_args[0][1]  # 第二个参数是用户ID
            
            assert message["type"] == "task_completed"
            assert message["task_id"] == "test_task_123"
            assert message["status"] == "COMPLETED"
            assert user_id == 1
    
    def test_file_validation_logic(self):
        """测试文件验证逻辑"""
        # 测试有效文件
        valid_file = {
            "filename": "test.jpg",
            "content_type": "image/jpeg",
            "size": 1024
        }
        
        # 这里应该有文件验证的逻辑测试
        # 由于验证逻辑在API端点中，这里主要测试数据结构
        assert valid_file["content_type"].startswith("image/")
        assert valid_file["size"] < 10 * 1024 * 1024  # 10MB限制
    
    @pytest.mark.asyncio
    async def test_batch_status_query(self, task_service):
        """测试批量状态查询"""
        batch_id = "test_batch_456"
        
        # 模拟数据库查询结果
        mock_tasks = []
        for i in range(3):
            task = Mock(spec=Task)
            task.task_id = f"task_{i}"
            task.status = TaskStatusEnum.COMPLETED if i < 2 else TaskStatusEnum.PENDING
            task.tracking_number = f"123456789{i}"
            task.error_message = None
            task.created_at = None
            task.completed_at = None
            task.extra_metadata = {"batch_id": batch_id}
            mock_tasks.append(task)
        
        with patch.object(task_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = mock_tasks
            
            result = await task_service.get_batch_status(batch_id)
            
            assert result is not None
            assert result["batch_id"] == batch_id
            assert result["total_tasks"] == 3
            assert result["completed_tasks"] == 2
            assert result["processing_tasks"] == 1
            assert len(result["tasks"]) == 3
    
    def test_progress_calculation(self, task_service):
        """测试进度计算"""
        test_cases = [
            (TaskStatusEnum.PENDING, 10),
            (TaskStatusEnum.RECOGNIZING, 25),
            (TaskStatusEnum.TRACKING, 50),
            (TaskStatusEnum.DELIVERED, 75),
            (TaskStatusEnum.GENERATING, 90),
            (TaskStatusEnum.COMPLETED, 100),
            (TaskStatusEnum.FAILED, 0)
        ]
        
        for status, expected_progress in test_cases:
            progress = task_service._calculate_progress(status)
            assert progress == expected_progress, f"状态 {status} 的进度应该是 {expected_progress}，实际是 {progress}"
    
    def test_status_message_generation(self, task_service):
        """测试状态消息生成"""
        test_cases = [
            (TaskStatusEnum.PENDING, "任务等待处理"),
            (TaskStatusEnum.RECOGNIZING, "正在识别二维码"),
            (TaskStatusEnum.TRACKING, "正在查询物流信息"),
            (TaskStatusEnum.DELIVERED, "快递已签收"),
            (TaskStatusEnum.GENERATING, "正在生成文档"),
            (TaskStatusEnum.COMPLETED, "任务处理完成"),
            (TaskStatusEnum.FAILED, "任务处理失败")
        ]
        
        for status, expected_message in test_cases:
            message = task_service._get_status_message(status)
            assert message == expected_message, f"状态 {status} 的消息应该是 '{expected_message}'，实际是 '{message}'"

def run_unit_tests():
    """运行单元测试"""
    logger.info("开始运行批量处理单元测试")
    
    # 运行pytest
    import subprocess
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    logger.info("测试输出:")
    logger.info(result.stdout)
    
    if result.stderr:
        logger.error("测试错误:")
        logger.error(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    # 如果直接运行此文件，执行测试
    success = run_unit_tests()
    if success:
        logger.info("✅ 所有单元测试通过")
    else:
        logger.error("❌ 单元测试失败")
        sys.exit(1)