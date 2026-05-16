import time
from functools import wraps

def log_execution_time(func):
    """Decorator để đo thời gian chạy của hàm"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️ [Timer] {func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def retry_on_failure(max_retries=3, delay=2):
    """Decorator để thử lại khi gọi API thất bại"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    print(f"⚠️ [Retry] {func.__name__} failed (attempt {retries}/{max_retries}). Error: {e}")
                    if retries >= max_retries:
                        raise e
                    time.sleep(delay)
        return wrapper
    return decorator
