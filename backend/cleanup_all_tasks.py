#!/usr/bin/env python3
"""
Database cleanup script to delete all tasks and their associated files.
This script will:
1. Query all tasks from the database
2. Delete all associated files using the existing cleanup methods
3. Delete all tasks from the database
4. Clean up empty directories and temporary files
"""

import os
import sys
import shutil
import glob
from typing import List, Optional

# Add the app directory to Python path
sys.path.append('/home/rory/final_SDHZ/backend')

from app.core.database import get_db
from app.models.task import Task
from app.models.activity_log import ActivityLog
from app.services.task import TaskService
from app.services.activity_log import ActivityLogService
from sqlalchemy.orm import Session

def cleanup_file_directories():
    """Clean up common file directories and empty folders"""
    upload_dirs_to_clean = [
        '/home/rory/final_SDHZ/backend/uploads',
        '/home/rory/final_SDHZ/backend/uploads/delivery_receipts',
        '/home/rory/final_SDHZ/backend/uploads/tracking_screenshots',
        '/home/rory/final_SDHZ/backend/uploads/tracking_html',
        '/home/rory/final_SDHZ/backend/uploads/express_cache'
    ]
    
    cleaned_files = 0
    
    print("🧹 Cleaning up file directories...")
    
    for upload_dir in upload_dirs_to_clean:
        if os.path.exists(upload_dir):
            # Remove all files in the directory but keep the directory structure
            for file_path in glob.glob(os.path.join(upload_dir, '*')):
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        cleaned_files += 1
                        print(f"  ✅ Deleted file: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"  ❌ Failed to delete {file_path}: {e}")
    
    # Clean up any remaining image files in uploads root
    uploads_root = '/home/rory/final_SDHZ/backend/uploads'
    if os.path.exists(uploads_root):
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.docx', '*.pdf', '*.html', '*.json', '*.txt']:
            for file_path in glob.glob(os.path.join(uploads_root, ext)):
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        cleaned_files += 1
                        print(f"  ✅ Deleted file: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"  ❌ Failed to delete {file_path}: {e}")
    
    print(f"🗑️ Total files cleaned: {cleaned_files}")
    return cleaned_files

def cleanup_all_tasks():
    """Delete all tasks and their associated files"""
    
    print("🚀 Starting database cleanup process...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Count tasks first
        task_count = db.query(Task).count()
        activity_count = db.query(ActivityLog).count()
        
        print(f"📊 Found {task_count} tasks and {activity_count} activity logs to delete")
        
        if task_count == 0 and activity_count == 0:
            print("✅ Database is already clean - no tasks or activities to delete")
            return
        
        # Get all tasks for file cleanup
        tasks = db.query(Task).all()
        task_service = TaskService(db)
        
        deleted_tasks = 0
        files_cleaned = 0
        
        print("🗂️ Deleting tasks and cleaning up associated files...")
        
        # Delete each task using the existing service method
        for task in tasks:
            try:
                print(f"  🔄 Processing task {task.id} (status: {task.status})")
                
                # Use the enhanced cleanup method
                task_service._cleanup_task_files(task)
                # Also cleanup delivery receipt
                task_service._cleanup_delivery_receipt(task)
                # Count as 1 task processed
                files_cleaned += 1
                
                # Delete the task from database
                db.delete(task)
                deleted_tasks += 1
                
                print(f"  ✅ Task {task.id} deleted (files cleaned)")
                
            except Exception as e:
                print(f"  ❌ Failed to delete task {task.id}: {e}")
                continue
        
        # Delete all activity logs
        print("📝 Deleting activity logs...")
        db.query(ActivityLog).delete()
        
        # Commit all deletions
        db.commit()
        
        print(f"✅ Database cleanup completed:")
        print(f"   - Tasks deleted: {deleted_tasks}")
        print(f"   - Activity logs deleted: {activity_count}")
        print(f"   - Task files cleaned: {files_cleaned}")
        
        # Additional file system cleanup
        additional_files = cleanup_file_directories()
        
        print(f"🎉 Total cleanup summary:")
        print(f"   - Database tasks: {deleted_tasks}")
        print(f"   - Database activities: {activity_count}")  
        print(f"   - Task-related files: {files_cleaned}")
        print(f"   - Additional files: {additional_files}")
        print(f"   - Total files cleaned: {files_cleaned + additional_files}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        cleanup_all_tasks()
        print("\n🎊 Database cleanup completed successfully!")
    except Exception as e:
        print(f"\n💥 Cleanup failed: {e}")
        sys.exit(1)