# Script này để fast scrape. Không có database. Không có delay.
# Khuyến khích dùng 1 lần.
# Vì không có delay nên rất dễ bị instagram restrict.

import instaloader
import os
import requests
from pathlib import Path
import dotenv

# Initialize Instaloader
L = instaloader.Instaloader()  # Đặt mức độ log để xem thông tin chi tiết hơn về lỗi

# Đọc thông tin đăng nhập từ file .env nếu tồn tại
env_file = Path(".env")
if env_file.exists():
    dotenv.load_dotenv()
    
    L.context._session.cookies.set("csrftoken", os.getenv("IG_CSRFTOKEN", ""))
    L.context._session.cookies.set("sessionid", os.getenv("IG_SESSIONID", ""))
    L.context._session.cookies.set("ds_user_id", os.getenv("IG_DS_USER_ID", ""))
    L.context._session.cookies.set("mid", os.getenv("IG_MID", ""))
    L.context._session.cookies.set("ig_did", os.getenv("IG_DID", ""))
    
    # Đặt username từ env
    L.context.username = os.getenv("IG_USERNAME", "your_username")
else:
    # Tạo file .env mẫu nếu chưa tồn tại
    with open(".env", "w") as env_file:
        env_file.write("""# Instagram credentials
IG_USERNAME=your_username
IG_CSRFTOKEN=
IG_SESSIONID=
IG_DS_USER_ID=
IG_MID=
IG_DID=
""")
    
    print("[Info] Đã tạo file .env mẫu. Vui lòng cập nhật thông tin đăng nhập vào file này.")
    L.context.username = "your_username"


# Đọc danh sách tài khoản từ file
with open("list_accounts.txt", "r") as f:
    accounts = [line.strip() for line in f if line.strip()]  # Bỏ dòng trống

for username in accounts:
    print(f"\nTải dữ liệu từ tài khoản: {username}")
    try:
        # Lấy profile
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"User: {profile.username}, Followers: {profile.followers}")
        
        # Tạo thư mục chính cho tài khoản
        account_folder = f"{profile.username}"
        os.makedirs(account_folder, exist_ok=True)

        # Tạo các thư mục con
        stories_folder = os.path.join(account_folder, "stories")
        highlights_folder = os.path.join(account_folder, "highlights")
        posts_folder = os.path.join(account_folder, "posts")
        reels_folder = os.path.join(account_folder, "reels")

        os.makedirs(stories_folder, exist_ok=True)
        os.makedirs(highlights_folder, exist_ok=True)
        os.makedirs(posts_folder, exist_ok=True)
        os.makedirs(reels_folder, exist_ok=True)

        # Tải avatar bằng requests
        profile_pic_url = profile.get_profile_pic_url()
        if profile_pic_url:
            avatar_path = os.path.join(account_folder, f"{profile.username}_avatar.jpg")
            response = requests.get(profile_pic_url)
            if response.status_code == 200:
                with open(avatar_path, "wb") as f:
                    f.write(response.content)

        # Tải stories
        story_count = 0
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                L.download_storyitem(item, target=stories_folder)
                story_count += 1
        print(f"Total stories: {story_count}")

        # Tải posts
        post_count = 0
        for post in profile.get_posts():
            L.download_post(post, target=posts_folder)
            post_count += 1
        print(f"Total posts: {post_count}")

        # Tải highlights
        highlight_count = 0
        for highlight in profile.get_highlights():
            for item in highlight.get_items():
                L.download_storyitem(item, target=highlights_folder)
                highlight_count += 1
        print(f"Total highlights: {highlight_count}")

        # Tải reels
        reels_count = 0
        for reel in profile.get_reels():
            L.download_post(reel, target=reels_folder)
            reels_count += 1
        print(f"Total reels: {reels_count}")

    except Exception as e:
        print(f"Lỗi khi tải từ {username}: {e}")
