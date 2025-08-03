#!/usr/bin/env python3
"""
Celery Beat 管理脚本
用于启动、停止和管理 Celery Beat 定时任务调度器
"""

import os
import sys
import signal
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

class CeleryBeatManager:
    """Celery Beat 管理器"""
    
    def __init__(self):
        self.pidfile = PROJECT_ROOT / "celerybeat.pid"
        self.schedulefile = PROJECT_ROOT / "celerybeat-schedule"
        self.logfile = PROJECT_ROOT / "logs" / "celerybeat.log"
        
        # 确保日志目录存在
        self.logfile.parent.mkdir(exist_ok=True)
    
    def start(self, detach=True, loglevel="info"):
        """启动 Celery Beat"""
        if self.is_running():
            print("Celery Beat 已经在运行")
            return False
        
        cmd = [
            "celery", "-A", "app.tasks.celery_app",
            "beat",
            "--loglevel", loglevel,
            "--pidfile", str(self.pidfile),
            "--schedule", str(self.schedulefile),
            "--logfile", str(self.logfile)
        ]
        
        if detach:
            cmd.append("--detach")
        
        print(f"启动 Celery Beat: {' '.join(cmd)}")
        
        try:
            if detach:
                subprocess.run(cmd, check=True)
                print("Celery Beat 已在后台启动")
            else:
                # 前台运行，允许 Ctrl+C 停止
                subprocess.run(cmd)
        except subprocess.CalledProcessError as e:
            print(f"启动 Celery Beat 失败: {e}")
            return False
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭 Celery Beat...")
            self.stop()
        
        return True
    
    def stop(self):
        """停止 Celery Beat"""
        if not self.is_running():
            print("Celery Beat 未运行")
            return True
        
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
            
            print(f"停止 Celery Beat (PID: {pid})")
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程停止
            import time
            for _ in range(10):
                if not self.is_running():
                    break
                time.sleep(1)
            
            if self.is_running():
                print("正常停止失败，强制终止...")
                os.kill(pid, signal.SIGKILL)
            
            # 清理 PID 文件
            if self.pidfile.exists():
                self.pidfile.unlink()
            
            print("Celery Beat 已停止")
            return True
            
        except (FileNotFoundError, ProcessLookupError):
            print("进程已停止，清理 PID 文件")
            if self.pidfile.exists():
                self.pidfile.unlink()
            return True
        except Exception as e:
            print(f"停止 Celery Beat 失败: {e}")
            return False
    
    def restart(self, loglevel="info"):
        """重启 Celery Beat"""
        print("重启 Celery Beat...")
        self.stop()
        import time
        time.sleep(2)
        return self.start(loglevel=loglevel)
    
    def status(self):
        """检查 Celery Beat 状态"""
        if self.is_running():
            with open(self.pidfile, 'r') as f:
                pid = f.read().strip()
            print(f"Celery Beat 正在运行 (PID: {pid})")
            return True
        else:
            print("Celery Beat 未运行")
            return False
    
    def is_running(self):
        """检查 Celery Beat 是否正在运行"""
        if not self.pidfile.exists():
            return False
        
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)
            return True
        except (FileNotFoundError, ProcessLookupError, ValueError):
            # PID 文件不存在或进程不存在
            if self.pidfile.exists():
                self.pidfile.unlink()
            return False
    
    def logs(self, lines=50, follow=False):
        """查看日志"""
        if not self.logfile.exists():
            print("日志文件不存在")
            return
        
        if follow:
            cmd = ["tail", "-f", str(self.logfile)]
        else:
            cmd = ["tail", f"-{lines}", str(self.logfile)]
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            pass
    
    def clear_schedule(self):
        """清除调度文件"""
        if self.schedulefile.exists():
            self.schedulefile.unlink()
            print("调度文件已清除")
        else:
            print("调度文件不存在")
    
    def list_tasks(self):
        """列出所有定时任务"""
        try:
            from app.tasks.beat_schedules import BEAT_SCHEDULE
            
            print("\n定时任务列表:")
            print("=" * 80)
            
            for name, config in BEAT_SCHEDULE.items():
                task = config['task']
                schedule = config['schedule']
                queue = config.get('options', {}).get('queue', 'default')
                description = config.get('description', '无描述')
                
                print(f"\n任务名称: {name}")
                print(f"任务路径: {task}")
                print(f"执行队列: {queue}")
                print(f"调度规则: {schedule}")
                print(f"任务描述: {description}")
                print("-" * 40)
                
        except ImportError as e:
            print(f"无法导入任务配置: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Celery Beat 管理工具")
    parser.add_argument("action", choices=[
        "start", "stop", "restart", "status", 
        "logs", "clear", "list", "foreground"
    ], help="操作类型")
    
    parser.add_argument("--loglevel", default="info", 
                       choices=["debug", "info", "warning", "error"],
                       help="日志级别")
    
    parser.add_argument("--lines", type=int, default=50,
                       help="显示日志行数")
    
    parser.add_argument("--follow", action="store_true",
                       help="实时跟踪日志")
    
    args = parser.parse_args()
    
    manager = CeleryBeatManager()
    
    if args.action == "start":
        manager.start(loglevel=args.loglevel)
    elif args.action == "stop":
        manager.stop()
    elif args.action == "restart":
        manager.restart(loglevel=args.loglevel)
    elif args.action == "status":
        manager.status()
    elif args.action == "logs":
        manager.logs(lines=args.lines, follow=args.follow)
    elif args.action == "clear":
        manager.clear_schedule()
    elif args.action == "list":
        manager.list_tasks()
    elif args.action == "foreground":
        manager.start(detach=False, loglevel=args.loglevel)


if __name__ == "__main__":
    main()