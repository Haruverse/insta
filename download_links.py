# Đây là script để tải items từ link

import instaloader
import os
import yaml
import time
import requests
from pathlib import Path
import dotenv
from database import Database

# Đọc cấu hình từ file config.yml
def load_config():
    config_path = Path("config.yml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        print("[Warning] Không tìm thấy file config.yml. Sử dụng cấu hình mặc định.")
        return {
            "download": {
                "retry_times": 10,
                "timeout": 30
            },
            "avatar": True,
            "stories": True,
            "posts": True,
            "reels": True,
            "highlights": True
        }

# Tải cấu hình
config = load_config()

# Lấy cấu hình retry và timeout từ config
retry_times = config.get("download", {}).get("retry_times", 10)
timeout_seconds = config.get("download", {}).get("timeout", 30)

# Tạo thư mục downloads nếu chưa tồn tại
downloads_folder = Path("downloads")
downloads_folder.mkdir(exist_ok=True)

# Khởi tạo database
db = Database("instagram_data.db")

# Khởi tạo Instaloader
L = instaloader.Instaloader()

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

def retry_with_timeout(func, max_retries=retry_times, timeout=timeout_seconds, *args, **kwargs):
    """
    Thử lại một hàm với số lần retry giới hạn
    
    Args:
        func: Hàm cần thực thi
        max_retries: Số lần retry tối đa
        timeout: Thời gian chờ giữa các lần retry
        *args, **kwargs: Tham số cho hàm func
        
    Returns:
        Kết quả của hàm hoặc None nếu tất cả các lần retry đều thất bại
    """
    for retry in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if retry < max_retries - 1:
                print(f"[Warning] Lỗi: {e}. Thử lại lần {retry + 1}/{max_retries} sau {timeout} giây...")
                time.sleep(timeout)
            else:
                print(f"[Error] Đã thử {max_retries} lần nhưng vẫn thất bại: {e}")
                raise

def download_post(post, folder_path, user_id):
    """
    Tải post sau khi kiểm tra trong database
    
    Args:
        post: Post object từ instaloader
        folder_path: Đường dẫn lưu file
        user_id: ID của người dùng
    
    Returns:
        bool: True nếu đã tải, False nếu bỏ qua
    """
    post_id = str(post.mediaid)
    
    # Kiểm tra xem post đã tồn tại trong database chưa
    if db.get_post(user_id, post_id):
        print(f"[Info] Post {post_id} đã tồn tại trong database, bỏ qua.")
        return False
        
    # Tải post
    original_dirname_pattern = L.dirname_pattern
    L.dirname_pattern = str(folder_path)
    
    try:
        # Tải post với retry
        def download_post_item():
            L.download_post(post, target=folder_path)
        
        retry_with_timeout(download_post_item)
        
        # Lưu vào database
        post_data = {
            'mediaid': post_id,
            'typename': post.typename,
            'date_utc': post.date_utc.timestamp(),
            'caption': post.caption if post.caption else "",
            'url': post.video_url if post.is_video else post.url,
            'is_video': post.is_video
        }
        db.insert_post(user_id, post_id, post_data)
        
        # Xóa khỏi danh sách failed nếu đã tải thành công
        db.remove_failed_item(user_id, post_id, 'post')
        
        return True
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] Không thể tải post {post_id}: {error_msg}")
        db.add_failed_item(user_id, post_id, 'post', error_msg)
        return False
    finally:
        L.dirname_pattern = original_dirname_pattern

def download_reel(reel, folder_path, user_id):
    """
    Tải reel sau khi kiểm tra trong database
    
    Args:
        reel: Reel object từ instaloader
        folder_path: Đường dẫn lưu file
        user_id: ID của người dùng
    
    Returns:
        bool: True nếu đã tải, False nếu bỏ qua
    """
    reel_id = str(reel.mediaid)
    
    # Kiểm tra xem reel đã tồn tại trong database chưa
    if db.get_reel(user_id, reel_id):
        print(f"[Info] Reel {reel_id} đã tồn tại trong database, bỏ qua.")
        return False
        
    # Tải reel
    original_dirname_pattern = L.dirname_pattern
    L.dirname_pattern = str(folder_path)
    
    try:
        # Tải reel với retry
        def download_reel_item():
            L.download_post(reel, target=folder_path)  # Instaloader sử dụng cùng phương thức cho post và reel
        
        retry_with_timeout(download_reel_item)
        
        # Lưu vào database
        reel_data = {
            'mediaid': reel_id,
            'typename': reel.typename,
            'date_utc': reel.date_utc.timestamp(),
            'caption': reel.caption if reel.caption else "",
            'url': reel.video_url,
            'is_video': True
        }
        db.insert_reel(user_id, reel_id, reel_data)
        
        # Xóa khỏi danh sách failed nếu đã tải thành công
        db.remove_failed_item(user_id, reel_id, 'reel')
        
        return True
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] Không thể tải reel {reel_id}: {error_msg}")
        db.add_failed_item(user_id, reel_id, 'reel', error_msg)
        return False
    finally:
        L.dirname_pattern = original_dirname_pattern

def download_profile_avatar(profile, account_folder):
    """
    Tải avatar sau khi kiểm tra trong database
    
    Args:
        profile: Profile object từ instaloader
        account_folder: Đường dẫn lưu file
    
    Returns:
        bool: True nếu đã tải, False nếu bỏ qua
    """
    user_id = str(profile.userid)
    
    try:
        # Lấy profile pic URL với retry
        def get_profile_pic():
            return profile.get_profile_pic_url()
        
        profile_pic_url = retry_with_timeout(get_profile_pic)
        
        # Kiểm tra xem avatar đã tồn tại trong database chưa
        stored_url = db.get_avatar(user_id)
        if stored_url and stored_url == profile_pic_url:
            print(f"[Info] Avatar của {profile.username} không thay đổi, bỏ qua.")
            return False
        
        # Tải avatar mới
        if profile_pic_url:
            avatar_path = os.path.join(account_folder, f"{profile.username}_avatar.jpg")
            
            def download_avatar_image():
                response = requests.get(profile_pic_url, timeout=timeout_seconds)
                if response.status_code == 200:
                    with open(avatar_path, "wb") as f:
                        f.write(response.content)
                return response.status_code
            
            status_code = retry_with_timeout(download_avatar_image)
            
            if status_code == 200:
                # Lưu vào database
                db.insert_avatar(user_id, profile_pic_url)
                
                # Xóa khỏi danh sách failed nếu đã tải thành công
                db.remove_failed_item(user_id, 'avatar', 'avatar')
                
                print(f"[Info] Đã tải avatar vào {avatar_path}")
                return True
        
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] Không thể tải avatar: {error_msg}")
        db.add_failed_item(user_id, 'avatar', 'avatar', error_msg)
        return False

def download_from_link(link):
    """
    Tải nội dung từ một link Instagram
    
    Args:
        link: URL của nội dung Instagram
    """
    try:
        print(f"[Info] Xử lý link: {link}")
        
        # Kiểm tra loại link (post, reel, story, highlight, profile)
        if "/p/" in link or "/reel/" in link:
            # Link là post hoặc reel
            shortcode = link.split("/")[-2]  # Lấy shortcode từ link
            
            def get_post_from_shortcode():
                return instaloader.Post.from_shortcode(L.context, shortcode)
            
            post = retry_with_timeout(get_post_from_shortcode)
            
            # Lấy thông tin user từ post
            user_id = str(post.owner_id)
            username = post.owner_username
            
            # Tạo thư mục đích
            account_folder = downloads_folder.joinpath(username)
            account_folder.mkdir(exist_ok=True)
            
            if post.is_video and config.get("reels", True):
                # Nếu là video (reel)
                reels_folder = account_folder.joinpath("reels")
                reels_folder.mkdir(exist_ok=True)
                
                if download_reel(post, reels_folder, user_id):
                    print(f"[Info] Đã tải reel {shortcode} của {username}")
                else:
                    print(f"[Info] Bỏ qua reel {shortcode} (đã tồn tại hoặc lỗi)")
            elif config.get("posts", True):
                # Nếu là post thường
                posts_folder = account_folder.joinpath("posts")
                posts_folder.mkdir(exist_ok=True)
                
                if download_post(post, posts_folder, user_id):
                    print(f"[Info] Đã tải post {shortcode} của {username}")
                else:
                    print(f"[Info] Bỏ qua post {shortcode} (đã tồn tại hoặc lỗi)")
        
        elif link.endswith('/'):
            # Link là profile
            username = link.split("/")[-2]
            if not username:
                print(f"[Error] Không thể xác định username từ link: {link}")
                return
                
            print(f"[Info] Đang tải thông tin profile của {username}")
            
            def get_profile():
                return instaloader.Profile.from_username(L.context, username)
            
            profile = retry_with_timeout(get_profile)
            
            # Tạo thư mục đích
            account_folder = downloads_folder.joinpath(username)
            account_folder.mkdir(exist_ok=True)
            
            # Tải avatar nếu được bật trong config
            if config.get("avatar", True):
                if download_profile_avatar(profile, account_folder):
                    print(f"[Info] Đã tải avatar của {username}")
                else:
                    print(f"[Info] Bỏ qua avatar của {username} (đã tồn tại hoặc lỗi)")
        
        else:
            print(f"[Warning] Định dạng link không được hỗ trợ: {link}")
    
    except Exception as e:
        print(f"[Error] Không thể xử lý link {link}: {e}")

def main():
    # Đọc danh sách link từ file links.txt
    try:
        with open("links.txt", "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        # Tạo file rỗng nếu không tồn tại
        open("links.txt", "w", encoding="utf-8").close()
        links = []
        print("[Warning] File links.txt không tồn tại. Đã tạo file mới.")
    
    if not links:
        print("[Info] Không có link nào để tải. Vui lòng thêm links vào file links.txt")
        return
    
    # Tải từng link
    for link in links:
        download_from_link(link)
        time.sleep(2)  # Delay giữa mỗi link
    
    # Đóng kết nối database
    db.close()
    print("[Info] Hoàn tất tải từ links")

if __name__ == "__main__":
    main()
