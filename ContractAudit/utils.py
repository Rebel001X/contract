from functools import wraps
from typing import Any, Dict, Union
from fastapi import HTTPException

def unified_response(func):
    """
    统一响应格式装饰器
    自动将返回值包装为统一格式：
    {
        "code": 0,
        "data": result,
        "maxPage": 1,
        "message": ""
    }
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # 如果已经是统一格式，直接返回
            if isinstance(result, dict) and "code" in result and "data" in result:
                return result
            
            # 包装为统一格式
            return {
                "code": 0,
                "data": result,
                "maxPage": 1,
                "message": ""
            }
            
        except HTTPException as e:
            # HTTPException转换为统一错误格式
            return {
                "code": e.status_code,
                "data": None,
                "maxPage": 1,
                "message": e.detail
            }
        except Exception as e:
            # 其他异常包装为统一错误格式
            return {
                "code": 500,
                "data": None,
                "maxPage": 1,
                "message": str(e)
            }
    
    return wrapper 