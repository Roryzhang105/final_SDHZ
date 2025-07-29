import os
from datetime import datetime
from celery import current_app as celery_app
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.delivery_receipt import DeliveryReceiptService
from app.services.tracking import TrackingService


@celery_app.task
def capture_tracking_screenshot_task(tracking_number: str):
    """
    截取物流跟踪页面截图的异步任务
    """
    db: Session = SessionLocal()
    try:
        tracking_service = TrackingService(db)
        receipt_service = DeliveryReceiptService(db)
        
        receipt = tracking_service.get_receipt_by_tracking_number(tracking_number)
        if not receipt:
            return {"error": "未找到对应的送达回证"}
        
        # 生成截图
        screenshot_path = capture_tracking_screenshot(tracking_number, receipt.courier_company)
        
        if screenshot_path:
            # 更新送达回证的截图路径
            receipt_service.update_receipt_files(
                receipt_id=receipt.id,
                tracking_screenshot_path=screenshot_path
            )
            
            return {
                "message": "物流跟踪截图生成成功",
                "tracking_number": tracking_number,
                "screenshot_path": screenshot_path
            }
        else:
            return {"error": "截图生成失败"}
            
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def capture_tracking_screenshot(tracking_number: str, courier_company: str) -> str:
    """
    使用Selenium截取物流跟踪页面
    """
    try:
        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 初始化WebDriver
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        try:
            # 根据快递公司构造查询URL
            url = build_tracking_url(tracking_number, courier_company)
            
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 生成截图文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tracking_{tracking_number}_{timestamp}.png"
            screenshot_dir = os.path.join(settings.UPLOAD_DIR, "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, filename)
            
            # 截图
            driver.save_screenshot(screenshot_path)
            
            return screenshot_path
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"截图失败: {e}")
        return None


def build_tracking_url(tracking_number: str, courier_company: str) -> str:
    """
    根据快递公司构造查询URL
    """
    # 快递公司URL映射
    courier_urls = {
        "顺丰": f"https://www.sf-express.com/chn/sc/dynamic_function/waybill/#search/bill-number/{tracking_number}",
        "中通": f"https://www.zto.com/query?number={tracking_number}",
        "圆通": f"https://www.yto.net.cn/query?number={tracking_number}",
        "申通": f"https://www.sto.cn/query?number={tracking_number}",
        "韵达": f"https://www.yundaex.com/query?number={tracking_number}",
        "EMS": f"https://www.ems.com.cn/query?number={tracking_number}",
    }
    
    return courier_urls.get(courier_company, f"https://www.kuaidi100.com/query?number={tracking_number}")


@celery_app.task
def batch_capture_screenshots(tracking_numbers: list):
    """
    批量截图
    """
    results = []
    for tracking_number in tracking_numbers:
        result = capture_tracking_screenshot_task.delay(tracking_number)
        results.append({"tracking_number": tracking_number, "task_id": result.id})
    
    return {"message": f"批量截图 {len(tracking_numbers)} 个物流跟踪", "tasks": results}