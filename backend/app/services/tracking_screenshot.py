import os
import shutil
import subprocess
import tempfile
import datetime
import platform
import requests
import zipfile
from typing import Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from app.core.config import settings
from app.services.express_tracking import ExpressTrackingService
from app.services.tracking import TrackingService


class TrackingScreenshotService:
    """物流轨迹截图服务类"""
    
    # HTML模板
    HTML_TEMPLATE = '''<!DOCTYPE html><html lang="zh-CN"><head>
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
    
    def __init__(self, db: Session):
        self.db = db
        self.express_service = ExpressTrackingService(db)
        self.tracking_service = TrackingService(db)
        self.screenshot_dir = Path(settings.UPLOAD_DIR) / "tracking_screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
        self.html_dir = Path(settings.UPLOAD_DIR) / "tracking_html"
        self.html_dir.mkdir(exist_ok=True)
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # 确定架构
        if machine in ['x86_64', 'amd64']:
            arch = 'linux64'
        elif machine in ['aarch64', 'arm64']:
            arch = 'linux64'  # Chrome也为ARM64提供linux64版本
        else:
            arch = 'linux64'  # 默认使用linux64
            
        return {
            "system": system,
            "machine": machine, 
            "arch": arch,
            "is_wsl": 'microsoft' in platform.uname().release.lower()
        }
    
    def _validate_chromedriver(self, driver_path: str) -> bool:
        """验证ChromeDriver是否可用"""
        try:
            if not os.path.exists(driver_path):
                return False
                
            # 检查是否是可执行文件
            if not os.access(driver_path, os.X_OK):
                try:
                    os.chmod(driver_path, 0o755)
                except:
                    return False
            
            # 尝试运行版本检查
            result = subprocess.run([driver_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _find_correct_chromedriver(self, base_path: str) -> Optional[str]:
        """在WebDriver Manager下载目录中查找正确的chromedriver可执行文件"""
        try:
            # 遍历目录寻找chromedriver可执行文件
            for root, dirs, files in os.walk(os.path.dirname(base_path)):
                for file in files:
                    if file == 'chromedriver' or file == 'chromedriver.exe':
                        full_path = os.path.join(root, file)
                        if self._validate_chromedriver(full_path):
                            return full_path
            return None
        except Exception:
            return None
    
    def _download_chromedriver_manually(self) -> Optional[str]:
        """手动下载ChromeDriver作为备用方案"""
        try:
            system_info = self._get_system_info()
            
            # 创建ChromeDriver缓存目录
            cache_dir = Path.home() / '.chromedriver_cache'
            cache_dir.mkdir(exist_ok=True)
            
            # 获取Chrome版本
            chrome_version = self._get_chrome_version()
            if not chrome_version:
                return None
                
            major_version = chrome_version.split('.')[0]
            
            # 构建下载URL
            download_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
            
            try:
                # 获取具体版本号
                version_response = requests.get(download_url, timeout=10)
                if version_response.status_code != 200:
                    # 尝试使用较新的API
                    download_url = f"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{major_version}"
                    version_response = requests.get(download_url, timeout=10)
                    
                if version_response.status_code == 200:
                    driver_version = version_response.text.strip()
                else:
                    return None
                    
            except requests.RequestException:
                return None
            
            # 构建ChromeDriver下载URL
            if int(major_version) >= 115:
                # 新版本API
                zip_url = f"https://storage.googleapis.com/chrome-for-testing-public/{driver_version}/{system_info['arch']}/chromedriver-{system_info['arch']}.zip"
            else:
                # 旧版本API
                zip_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_{system_info['arch']}.zip"
            
            # 下载ChromeDriver
            zip_path = cache_dir / f"chromedriver_{driver_version}.zip"
            driver_dir = cache_dir / f"chromedriver_{driver_version}"
            
            if not driver_dir.exists():
                response = requests.get(zip_url, timeout=30)
                if response.status_code == 200:
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 解压
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(driver_dir)
                    
                    # 删除zip文件
                    zip_path.unlink()
                else:
                    return None
            
            # 查找chromedriver可执行文件
            for root, dirs, files in os.walk(driver_dir):
                for file in files:
                    if file == 'chromedriver' or file == 'chromedriver.exe':
                        driver_path = os.path.join(root, file)
                        if self._validate_chromedriver(driver_path):
                            return driver_path
            
            return None
            
        except Exception as e:
            print(f"手动下载ChromeDriver失败: {e}")
            return None
    
    def _get_chrome_version(self) -> Optional[str]:
        """获取Chrome版本"""
        chrome_commands = [
            'google-chrome --version',
            'google-chrome-stable --version', 
            'chromium-browser --version',
            'chromium --version'
        ]
        
        for cmd in chrome_commands:
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # 解析版本号
                    version_line = result.stdout.strip()
                    # 提取版本号 (例如: "Google Chrome 120.0.6099.109")
                    import re
                    match = re.search(r'\d+\.\d+\.\d+\.\d+', version_line)
                    if match:
                        return match.group(0)
            except Exception:
                continue
        return None
    
    def _clean_chromedriver_cache(self):
        """清理损坏的ChromeDriver缓存"""
        try:
            wdm_cache = Path.home() / '.wdm'
            if wdm_cache.exists():
                shutil.rmtree(wdm_cache)
        except Exception:
            pass
    
    def _check_chrome_available(self) -> Dict:
        """
        检查Chrome浏览器是否可用
        
        Returns:
            包含检查结果的字典
        """
        result = {
            "available": False,
            "error": None,
            "chrome_path": None,
            "driver_path": None,
            "system_info": self._get_system_info()
        }
        
        try:
            # 检查是否存在Chrome或Chromium
            chrome_commands = [
                'google-chrome',
                'google-chrome-stable', 
                'chromium-browser',
                'chromium',
                'chrome'
            ]
            
            for cmd in chrome_commands:
                chrome_path = shutil.which(cmd)
                if chrome_path:
                    result["chrome_path"] = chrome_path
                    break
            
            if not result["chrome_path"]:
                result["error"] = "未找到Chrome浏览器。请运行 './start.sh' 自动安装，或手动安装：sudo apt-get install google-chrome-stable"
                return result
            
            # 尝试获取ChromeDriver - 多种方法
            driver_path = None
            
            # 方法1: 使用WebDriver Manager
            try:
                driver_path = ChromeDriverManager().install()
                
                # 验证返回的路径
                if driver_path and not self._validate_chromedriver(driver_path):
                    # 尝试在同一目录下查找正确的chromedriver
                    correct_path = self._find_correct_chromedriver(driver_path)
                    if correct_path:
                        driver_path = correct_path
                    else:
                        driver_path = None
                        
            except Exception as e:
                print(f"WebDriver Manager失败: {e}")
                driver_path = None
            
            # 方法2: 如果WebDriver Manager失败，尝试手动下载
            if not driver_path:
                print("尝试手动下载ChromeDriver...")
                # 清理可能损坏的缓存
                self._clean_chromedriver_cache()
                driver_path = self._download_chromedriver_manually()
            
            # 方法3: 检查系统是否已安装chromedriver
            if not driver_path:
                system_chromedriver = shutil.which('chromedriver')
                if system_chromedriver and self._validate_chromedriver(system_chromedriver):
                    driver_path = system_chromedriver
            
            if driver_path:
                result["driver_path"] = driver_path
                result["available"] = True
            else:
                system_info = result["system_info"]
                result["error"] = f"ChromeDriver获取失败。系统信息: {system_info['system']}/{system_info['machine']}{'(WSL)' if system_info['is_wsl'] else ''}。请尝试手动安装ChromeDriver或联系管理员。"
            
        except Exception as e:
            result["error"] = f"Chrome检测过程中发生错误: {str(e)}"
        
        return result
    
    def _generate_html_fallback(self, html_path: str, tracking_number: str) -> str:
        """
        当Chrome不可用时，生成HTML文件作为备用方案
        
        Args:
            html_path: 临时HTML文件路径
            tracking_number: 快递单号
            
        Returns:
            永久HTML文件路径
        """
        # 生成永久HTML文件名
        html_filename = f"tracking_{tracking_number}_{datetime.datetime.now():%Y%m%d_%H%M%S}.html"
        permanent_html_path = self.html_dir / html_filename
        
        # 复制临时HTML文件到永久位置
        shutil.copy2(html_path, permanent_html_path)
        
        return str(permanent_html_path)
    
    def generate_screenshot(self, tracking_number: str, company_code: str = "ems") -> Dict:
        """
        生成物流轨迹截图
        
        Args:
            tracking_number: 快递单号
            company_code: 快递公司编码
            
        Returns:
            截图生成结果
        """
        try:
            # 1. 查询物流信息
            tracking_result = self.express_service.query_express(tracking_number, company_code)
            
            if not tracking_result["success"]:
                return {
                    "success": False,
                    "error": f"查询物流信息失败: {tracking_result['error']}",
                    "tracking_number": tracking_number
                }
            
            # 2. 生成HTML
            html_path = self._render_html(
                tracking_number=tracking_number,
                status=tracking_result["current_status"],
                sign_time=tracking_result.get("sign_time", ""),
                traces=tracking_result.get("traces", [])
            )
            
            # 3. 生成截图
            screenshot_filename = f"tracking_{tracking_number}_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
            screenshot_path = self.screenshot_dir / screenshot_filename
            
            # 调用改进的截图方法
            screenshot_result = self._html_to_png(html_path, str(screenshot_path), tracking_number)
            
            # 4. 清理临时HTML文件
            try:
                os.unlink(html_path)
            except:
                pass
            
            # 5. 处理截图结果
            response = {
                "tracking_number": tracking_number,
                "company_code": company_code,
                "is_signed": tracking_result.get("is_signed", False),
                "current_status": tracking_result["current_status"],
                "traces_count": len(tracking_result.get("traces", [])),
                "screenshot_method": screenshot_result.get("method", "unknown")
            }
            
            if screenshot_result["success"]:
                if screenshot_result.get("screenshot_path"):
                    # 成功生成PNG截图
                    file_size = Path(screenshot_result["screenshot_path"]).stat().st_size if Path(screenshot_result["screenshot_path"]).exists() else 0
                    
                    # 更新数据库中的截图信息
                    db_updated = self.tracking_service.update_screenshot_info(
                        tracking_number=tracking_number,
                        screenshot_path=screenshot_result["screenshot_path"],
                        screenshot_filename=screenshot_filename
                    )
                    
                    response.update({
                        "success": True,
                        "message": "物流轨迹截图生成成功",
                        "screenshot_path": screenshot_result["screenshot_path"],
                        "screenshot_filename": screenshot_filename,
                        "file_size": file_size,
                        "db_updated": db_updated
                    })
                elif screenshot_result.get("html_fallback_path"):
                    # 生成HTML备用文件
                    file_size = Path(screenshot_result["html_fallback_path"]).stat().st_size if Path(screenshot_result["html_fallback_path"]).exists() else 0
                    response.update({
                        "success": True,
                        "message": "截图功能不可用，已生成HTML轨迹文件",
                        "html_fallback_path": screenshot_result["html_fallback_path"],
                        "file_size": file_size,
                        "note": "Chrome浏览器不可用，已提供HTML格式的轨迹文件"
                    })
            else:
                response.update({
                    "success": False,
                    "message": "截图生成失败",
                    "error": screenshot_result.get("error", "未知错误")
                })
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"生成截图过程中发生错误: {str(e)}",
                "tracking_number": tracking_number
            }
    
    def _render_html(self, tracking_number: str, status: str, sign_time: str, traces: List[Dict]) -> str:
        """
        渲染HTML模板
        
        Args:
            tracking_number: 快递单号
            status: 当前状态
            sign_time: 签收时间
            traces: 轨迹列表
            
        Returns:
            临时HTML文件路径
        """
        # 生成时间线项目
        timeline_items = []
        for trace in traces:
            time_str = trace.get('time', '—')
            context = trace.get('context', '—')
            item_html = self.ITEM_TEMPLATE.format(time=time_str, desc=context)
            timeline_items.append(item_html)
        
        timeline_html = '\n'.join(timeline_items)
        
        # 填充模板
        html_content = self.HTML_TEMPLATE.format(
            tracking_no=tracking_number,
            status=status,
            sign_time=sign_time or '—',
            timeline_items=timeline_html
        )
        
        # 创建临时HTML文件
        fd, html_path = tempfile.mkstemp(suffix='.html', text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _html_to_png(self, html_path: str, output_path: str, tracking_number: str = "") -> Dict:
        """
        将HTML转换为PNG截图，支持Chrome检测和备用方案
        
        Args:
            html_path: HTML文件路径
            output_path: 输出PNG文件路径
            tracking_number: 快递单号（用于备用方案）
            
        Returns:
            转换结果字典
        """
        result = {
            "success": False,
            "screenshot_path": None,
            "html_fallback_path": None,
            "method": None,
            "error": None
        }
        
        # 1. 检查Chrome是否可用
        chrome_check = self._check_chrome_available()
        
        if chrome_check["available"]:
            # Chrome可用，尝试生成截图
            try:
                # 配置Chrome选项
                chrome_options = Options()
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--window-size=1280,1600')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-logging')
                chrome_options.add_argument('--disable-crash-reporter')
                
                # 创建WebDriver
                service = Service(chrome_check["driver_path"])
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                try:
                    # 加载HTML文件
                    file_url = 'file:///' + os.path.abspath(html_path)
                    driver.get(file_url)
                    driver.implicitly_wait(5)
                    
                    # 找到容器元素并截图
                    container = driver.find_element('id', 'capture-container')
                    screenshot_data = container.screenshot_as_png
                    
                    # 保存截图
                    with open(output_path, 'wb') as f:
                        f.write(screenshot_data)
                    
                    result["success"] = True
                    result["screenshot_path"] = output_path
                    result["method"] = "chrome_screenshot"
                    
                finally:
                    driver.quit()
                    
            except Exception as e:
                result["error"] = f"Chrome截图失败: {str(e)}"
                # Chrome失败，尝试备用方案
                try:
                    html_fallback_path = self._generate_html_fallback(html_path, tracking_number)
                    result["html_fallback_path"] = html_fallback_path
                    result["method"] = "html_fallback"
                    result["error"] += f"，已生成HTML备用文件: {html_fallback_path}"
                except Exception as fallback_error:
                    result["error"] += f"，HTML备用方案也失败: {str(fallback_error)}"
        else:
            # Chrome不可用，直接使用HTML备用方案
            try:
                html_fallback_path = self._generate_html_fallback(html_path, tracking_number)
                result["success"] = True
                result["html_fallback_path"] = html_fallback_path
                result["method"] = "html_fallback"
                result["error"] = f"Chrome不可用: {chrome_check['error']}。已生成HTML文件作为替代方案。"
            except Exception as e:
                result["error"] = f"Chrome不可用且HTML备用方案失败: {str(e)}"
        
        return result
    
    def batch_generate_screenshots(self, tracking_numbers: List[str], company_code: str = "ems") -> List[Dict]:
        """
        批量生成物流轨迹截图
        
        Args:
            tracking_numbers: 快递单号列表
            company_code: 快递公司编码
            
        Returns:
            截图生成结果列表
        """
        results = []
        for tracking_number in tracking_numbers:
            result = self.generate_screenshot(tracking_number, company_code)
            results.append(result)
        
        return results
    
    def generate_screenshot_from_tracking_data(self, tracking_data: Dict) -> Dict:
        """
        基于已有的物流查询数据生成截图
        
        Args:
            tracking_data: 物流查询结果数据
            
        Returns:
            截图生成结果
        """
        try:
            if not tracking_data.get("success"):
                return {
                    "success": False,
                    "error": "物流数据无效",
                    "tracking_number": tracking_data.get("tracking_number", "")
                }
            
            tracking_number = tracking_data["tracking_number"]
            
            # 生成HTML
            html_path = self._render_html(
                tracking_number=tracking_number,
                status=tracking_data["current_status"],
                sign_time=tracking_data.get("sign_time", ""),
                traces=tracking_data.get("traces", [])
            )
            
            # 生成截图
            screenshot_filename = f"tracking_{tracking_number}_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
            screenshot_path = self.screenshot_dir / screenshot_filename
            
            # 调用改进的截图方法
            screenshot_result = self._html_to_png(html_path, str(screenshot_path), tracking_number)
            
            # 清理临时HTML文件
            try:
                os.unlink(html_path)
            except:
                pass
            
            # 处理截图结果
            response = {
                "tracking_number": tracking_number,
                "company_code": tracking_data.get("company_code", ""),
                "is_signed": tracking_data.get("is_signed", False), 
                "current_status": tracking_data["current_status"],
                "traces_count": len(tracking_data.get("traces", [])),
                "screenshot_method": screenshot_result.get("method", "unknown")
            }
            
            if screenshot_result["success"]:
                if screenshot_result.get("screenshot_path"):
                    # 成功生成PNG截图
                    file_size = Path(screenshot_result["screenshot_path"]).stat().st_size if Path(screenshot_result["screenshot_path"]).exists() else 0
                    
                    # 更新数据库中的截图信息
                    db_updated = self.tracking_service.update_screenshot_info(
                        tracking_number=tracking_number,
                        screenshot_path=screenshot_result["screenshot_path"],
                        screenshot_filename=screenshot_filename
                    )
                    
                    response.update({
                        "success": True,
                        "message": "物流轨迹截图生成成功",
                        "screenshot_path": screenshot_result["screenshot_path"],
                        "screenshot_filename": screenshot_filename,
                        "file_size": file_size,
                        "db_updated": db_updated
                    })
                elif screenshot_result.get("html_fallback_path"):
                    # 生成HTML备用文件
                    file_size = Path(screenshot_result["html_fallback_path"]).stat().st_size if Path(screenshot_result["html_fallback_path"]).exists() else 0
                    response.update({
                        "success": True,
                        "message": "截图功能不可用，已生成HTML轨迹文件",
                        "html_fallback_path": screenshot_result["html_fallback_path"],
                        "file_size": file_size,
                        "note": "Chrome浏览器不可用，已提供HTML格式的轨迹文件"
                    })
            else:
                response.update({
                    "success": False,
                    "message": "截图生成失败",
                    "error": screenshot_result.get("error", "未知错误")
                })
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"生成截图过程中发生错误: {str(e)}",
                "tracking_number": tracking_data.get("tracking_number", "")
            }
    
    def cleanup_old_screenshots(self, days: int = 7) -> Dict:
        """
        清理旧的截图文件
        
        Args:
            days: 保留天数，默认7天
            
        Returns:
            清理结果
        """
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            for screenshot_file in self.screenshot_dir.glob("tracking_*.png"):
                if screenshot_file.stat().st_mtime < cutoff_time:
                    screenshot_file.unlink()
                    cleaned_count += 1
            
            return {
                "success": True,
                "message": f"成功清理 {cleaned_count} 个过期截图文件",
                "cleaned_count": cleaned_count,
                "retention_days": days
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清理截图文件失败: {str(e)}"
            }