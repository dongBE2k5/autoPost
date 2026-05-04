# services/tiktok_service.py
import random
import time
import requests
from apify_client import ApifyClient

class TikTokService:
    def __init__(self, apify_token):
        self.apify_token = apify_token

    # THÊM THAM SỐ min_views=30000 VÀO ĐÂY
    def fetch_trending_videos(self, keyword, max_videos, min_views=30000, log_cb=print):
        """
        Cào video TikTok. Tự động Fallback nếu cách 1 lỗi.
        Có chức năng lọc theo lượt xem tối thiểu (min_views).
        """
        videos_data = []
        search_keyword = keyword if keyword else "viral"

        try:
            # --- PHƯƠNG ÁN A ---
            log_cb(f"B1: [Apify] Đang tìm {max_videos} video (Phương án A)...")
            client = ApifyClient(self.apify_token)
            run_input = {
                "trendType": "videos",
                "maxItems": max_videos * 2, # Lấy dư ra để lọc
                "maxResults": max_videos * 2,       
                "resultsPerPage": max_videos * 2,   
                "limit": max_videos * 2,            
                "countryCode": "VN",
                "hashtagPeriod": "7",
                "videoSortBy": "vv",
                "proxyConfiguration": { "useApifyProxy": True },
            }

            run = client.actor("GULLsEZsAD69QFACQ").call(run_input=run_input)
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                v_link = item.get("TikTok URL_video", "")
                
                # Phương án A thường không trả về số view rõ ràng, nên ta ưu tiên lấy link trước
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
            # --- PHƯƠNG ÁN B (FALLBACK VỚI LỌC VIEW) ---
            log_cb(f"⚠️ Phương án A lỗi ({str(e_primary)[:30]}). Chuyển sang Phương án B (Clockworks)...")
            
            KEYWORDS = ["xuhuong", "trend", "fyp", "viral", "hot tiktok", "tiktok vietnam","vietnam","xh"]
            fallback_keyword = keyword if keyword else random.choice(KEYWORDS)
            
            log_cb(f"-> [Fallback] Đang quét từ khóa: {fallback_keyword}")
            run_url = f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs?token={self.apify_token}"

            payload = {
                "searchQueries": [fallback_keyword],
                "resultsPerPage": max_videos, # Yêu cầu nhiều hơn để trừ hao những video bị lọc
                "proxyCountryCode": "VN",
                "searchSection": "/video",
                "searchSorting": "1",
                "searchDatePosted": "2",
            }

            res = requests.post(run_url, json=payload)
            data = res.json()

            if "data" not in data:
                raise Exception(f"Fallback API khởi tạo lỗi: {data}")

            run_id = data["data"]["id"]
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={self.apify_token}"

            while True:
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
            
            # --- LOGIC LỌC VIEW ---
            for v in fb_videos:
                video_url = v.get("webVideoUrl")
                views = v.get("playCount", 0)
                
                if not video_url: continue
                
                # Bỏ qua nếu view thấp hơn ngưỡng
                if views < min_views:
                    continue

                videos_data.append({
                    "link": video_url,
                    "desc": v.get("text", "Không có mô tả"),
                    "creator": v.get("authorMeta", {}).get("name", "Không xác định"),
                    "views": views
                })
                if len(videos_data) >= max_videos:
                    break

            # --- FALLBACK TẦNG 2: Nếu bộ lọc quá gắt khiến list rỗng ---
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