#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.core.config import settings
from app.models.base import Base

# 导入所有模型以确保它们被注册
from app.models.user import User
from app.models.delivery_receipt import DeliveryReceipt
from app.models.courier import Courier
from app.models.tracking import TrackingInfo


def create_database_if_not_exists():
    """检查SQLite数据库连接"""
    try:
        # 尝试连接到SQLite数据库
        engine.connect()
        print("SQLite数据库连接正常")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False
    return True


def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功")
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        return False


def init_courier_data():
    """初始化快递公司数据"""
    db = SessionLocal()
    try:
        # 检查是否已有快递公司数据
        existing_couriers = db.query(Courier).count()
        if existing_couriers > 0:
            print("快递公司数据已存在，跳过初始化")
            return True

        # 初始化常用快递公司
        couriers = [
            {
                "name": "顺丰速运",
                "code": "shunfeng",
                "website": "https://www.sf-express.com",
                "tracking_url": "https://www.sf-express.com/chn/sc/dynamic_function/waybill/#search/bill-number/{tracking_number}",
                "description": "顺丰速运快递"
            },
            {
                "name": "中通快递",
                "code": "zhongtong", 
                "website": "https://www.zto.com",
                "tracking_url": "https://www.zto.com/query?number={tracking_number}",
                "description": "中通快递"
            },
            {
                "name": "圆通快递",
                "code": "yuantong",
                "website": "https://www.yto.net.cn",
                "tracking_url": "https://www.yto.net.cn/query?number={tracking_number}",
                "description": "圆通快递"
            },
            {
                "name": "申通快递",
                "code": "shentong",
                "website": "https://www.sto.cn",
                "tracking_url": "https://www.sto.cn/query?number={tracking_number}",
                "description": "申通快递"
            },
            {
                "name": "韵达快递",
                "code": "yunda",
                "website": "https://www.yundaex.com",
                "tracking_url": "https://www.yundaex.com/query?number={tracking_number}",
                "description": "韵达快递"
            },
            {
                "name": "中国邮政",
                "code": "ems",
                "website": "https://www.ems.com.cn",
                "tracking_url": "https://www.ems.com.cn/query?number={tracking_number}",
                "description": "中国邮政EMS"
            }
        ]

        for courier_data in couriers:
            courier = Courier(**courier_data)
            db.add(courier)

        db.commit()
        print(f"成功初始化 {len(couriers)} 个快递公司数据")
        return True

    except Exception as e:
        print(f"初始化快递公司数据失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    print("开始初始化数据库...")
    
    # 1. 检查数据库连接
    if not create_database_if_not_exists():
        return False
    
    # 2. 创建表
    if not create_tables():
        return False
    
    # 3. 初始化基础数据
    if not init_courier_data():
        return False
    
    print("数据库初始化完成！")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)