import hashlib
import json
import os
import time
import requests
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings


class ExpressTrackingService:
    """快递追踪服务类，封装快递100 API调用功能"""
    
    # 快递100授权信息
    KUAIDI_KEY = "GUpgAlsJ4403"
    KUAIDI_CUSTOMER = "5813A47FED91DD26A0EF340F2A194938"
    
    # 缓存设置
    CACHE_TTL = 30 * 60  # 30分钟缓存有效期
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_dir = Path(settings.UPLOAD_DIR) / "express_cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def _md5(self, s: str) -> str:
        """生成MD5摘要"""
        return hashlib.md5(s.encode()).hexdigest().upper()
    
    def _sign(self, param_str: str) -> str:
        """生成API签名"""
        return self._md5(param_str + self.KUAIDI_KEY + self.KUAIDI_CUSTOMER)
    
    def _cache_path(self, tracking_number: str, company_code: str) -> Path:
        """获取缓存文件路径"""
        filename = f"{company_code}_{tracking_number}.json"
        return self.cache_dir / filename
    
    def _load_cache(self, tracking_number: str, company_code: str) -> Optional[Dict]:
        """加载缓存数据"""
        cache_path = self._cache_path(tracking_number, company_code)
        
        if cache_path.exists() and time.time() - cache_path.stat().st_mtime < self.CACHE_TTL:
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def _save_cache(self, tracking_number: str, company_code: str, data: Dict) -> None:
        """保存缓存数据"""
        cache_path = self._cache_path(tracking_number, company_code)
        try:
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 缓存失败不影响主要功能
    
    def query_express(self, tracking_number: str, company_code: str = "ems") -> Dict:
        """
        查询快递物流信息
        
        Args:
            tracking_number: 快递单号
            company_code: 快递公司编码，默认为ems
            
        Returns:
            包含查询结果的字典
        """
        company_code = company_code.strip().lower() or "ems"
        
        try:
            # 1. 尝试读取缓存
            cached_data = self._load_cache(tracking_number, company_code)
            if cached_data:
                return self._format_response(cached_data, tracking_number, company_code, from_cache=True)
            
            # 2. 请求快递100 API
            param = {
                "com": company_code,
                "num": tracking_number,
                "phone": "",
                "from": "",
                "to": "",
                "resultv2": "1",
                "show": "0",
                "order": "desc"
            }
            param_str = json.dumps(param, ensure_ascii=False)
            payload = {
                "customer": self.KUAIDI_CUSTOMER,
                "param": param_str,
                "sign": self._sign(param_str),
            }
            
            url = "https://poll.kuaidi100.com/poll/query.do"
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            
            api_result = response.json()
            
            # 3. 保存缓存
            self._save_cache(tracking_number, company_code, api_result)
            
            # 4. 格式化返回结果
            return self._format_response(api_result, tracking_number, company_code, from_cache=False)
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"网络请求失败: {str(e)}",
                "tracking_number": tracking_number,
                "company_code": company_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"查询过程中发生错误: {str(e)}",
                "tracking_number": tracking_number,
                "company_code": company_code
            }
    
    def _format_response(self, api_result: Dict, tracking_number: str, company_code: str, from_cache: bool = False) -> Dict:
        """格式化API返回结果"""
        try:
            state = api_result.get("state")
            message = api_result.get("message", "")
            status = api_result.get("status")
            data = api_result.get("data", [])
            
            # 判断是否成功
            if status == "200" or state is not None:
                # 解析物流状态
                is_signed = state == "3"  # 3表示已签收
                sign_time = data[0]["time"] if is_signed and data else ""
                
                # 转换状态描述
                status_map = {
                    "0": "在途",
                    "1": "揽收", 
                    "2": "疑难",
                    "3": "已签收",
                    "4": "退签",
                    "5": "派件",
                    "8": "清关",
                    "14": "拒签"
                }
                current_status = status_map.get(str(state), f"状态{state}")
                
                return {
                    "success": True,
                    "tracking_number": tracking_number,
                    "company_code": company_code,
                    "current_status": current_status,
                    "is_signed": is_signed,
                    "sign_time": sign_time,
                    "last_update": datetime.now().isoformat(),
                    "traces": data,
                    "raw_data": api_result,
                    "from_cache": from_cache,
                    "message": "查询成功"
                }
            else:
                return {
                    "success": False,
                    "error": message or "快递100查询失败",
                    "tracking_number": tracking_number,
                    "company_code": company_code,
                    "raw_data": api_result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"解析API结果失败: {str(e)}",
                "tracking_number": tracking_number,
                "company_code": company_code,
                "raw_data": api_result
            }
    
    def batch_query_express(self, tracking_numbers: List[str], company_code: str = "ems") -> List[Dict]:
        """
        批量查询快递物流信息
        
        Args:
            tracking_numbers: 快递单号列表
            company_code: 快递公司编码
            
        Returns:
            查询结果列表
        """
        results = []
        for tracking_number in tracking_numbers:
            result = self.query_express(tracking_number, company_code)
            results.append(result)
        
        return results
    
    def get_company_code_by_number(self, tracking_number: str) -> str:
        """
        根据快递单号推断快递公司编码
        
        Args:
            tracking_number: 快递单号
            
        Returns:
            快递公司编码
        """
        tracking_number = tracking_number.strip().upper()
        
        # EMS单号格式：2个字母+9个数字+2个字母 或 纯数字
        if len(tracking_number) == 13 and tracking_number[:2].isalpha() and tracking_number[-2:].isalpha():
            return "ems"
        elif tracking_number.isdigit() and len(tracking_number) >= 10:
            return "ems"
        
        # 顺丰速运：SF开头+12位数字
        elif tracking_number.startswith("SF") and len(tracking_number) == 14:
            return "shunfeng"
        
        # 中通快递：12位纯数字
        elif tracking_number.isdigit() and len(tracking_number) == 12:
            return "zhongtong"
        
        # 圆通速递：YT开头或10位数字
        elif tracking_number.startswith("YT") or (tracking_number.isdigit() and len(tracking_number) == 10):
            return "yuantong"
        
        # 申通快递：268开头+12位数字
        elif tracking_number.startswith("268") and len(tracking_number) == 15:
            return "shentong"
        
        # 韵达速递：13位数字
        elif tracking_number.isdigit() and len(tracking_number) == 13:
            return "yunda"
        
        # 默认返回EMS
        else:
            return "ems"
    
    def clear_cache(self, tracking_number: str = None, company_code: str = None) -> Dict:
        """
        清理缓存
        
        Args:
            tracking_number: 指定清理的快递单号，为None时清理所有
            company_code: 指定清理的快递公司，为None时清理所有
            
        Returns:
            清理结果
        """
        try:
            cleared_count = 0
            
            if tracking_number and company_code:
                # 清理指定单号的缓存
                cache_path = self._cache_path(tracking_number, company_code)
                if cache_path.exists():
                    cache_path.unlink()
                    cleared_count = 1
            else:
                # 清理所有缓存
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                    cleared_count += 1
            
            return {
                "success": True,
                "message": f"成功清理 {cleared_count} 个缓存文件",
                "cleared_count": cleared_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清理缓存失败: {str(e)}"
            }