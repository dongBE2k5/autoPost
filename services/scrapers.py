import random
import time
import requests
from typing import List, Dict, Any, Callable
from apify_client import ApifyClient
from core.interfaces import IVideoScraper
from utils.decorators import log_execution_time, retry_on_failure

class TikTokScraper(IVideoScraper):
    def __init__(self, apify_token: str):
        self.apify_token = apify_token

    @log_execution_time
    @retry_on_failure(max_retries=2, delay=3)
    def fetch_trending_videos(self, keyword: str, max_videos: int, min_views: int = 30000, log_cb: Callable = print, stop_cb: Callable = None, search_queries: List[str] = None, hashtags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Cào video TikTok. Tự động Fallback nếu cách 1 lỗi.
        Tuân thủ IVideoScraper.
        """
        videos_data = []
        search_keyword = keyword if keyword else "viral"

        try:
            if stop_cb and stop_cb(): raise Exception("Stopped")
            log_cb(f"B1: [Apify] Đang tìm {max_videos} video (Phương án A)...")
            client = ApifyClient(self.apify_token)
            run_input = {
                "trendType": "videos",
                "maxItems": max_videos * 2,
                "maxResults": max_videos * 2,
                "resultsPerPage": max_videos * 2,
                "limit": max_videos * 2,
                "countryCode": "VN",
                "hashtagPeriod": "7",
                "videoSortBy": "vv",
                "proxyConfiguration": { "useApifyProxy": True },
            }
            if hashtags:
                run_input["hashtags"] = hashtags
                log_cb(f"🏷️ Dùng hashtags tùy chỉnh: {', '.join(hashtags[:5])}{'...' if len(hashtags) > 5 else ''}")

            run = client.actor("GULLsEZsAD69QFACQ").call(run_input=run_input)
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                v_link = item.get("TikTok URL_video", "")
                if v_link:
                    author_info = item.get("author", {})
                    creator = author_info.get("nickname", "Không xác định") if isinstance(author_info, dict) else "Không xác định"
                    videos_data.append({
                        "link": v_link,
                        "desc": item.get("Title_video", "Không có mô tả"),
                        "creator": creator
                    })
                if len(videos_data) >= max_videos:
                    break
            
            if not videos_data:
                raise Exception("Không tìm thấy video nào ở Phương án A.")
                
        except Exception as e_primary:
            if str(e_primary) == "Stopped": raise e_primary
            if stop_cb and stop_cb(): raise Exception("Stopped")
            log_cb(f"⚠️ Phương án A lỗi ({str(e_primary)[:30]}). Chuyển sang Phương án B (Clockworks)...")
            
            DEFAULT_KEYWORDS = ["xuhuong", "trend", "fyp", "viral", "hot tiktok", "tiktok vietnam", "vietnam", "xh"]
            fallback_keyword = keyword if keyword else random.choice(DEFAULT_KEYWORDS)

            if search_queries:
                queries_to_use = search_queries
                log_cb(f"🔍 Dùng {len(queries_to_use)} search queries tùy chỉnh.")
            else:
                queries_to_use = [fallback_keyword]
                log_cb(f"-> [Fallback] Đang quét từ khóa: {fallback_keyword}")

            run_url = f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs?token={self.apify_token}"

            payload = {
                "commentsPerPost": 0,
                "excludePinnedPosts": True,
                "maxProfilesPerQuery": 1,
                "proxyCountryCode": "VN",
                "resultsPerPage": max_videos / 2,
                "scrapeRelatedVideos": True,
                "searchQueries": queries_to_use,
                "searchSection": "/video",
                "shouldDownloadAvatars": False,
                "shouldDownloadCovers": False,
                "shouldDownloadMusicCovers": False,
                "shouldDownloadSlideshowImages": False,
                "shouldDownloadVideos": False,
                "videoSearchDateFilter": "PAST_WEEK",
                "videoSearchSorting": "MOST_RELEVANT"
            }
            if hashtags:
                payload["hashtags"] = hashtags

            res = requests.post(run_url, json=payload)
            data = res.json()

            if "data" not in data:
                raise Exception(f"Fallback API khởi tạo lỗi: {data}")

            run_id = data["data"]["id"]
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={self.apify_token}"

            while True:
                if stop_cb and stop_cb(): raise Exception("Stopped")
                status_res = requests.get(status_url).json()
                status = status_res["data"]["status"]
                log_cb(f"-> [Fallback] Trạng thái: {status} ⏳...")

                if status == "SUCCEEDED":
                    break
                elif status in ["FAILED", "ABORTED"]:
                    raise Exception("Fallback Actor chạy thất bại.")
                time.sleep(3)

            dataset_id = status_res["data"]["defaultDatasetId"]
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={self.apify_token}"
            
            fb_videos = requests.get(dataset_url).json()
            log_cb(f"-> [Fallback] Lấy được {len(fb_videos)} video thô. Đang lọc view >= {min_views}...")
            
            for v in fb_videos:
                video_url = v.get("webVideoUrl")
                views = v.get("playCount", 0)
                
                if not video_url: continue
                if views < min_views: continue

                videos_data.append({
                    "link": video_url,
                    "desc": v.get("text", "Không có mô tả"),
                    "creator": v.get("authorMeta", {}).get("name", "Không xác định"),
                    "views": views
                })
                if len(videos_data) >= max_videos:
                    break

            if not videos_data and fb_videos:
                log_cb(f"⚠️ Không có video nào đạt {min_views} view. Đang tự động vớt video top đầu...")
                for v in fb_videos:
                    video_url = v.get("webVideoUrl")
                    if not video_url: continue

                    videos_data.append({
                        "link": video_url,
                        "desc": v.get("text", "Không có mô tả"),
                        "creator": v.get("authorMeta", {}).get("name", "Không xác định"),
                        "views": v.get("playCount", 0)
                    })
                    if len(videos_data) >= max_videos:
                        break

            if not videos_data:
                raise Exception("Không tìm thấy video TikTok nào (Cả 2 cách đều thất bại)!")

        log_cb(f"✅ Xong: Đã chốt được {len(videos_data)} video chất lượng cao.")
        for i, v in enumerate(videos_data, 1):
            desc_short = v['desc'].replace('\n', ' ')
            desc_short = desc_short[:60] + "..." if len(desc_short) > 60 else desc_short
            log_cb(f"   🎬 Video {i} | Tác giả: {v['creator']} | Nội dung: {desc_short}")
            
        return videos_data
