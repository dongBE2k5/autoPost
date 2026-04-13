from TikTokApi import TikTokApi
import asyncio
import os
from datetime import datetime, timedelta

ms_token = os.getenv("ms_token")

async def trending_videos():

    now = datetime.now()
    time_24h = now - timedelta(hours=24)
    time_72h = now - timedelta(hours=72)

    async with TikTokApi() as api:

        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=5,
            browser="chromium",
            headless=False   # 👈 QUAN TRỌNG
        )

        async for video in api.trending.videos(count=50):

            data = video.as_dict

            # chuyển timestamp → datetime
            create_time = datetime.fromtimestamp(data["createTime"])

            if time_72h <= create_time <= time_24h:

                user_id = data["author"]["uniqueId"]
                video_id = data["id"]

                video_url = f"https://www.tiktok.com/@{user_id}/video/{video_id}"

                print(f"Description: {data['desc']}")
                print(f"Views: {data['stats']['playCount']}")
                print(f"Created: {create_time}")
                print(f"URL: {video_url}")
                print("-"*30)

if __name__ == "__main__":
    asyncio.run(trending_videos())