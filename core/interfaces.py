from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable

class IVideoScraper(ABC):
    @abstractmethod
    def fetch_trending_videos(self, keyword: str, max_videos: int, min_views: int = 30000, log_cb: Callable = print, stop_cb: Callable = None, search_queries: List[str] = None, hashtags: List[str] = None) -> List[Dict[str, Any]]:
        """Lấy danh sách video trending"""
        pass

class ITextModel(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass

class IImageModel(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, aspect_ratio: str, style: str) -> bytes:
        pass

class IVideoModel(ABC):
    @abstractmethod
    def generate_video(self, prompt: str, negative_prompt: str) -> bytes:
        pass
