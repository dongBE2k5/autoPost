from apify_client import ApifyClient
import os
from dotenv import load_dotenv

load_dotenv()
token_tiktok = os.getenv("TOKEN_TIKTOK")
# Khởi tạo ApifyClient với API token của bạn
client = ApifyClient(token_tiktok)

# Prepare the Actor input
run_input = {
    "trendType": "videos",
    "maxItems": 5,
    "countryCode": "VN",
    "hashtagPeriod": "7",
    "industryId": "",
    "showOnlyNew": False,
    "videoCountryCode": "VN",
    "videoPeriod": "7",
    "videoSortBy": "vv",
    "creatorCountryCode": "VN",
    "creatorAudienceCountry": "",
    "creatorSortBy": "follower",
    "proxyConfiguration": { "useApifyProxy": True },
}

# Run the Actor and wait for it to finish
run = client.actor("GULLsEZsAD69QFACQ").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item.get("TikTok URL_video", ""),'\n')