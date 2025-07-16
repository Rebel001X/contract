def unified_response(func):
    """
    简单的统一响应装饰器示例。
    实际项目可根据需要扩展。
    """
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper 