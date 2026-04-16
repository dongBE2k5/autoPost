import requests
import time
import random



# =========================
# CONFIG
# =========================
KEYWORDS = [
    "xuhuong",
    "trend",
    "fyp",
    "viral",
    "hot tiktok",
    "tiktok vietnam"
]

MAX_VIDEOS = 30
MIN_VIEWS = 10000

# =========================
# 1. CHỌN KEYWORD NGẪU NHIÊN
# =========================
keyword = random.choice(KEYWORDS)

print("🔍 Keyword:", keyword)

run_url = f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs?token={API_TOKEN}"

payload = {
    "searchQueries": [keyword],

    "resultsPerPage": MAX_VIDEOS,

    "proxyConfiguration": {
        "useApifyProxy": True,
        "apifyProxyGroups": ["RESIDENTIAL"],
        "countryCode": "VN"
    }
}

res = requests.post(run_url, json=payload)
data = res.json()

if "data" not in data:
    print("❌ API lỗi:", data)
    exit()

run_id = data["data"]["id"]

# =========================
# 2. WAIT
# =========================
status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={API_TOKEN}"

while True:
    status_res = requests.get(status_url).json()
    status = status_res["data"]["status"]

    print("⏳", status)

    if status == "SUCCEEDED":
        break
    elif status in ["FAILED", "ABORTED"]:
        print("❌ Actor lỗi")
        exit()

    time.sleep(3)

# =========================
# 3. GET DATA
# =========================
dataset_id = status_res["data"]["defaultDatasetId"]
dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={API_TOKEN}"

videos = requests.get(dataset_url).json()

print("\n🔥 Tổng video:", len(videos))

# =========================
# 4. LỌC VIDEO
# =========================
count = 0

for v in videos:
    video_url = v.get("webVideoUrl")
    download_url = v.get("videoUrl")
    text = v.get("text", "")
    views = v.get("playCount", 0)
    likes = v.get("diggCount", 0)

    if not video_url:
        continue

    if views < MIN_VIEWS:
        continue

    count += 1

    print(f"\n🔥 VIDEO #{count}")
    print("📌 Caption:", text[:80])
    print("🎬 Xem:", video_url)
    print("⬇️ Tải:", download_url)
    print("👁 Views:", views)
    print("❤️ Likes:", likes)

# =========================
# 5. FALLBACK
# =========================
if count == 0:
    print("\n⚠️ Không lọc được → show top video\n")

    for i, v in enumerate(videos[:10], 1):
        print(f"\n🔥 VIDEO #{i}")
        print("🎬", v.get("webVideoUrl"))