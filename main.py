import instaloader
import os
import requests
import time 
import random
import json
import yaml
import dotenv
from pathlib import Path
from database import Database

# Đảm bảo các thư mục cần thiết tồn tại
def setup_directories():
    """Tạo các thư mục và tệp cần thiết cho ứng dụng"""
    # Lấy đường dẫn của thư mục hiện tại
    base_dir = Path(__file__).parent.absolute()
    
    # Tạo thư mục downloads
    downloads_folder = base_dir / "downloads"
    downloads_folder.mkdir(exist_ok=True)
    
    # Tạo file mẫu nếu chưa tồn tại
    for file_name in ["list_accounts.txt", "check_accounts.txt", "links.txt"]:
        file_path = base_dir / file_name
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                pass
                
    print("[Info] Đã thiết lập cấu trúc thư mục.")

# Đọc cấu hình từ file config.yml
def load_config():
    config_path = Path("config.yml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        # Tạo file config mẫu nếu chưa tồn tại
        default_config = {
            "download": {
                "retry_times": 10,
                "timeout": 30
            },
            "avatar": True,
            "stories": True,
            "posts": True,
            "reels": True,
            "highlights": True,
            "sources": ["list_accounts.txt", "links.txt", "check_accounts.txt"]
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            
        print(f"[Info] Đã tạo file config mẫu {config_path}")
        return default_config

# Tải cấu hình
config = load_config()

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

# Cấu hình độ trễ
micro_delay = random.uniform(2.5, 4.0)       # Delay giữa mỗi item
macro_delay = random.uniform(10, 20)         # Delay giữa từng loại: reels, post, story
account_delay = random.uniform(40, 80)       # Delay giữa mỗi account

# Lấy cấu hình retry và timeout từ config
retry_times = config.get("download", {}).get("retry_times", 10)
timeout_seconds = config.get("download", {}).get("timeout", 30)

# Đọc cấu hình download options
download_avatar = config.get("avatar", True)
download_stories = config.get("stories", True)
download_posts = config.get("posts", True)
download_reels = config.get("reels", True)
download_highlights = config.get("highlights", True)

# Hàm đọc danh sách tài khoản từ file
def read_accounts_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[Warning] Không tìm thấy file {file_path}, tạo file trống.")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                pass
            return []
        except PermissionError:
            print(f"[Error] Không có quyền tạo file {file_path}. Bỏ qua.")
            return []
    except PermissionError:
        print(f"[Error] Không có quyền đọc file {file_path}. Bỏ qua.")
        return []
    except Exception as e:
        print(f"[Error] Lỗi khi đọc file {file_path}: {e}. Bỏ qua.")
        return []

# Đọc danh sách tài khoản từ các file nguồn
accounts = []
check_accounts = []
links = []

for source in config.get("sources", []):
    if source == "check_accounts.txt":
        check_accounts = read_accounts_from_file(source)
    elif source == "links.txt":
        links = read_accounts_from_file(source)
    else:
        accounts.extend(read_accounts_from_file(source))

# Loại bỏ tài khoản trùng lặp
accounts = list(set(accounts))
check_accounts = list(set(check_accounts))

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

def download_story_content(items, folder_path, target_username, user_id):
    """
    Tải các nội dung story sau khi kiểm tra trong database
    
    Args:
        items: Danh sách các story item
        folder_path: Đường dẫn lưu file
        target_username: Tên người dùng
        user_id: ID của người dùng
    
    Returns:
        int: Số lượng story đã tải
    """
    original_dirname_pattern = L.dirname_pattern
    count = 0
    downloaded_stories_ids = set(db.get_all_downloaded_story_ids(user_id))
    
    # Kiểm tra xem đã có stories trong database chưa
    # Nếu chưa, không cần kiểm tra timestamp
    has_stories_in_db = len(downloaded_stories_ids) > 0
    
    try:
        L.dirname_pattern = str(folder_path)
        for item in items:
            story_id = str(item.mediaid)
            story_date = item.date_utc.timestamp()
            
            # Kiểm tra xem story đã tồn tại trong database chưa
            if story_id in downloaded_stories_ids:
                print(f"[Info] Story {story_id} đã tồn tại trong database, bỏ qua.")
                continue
            
            # Nếu đã có stories trong database, kiểm tra timestamp
            if has_stories_in_db:
                latest_timestamp = db.get_latest_timestamp(user_id, 'stories')
                if latest_timestamp > 0 and story_date <= latest_timestamp:
                    # Xác minh lại rằng có thực sự tồn tại story với timestamp này
                    has_story_with_timestamp = False
                    for existing_story_id in downloaded_stories_ids:
                        existing_story = db.get_story(user_id, existing_story_id)
                        if existing_story and 'date_utc' in existing_story and existing_story['date_utc'] == latest_timestamp:
                            has_story_with_timestamp = True
                            break
                    
                    if has_story_with_timestamp:
                        print(f"[Info] Story {story_id} cũ hơn timestamp đã lưu ({story_date} <= {latest_timestamp}), bỏ qua.")
                        continue
                    else:
                        print(f"[Info] Không tìm thấy story với timestamp {latest_timestamp} trong database, tiếp tục tải.")
                
            try:
                # Tải story với retry
                def download_story():
                    L.download_storyitem(item, target=target_username)
                    
                retry_with_timeout(download_story)
                
                # Lưu vào database - CHỈ sau khi đã tải thành công
                story_data = {
                    'mediaid': story_id,
                    'typename': item.typename,
                    'date_utc': story_date,
                    'url': item.video_url if item.is_video else item.url,
                    'is_video': item.is_video
                }
                db.insert_story(user_id, story_id, story_data)
                
                # Xóa khỏi danh sách failed nếu đã tải thành công
                db.remove_failed_item(user_id, story_id, 'story')
                
                count += 1
            except Exception as e:
                error_msg = str(e)
                print(f"[Error] Không thể tải story {story_id}: {error_msg}")
                db.add_failed_item(user_id, story_id, 'story', error_msg)
                
    finally:
        L.dirname_pattern = original_dirname_pattern
        
    return count


def download_post(post, folder_path, user_id, fast_update=False):
    """
    Tải post sau khi kiểm tra trong database
    
    Args:
        post: Post object từ instaloader
        folder_path: Đường dẫn lưu file
        user_id: ID của người dùng
        fast_update: Nếu True, sẽ kiểm tra timestamp và bỏ qua post cũ
    
    Returns:
        bool: True nếu đã tải, False nếu bỏ qua
        int: 1 nếu đã tìm thấy post cũ (cho fast_update), 0 nếu không
    """
    post_id = str(post.mediaid)
    post_date = post.date_utc.timestamp()
    
    # Kiểm tra xem post đã tồn tại trong database chưa
    if db.get_post(user_id, post_id):
        print(f"[Info] Post {post_id} đã tồn tại trong database, bỏ qua.")
        return False, 0
    
    # Nếu sử dụng fast_update, kiểm tra số lượng posts hiện có
    # Chỉ áp dụng fast_update nếu đã có posts trong database
    if fast_update:
        downloaded_post_ids = db.get_all_downloaded_post_ids(user_id)
        if len(downloaded_post_ids) == 0:
            print(f"[Info] Không có posts nào trong database, bỏ qua fast_update.")
            fast_update = False
    
    # Chỉ kiểm tra timestamp khi fast_update được bật và có posts trong database
    if fast_update:
        latest_timestamp = db.get_latest_timestamp(user_id, 'posts')
        if latest_timestamp > 0 and post_date <= latest_timestamp:
            # Xác minh lại rằng có thực sự tồn tại post với timestamp này
            has_post_with_timestamp = False
            for existing_post_id in db.get_all_downloaded_post_ids(user_id):
                existing_post = db.get_post(user_id, existing_post_id)
                if existing_post and 'date_utc' in existing_post and existing_post['date_utc'] == latest_timestamp:
                    has_post_with_timestamp = True
                    break
            
            if has_post_with_timestamp:
                print(f"[Info] Post {post_id} cũ hơn timestamp đã lưu ({post_date} <= {latest_timestamp}), bỏ qua.")
                return False, 1
            else:
                print(f"[Info] Không tìm thấy post với timestamp {latest_timestamp} trong database, tiếp tục tải.")
        
    # Tải post
    original_dirname_pattern = L.dirname_pattern
    L.dirname_pattern = str(folder_path)
    
    try:
        # Tải post với retry
        def download_post_item():
            L.download_post(post, target=folder_path)
        
        retry_with_timeout(download_post_item)
        
        # Lưu vào database - CHỈ sau khi đã tải thành công
        post_data = {
            'mediaid': post_id,
            'typename': post.typename,
            'date_utc': post_date,
            'caption': post.caption if post.caption else "",
            'url': post.video_url if post.is_video else post.url,
            'is_video': post.is_video
        }
        db.insert_post(user_id, post_id, post_data)
        
        # Xóa khỏi danh sách failed nếu đã tải thành công
        db.remove_failed_item(user_id, post_id, 'post')
        
        return True, 0
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] Không thể tải post {post_id}: {error_msg}")
        db.add_failed_item(user_id, post_id, 'post', error_msg)
        return False, 0
    finally:
        L.dirname_pattern = original_dirname_pattern


def download_reel(reel, folder_path, user_id, fast_update=False):
    """
    Tải reel sau khi kiểm tra trong database
    
    Args:
        reel: Reel object từ instaloader
        folder_path: Đường dẫn lưu file
        user_id: ID của người dùng
        fast_update: Nếu True, sẽ kiểm tra timestamp và bỏ qua reel cũ
    
    Returns:
        bool: True nếu đã tải, False nếu bỏ qua
        int: 1 nếu đã tìm thấy reel cũ (cho fast_update), 0 nếu không
    """
    reel_id = str(reel.mediaid)
    reel_date = reel.date_utc.timestamp()
    
    # Kiểm tra xem reel đã tồn tại trong database chưa
    if db.get_reel(user_id, reel_id):
        print(f"[Info] Reel {reel_id} đã tồn tại trong database, bỏ qua.")
        return False, 0
    
    # Nếu sử dụng fast_update, kiểm tra số lượng reels hiện có
    # Chỉ áp dụng fast_update nếu đã có reels trong database
    if fast_update:
        downloaded_reel_ids = db.get_all_downloaded_reel_ids(user_id)
        if len(downloaded_reel_ids) == 0:
            print(f"[Info] Không có reels nào trong database, bỏ qua fast_update.")
            fast_update = False
    
    # Chỉ kiểm tra timestamp khi fast_update được bật và có reels trong database
    if fast_update:
        latest_timestamp = db.get_latest_timestamp(user_id, 'reels')
        if latest_timestamp > 0 and reel_date <= latest_timestamp:
            # Xác minh lại rằng có thực sự tồn tại reel với timestamp này
            has_reel_with_timestamp = False
            for existing_reel_id in db.get_all_downloaded_reel_ids(user_id):
                existing_reel = db.get_reel(user_id, existing_reel_id)
                if existing_reel and 'date_utc' in existing_reel and existing_reel['date_utc'] == latest_timestamp:
                    has_reel_with_timestamp = True
                    break
            
            if has_reel_with_timestamp:
                print(f"[Info] Reel {reel_id} cũ hơn timestamp đã lưu ({reel_date} <= {latest_timestamp}), bỏ qua.")
                return False, 1
            else:
                print(f"[Info] Không tìm thấy reel với timestamp {latest_timestamp} trong database, tiếp tục tải.")
        
    # Tải reel
    original_dirname_pattern = L.dirname_pattern
    L.dirname_pattern = str(folder_path)
    
    try:
        # Tải reel với retry
        def download_reel_item():
            L.download_post(reel, target=folder_path)  # Instaloader sử dụng cùng phương thức cho post và reel
        
        retry_with_timeout(download_reel_item)
        
        # Lưu vào database - CHỈ sau khi đã tải thành công
        reel_data = {
            'mediaid': reel_id,
            'typename': reel.typename,
            'date_utc': reel_date,
            'caption': reel.caption if reel.caption else "",
            'url': reel.video_url,
            'is_video': True
        }
        db.insert_reel(user_id, reel_id, reel_data)
        
        # Xóa khỏi danh sách failed nếu đã tải thành công
        db.remove_failed_item(user_id, reel_id, 'reel')
        
        return True, 0
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] Không thể tải reel {reel_id}: {error_msg}")
        db.add_failed_item(user_id, reel_id, 'reel', error_msg)
        return False, 0
    finally:
        L.dirname_pattern = original_dirname_pattern


def download_highlight(highlight, highlight_folder, user_id):
    """
    Tải highlight sau khi kiểm tra trong database
    """
    highlight_id = str(highlight.unique_id)
    
    # Tạo tên thư mục an toàn cho highlight, loại bỏ ký tự đặc biệt
    safe_title = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in highlight.title])
    safe_title = safe_title.strip()
    if not safe_title:
        safe_title = f"highlight_{highlight_id}"  # Dùng ID nếu tên không còn ký tự hợp lệ
    
    # Tạo thư mục cho highlight
    highlight_specific_folder = highlight_folder.joinpath(safe_title)
    try:
        highlight_specific_folder.mkdir(exist_ok=True)
    except Exception as e:
        print(f"[Warning] Không thể tạo thư mục cho highlight '{highlight.title}', sử dụng ID thay thế: {e}")
        # Dùng ID làm tên thư mục nếu gặp lỗi
        highlight_specific_folder = highlight_folder.joinpath(f"highlight_{highlight_id}")
        highlight_specific_folder.mkdir(exist_ok=True)
    
    try:
        # Lấy highlight hiện có từ database
        existing_highlight = db.get_highlight(user_id, highlight_id)
        
        # Tải các item trong highlight
        def get_highlight_items():
            return list(highlight.get_items())
        
        items = retry_with_timeout(get_highlight_items)
        
        # Nếu highlight đã tồn tại trong database, so sánh số lượng item
        if existing_highlight:
            existing_item_count = existing_highlight.get('item_count', 0)
            current_item_count = len(items)
            
            if current_item_count > existing_item_count:
                print(f"[Info] Highlight {highlight.title} ({highlight_id}) có {current_item_count - existing_item_count} item mới.")
            elif current_item_count < existing_item_count:
                print(f"[Info] Highlight {highlight.title} ({highlight_id}) đã giảm số item từ {existing_item_count} xuống {current_item_count}.")
            else:
                print(f"[Info] Highlight {highlight.title} ({highlight_id}) không thay đổi số lượng item ({current_item_count}).")
        else:
            print(f"[Info] Tải mới highlight {highlight.title} ({highlight_id}) với {len(items)} item.")
        
        # Kiểm tra xem có highlight trong database chưa
        # Nếu chưa, không cần kiểm tra timestamp
        downloaded_highlight_ids = set(db.get_all_downloaded_highlight_ids(user_id))
        has_highlights_in_db = len(downloaded_highlight_ids) > 0
        
        # Tải từng story trong highlight (chỉ tải những cái chưa có trong database)
        count = download_story_content(items, highlight_specific_folder, target_username=highlight.owner_username, user_id=user_id)
        
        if count > 0 or not existing_highlight:
            # Chỉ cập nhật database khi đã tải thành công ít nhất một item mới hoặc khi highlight chưa tồn tại
            current_time = int(time.time())  # Timestamp hiện tại
            
            # Cập nhật thông tin highlight vào database
            highlight_data = {
                'unique_id': highlight_id,
                'title': highlight.title,
                'owner_id': user_id,
                'owner_username': highlight.owner_username,
                'item_count': len(items),
                'last_updated': current_time  # Thêm timestamp cập nhật
            }
            db.insert_highlight(user_id, highlight_id, highlight_data)
            
            # Không cập nhật timestamp của loại nội dung highlights nếu đây là highlight đầu tiên
            if has_highlights_in_db:
                db.update_latest_timestamp(user_id, 'highlights', current_time)
            
            # Xóa khỏi danh sách failed nếu đã tải thành công
            db.remove_failed_item(user_id, highlight_id, 'highlight')
        
        return count
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] Không thể tải highlight {highlight_id}: {error_msg}")
        db.add_failed_item(user_id, highlight_id, 'highlight', error_msg)
        return 0


def download_avatar(profile, account_folder):
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


def update_user_info(profile):
    """
    Cập nhật thông tin người dùng vào database
    
    Args:
        profile: Profile object từ instaloader
    """
    user_id = str(profile.userid)
    username = profile.username
    
    try:
        # Thêm hoặc cập nhật thông tin người dùng trong database
        db.insert_user(
            user_id=user_id,
            username=username,
            full_name=profile.full_name if hasattr(profile, 'full_name') else "",
            biography=profile.biography if hasattr(profile, 'biography') else "",
            followers_count=profile.followers if hasattr(profile, 'followers') else 0,
            following_count=profile.followees if hasattr(profile, 'followees') else 0,
            post_count=profile.mediacount if hasattr(profile, 'mediacount') else 0
        )
        
        print(f"[Info] Đã cập nhật thông tin người dùng {username} (ID: {user_id}) vào database")
    except Exception as e:
        print(f"[Error] Không thể cập nhật thông tin người dùng {username}: {e}")


def should_continue_fetching_reels(user_id, reels_batch, downloaded_reel_ids, use_fast_update=True):
    """
    Kiểm tra xem có nên tiếp tục tải danh sách reels tiếp theo hay không
    
    Args:
        user_id (str): ID của người dùng
        reels_batch (list): Danh sách các reel trong batch hiện tại
        downloaded_reel_ids (set): Tập hợp các ID reel đã tải
        use_fast_update (bool): Có sử dụng fast update hay không
        
    Returns:
        bool: True nếu cần tiếp tục tải, False nếu nên dừng lại
    """
    if not reels_batch:
        return False  # Không có reel nào để xử lý
        
    if not use_fast_update:
        # Nếu không dùng fast update, luôn tiếp tục tải để đảm bảo tải tất cả
        # Tuy nhiên, nếu tất cả các reel trong batch đã tồn tại trong database,
        # chúng ta có thể tối ưu bằng cách kiểm tra xem bao nhiêu phần trăm đã tồn tại
        existing_count = sum(1 for reel in reels_batch if str(reel.mediaid) in downloaded_reel_ids)
        if existing_count == len(reels_batch):
            # Nếu toàn bộ batch hiện tại đều đã tồn tại trong database
            # Điều này có thể chỉ ra rằng các batch tiếp theo cũng sẽ chứa nhiều reel đã tải
            # Vì các reel thường được sắp xếp theo thứ tự thời gian
            return False
        
        # Nếu hơn 80% số reel trong batch hiện tại đã tồn tại, có thể cân nhắc dừng lại
        # để tránh quá nhiều request API không cần thiết
        if existing_count / len(reels_batch) > 0.8:
            print(f"[Info] Hơn 80% reels trong batch hiện tại đã tồn tại, xem xét dừng tải.")
            # Nhưng chỉ dừng nếu không có reel mới nào trong 3 reel cuối cùng
            # Điều này đảm bảo chúng ta không bỏ sót reel mới xen kẽ trong dữ liệu cũ
            last_reels = reels_batch[-3:] if len(reels_batch) >= 3 else reels_batch
            if all(str(reel.mediaid) in downloaded_reel_ids for reel in last_reels):
                print(f"[Info] Không tìm thấy reel mới nào trong các reel cuối cùng, dừng tải.")
                return False
        
        return True  # Tiếp tục tải nếu không sử dụng fast_update
    
    # Kiểm tra timestamp mới nhất đã lưu
    latest_timestamp = db.get_latest_timestamp(user_id, 'reels')
    if latest_timestamp == 0:
        return True  # Chưa có timestamp nào được lưu
    
    # Kiểm tra xem tất cả reel trong batch hiện tại đã có trong database chưa
    all_existing = True
    oldest_reel_in_batch = None
    found_old_reel = False
    new_reels_count = 0
    
    for reel in reels_batch:
        reel_id = str(reel.mediaid)
        reel_date = reel.date_utc.timestamp()
        
        # Cập nhật reel cũ nhất trong batch để debug
        if oldest_reel_in_batch is None or reel_date < oldest_reel_in_batch:
            oldest_reel_in_batch = reel_date
        
        # Nếu reel chưa tồn tại, kiểm tra timestamp để xem có phải reel cũ không
        if reel_id not in downloaded_reel_ids:
            all_existing = False
            # Kiểm tra timestamp
            if reel_date <= latest_timestamp:
                found_old_reel = True
            else:
                # Đếm số reel mới hơn timestamp
                new_reels_count += 1
    
    # Log thông tin debug
    if oldest_reel_in_batch:
        print(f"[Debug] Reel cũ nhất trong batch hiện tại: {timestamp_to_date(oldest_reel_in_batch)}")
    print(f"[Debug] Số reels mới trong batch: {new_reels_count}/{len(reels_batch)}")
    
    # Nếu tất cả đều đã tồn tại trong database, không cần tải thêm
    if all_existing:
        print(f"[Info] Tất cả reels trong batch hiện tại đã tồn tại trong database, dừng tải.")
        return False
    
    # Nếu đây là lần đầu tải (rất ít hoặc không có reels trong database),
    # vẫn tiếp tục tải ngay cả khi tìm thấy reels cũ
    if len(downloaded_reel_ids) < 5:
        print(f"[Info] Có ít reels trong database ({len(downloaded_reel_ids)}), tiếp tục tải.")
        return True
    
    # Nếu tìm thấy ít nhất một reel mới hơn timestamp
    if new_reels_count > 0:
        return True
    
    # Nếu tìm thấy reel cũ hơn timestamp và không có reel mới nào
    if found_old_reel and new_reels_count == 0:
        print(f"[Info] Batch hiện tại chỉ chứa reels cũ hơn timestamp {timestamp_to_date(latest_timestamp)}, dừng tải.")
        return False
        
    # Trường hợp còn lại, tiếp tục tải (mặc dù hiếm khi xảy ra)
    return True

def download_user_data(username, use_fast_update=True):
    """
    Tải dữ liệu từ một tài khoản người dùng
    
    Args:
        username: Tên người dùng
        use_fast_update: Sử dụng fast update hay không
    """
    # Random delay trước mỗi lần xử lý account mới
    print(f"[Info] Đợi {account_delay:.2f} giây giữa mỗi account...")
    time.sleep(account_delay)
    
    print(f"\n[Info] Tải dữ liệu từ tài khoản: {username}")
    try:
        # Tải profile
        def get_profile():
            return instaloader.Profile.from_username(L.context, username)
        
        profile = retry_with_timeout(get_profile)
        user_id = str(profile.userid)
        
        # Cập nhật thông tin người dùng
        update_user_info(profile)
        
        print(f"[Info] User: {profile.username}, ID: {user_id}, Followers: {profile.followers}")
        
        # Tạo các thư mục chính trong thư mục downloads
        account_folder = downloads_folder.joinpath(profile.username)
        account_folder.mkdir(exist_ok=True)

        stories_folder = account_folder.joinpath("stories")
        highlights_folder = account_folder.joinpath("highlights")
        posts_folder = account_folder.joinpath("posts")
        reels_folder = account_folder.joinpath("reels")

        stories_folder.mkdir(exist_ok=True)
        highlights_folder.mkdir(exist_ok=True)
        posts_folder.mkdir(exist_ok=True)
        reels_folder.mkdir(exist_ok=True)

        # QUAN TRỌNG: Kiểm tra xem tài khoản đã có dữ liệu trong database chưa
        # Nếu chưa có, tắt fast_update để tải tất cả dữ liệu
        has_posts = len(db.get_all_downloaded_post_ids(user_id)) > 0
        has_reels = len(db.get_all_downloaded_reel_ids(user_id)) > 0
        has_stories = len(db.get_all_downloaded_story_ids(user_id)) > 0
        
        # Nếu tài khoản chưa có dữ liệu, tắt fast_update
        if use_fast_update and not (has_posts or has_reels or has_stories):
            print(f"[Info] Tài khoản {username} chưa có dữ liệu trong database. Chuyển sang chế độ tải đầy đủ.")
            use_fast_update = False

        # Tải avatar nếu được bật trong config
        if download_avatar:
            avatar_downloaded = download_avatar(profile, account_folder)
            time.sleep(micro_delay)

        # Tải stories nếu được bật trong config
        story_count = 0
        if download_stories:
            downloaded_story_ids = set(db.get_all_downloaded_story_ids(user_id))
            print(f"[Info] Đã có {len(downloaded_story_ids)} stories trong database")
            
            def get_stories():
                return L.get_stories(userids=[profile.userid])
            
            for story in retry_with_timeout(get_stories, max_retries=retry_times):
                for item in story.get_items():
                    story_id = str(item.mediaid)
                    if story_id in downloaded_story_ids:
                        print(f"[Info] Story {story_id} đã tồn tại trong database, bỏ qua.")
                        continue
                        
                    try:
                        # Tải story item với retry
                        def download_story_item():
                            L.download_storyitem(item, target=stories_folder)
                        
                        retry_with_timeout(download_story_item)
                        
                        # Lưu vào database
                        story_data = {
                            'mediaid': story_id,
                            'typename': item.typename,
                            'date_utc': item.date_utc.timestamp(),
                            'url': item.video_url if item.is_video else item.url,
                            'is_video': item.is_video
                        }
                        db.insert_story(user_id, story_id, story_data)
                        
                        # Xóa khỏi danh sách failed nếu đã tải thành công
                        db.remove_failed_item(user_id, story_id, 'story')
                        
                        story_count += 1
                        time.sleep(micro_delay)
                    except Exception as e:
                        error_msg = str(e)
                        print(f"[Error] Không thể tải story {story_id}: {error_msg}")
                        db.add_failed_item(user_id, story_id, 'story', error_msg)
                        
            print(f"[Info] Total stories downloaded: {story_count}")
        time.sleep(macro_delay)

        # Tải posts nếu được bật trong config
        post_count = 0
        if download_posts:
            downloaded_post_ids = set(db.get_all_downloaded_post_ids(user_id))
            print(f"[Info] Đã có {len(downloaded_post_ids)} posts trong database")
            
            # Lấy tất cả posts từ profile
            found_old_post = False
            for post in profile.get_posts():
                if found_old_post and use_fast_update:
                    print(f"[Info] Đã tìm thấy post cũ hơn timestamp, dừng tải posts.")
                    break
                    
                post_id = str(post.mediaid)
                if post_id in downloaded_post_ids:
                    print(f"[Info] Post {post_id} đã tồn tại trong database, bỏ qua.")
                    continue
                    
                downloaded, found_old = download_post(post, posts_folder, user_id, fast_update=use_fast_update)
                if downloaded:
                    post_count += 1
                    time.sleep(micro_delay)
                
                found_old_post = found_old_post or (found_old == 1)
                    
            print(f"[Info] Total posts downloaded: {post_count}")
        time.sleep(macro_delay)

        # Tải highlights nếu được bật trong config
        highlight_count = 0
        if download_highlights:
            def get_highlights():
                return L.get_highlights(profile)
            
            for highlight in retry_with_timeout(get_highlights):
                count = download_highlight(highlight, highlights_folder, user_id)
                highlight_count += count
                time.sleep(micro_delay)
                
            print(f"[Info] Total highlight items downloaded: {highlight_count}")
        time.sleep(macro_delay)

        # Tải reels nếu được bật trong config
        reels_count = 0
        if download_reels:
            downloaded_reel_ids = set(db.get_all_downloaded_reel_ids(user_id))
            print(f"[Info] Đã có {len(downloaded_reel_ids)} reels trong database")
            
            # Lấy timestamp mới nhất đã lưu để kiểm tra nhanh
            latest_timestamp = db.get_latest_timestamp(user_id, 'reels')
            if latest_timestamp > 0 and use_fast_update:
                print(f"[Info] Chỉ tải reels mới hơn timestamp {timestamp_to_date(latest_timestamp)}")
            
            # Kiểm tra xem có thông tin pagination đã lưu không
            pagination_info = db.get_pagination_info(user_id, 'reels')
            if pagination_info:
                print(f"[Info] Sử dụng thông tin pagination đã lưu để tiếp tục tải reels")
                
                # TODO: Trong tương lai, khi Instaloader hỗ trợ nhập token phân trang,
                # có thể cập nhật code để sử dụng token đã lưu
                # Hiện tại, pagination_info chỉ lưu thông tin để debug và thống kê
            
            # Dùng đoạn code tương thích với API Instaloader để lấy reels theo batch
            # Mỗi lần gọi get_reels() sẽ tải một trang dữ liệu (khoảng 12 reels)
            try:
                # Dùng profile.get_reels() để lấy iterator
                reels_iterator = profile.get_reels()
                continue_fetching = True
                forbidden_retries = 0
                max_forbidden_retries = 3
                
                # Đếm số lần gửi request API để thống kê và debug
                api_requests_count = 0
                total_reels_found = 0
                
                while continue_fetching:
                    # Lấy batch reels hiện tại
                    current_batch = []
                    current_page_has_error = False
                    
                    try:
                        # Lấy tối đa 12 reels (thường là kích thước trang của API)
                        for _ in range(12):
                            current_batch.append(next(reels_iterator))
                            
                        # Tăng số lượng request API thành công
                        api_requests_count += 1
                        total_reels_found += len(current_batch)
                        
                        # Reset forbidden_retries vì đã lấy batch thành công
                        forbidden_retries = 0
                    except StopIteration:
                        # Hết reels
                        pass
                    except instaloader.exceptions.ConnectionException as e:
                        current_page_has_error = True
                        if "403 Forbidden" in str(e):
                            forbidden_retries += 1
                            if forbidden_retries >= max_forbidden_retries:
                                print("[Error] Đã gặp lỗi 403 Forbidden nhiều lần khi lấy danh sách reels.")
                                print("[Info] Instagram đang giới hạn số lượng request. Đây là vấn đề thường gặp.")
                                print("[Info] Các reels đã tải vẫn được lưu vào database.")
                                print("[Info] Thử lại sau hoặc xem xét điều chỉnh các thông số delay trong config.")
                                
                                # Lưu thông tin phân trang cho lần tải tiếp theo
                                pagination_data = {
                                    'api_requests_sent': api_requests_count,
                                    'total_reels_found': total_reels_found,
                                    'reels_downloaded': reels_count,
                                    'last_timestamp': int(time.time()),
                                    'reason': '403_forbidden'
                                }
                                db.save_pagination_info(user_id, 'reels', pagination_data)
                                
                                break
                            print(f"[Warning] Gặp lỗi 403 Forbidden khi lấy danh sách reels. Thử lại lần {forbidden_retries}/{max_forbidden_retries}...")
                            time.sleep(random.uniform(30, 60))  # Chờ lâu hơn khi gặp lỗi 403
                            continue
                        else:
                            # Các lỗi kết nối khác
                            print(f"[Error] Lỗi kết nối khi lấy danh sách reels: {e}")
                            
                            # Lưu thông tin phân trang cho lần tải tiếp theo
                            pagination_data = {
                                'api_requests_sent': api_requests_count,
                                'total_reels_found': total_reels_found,
                                'reels_downloaded': reels_count,
                                'last_timestamp': int(time.time()),
                                'reason': 'connection_error'
                            }
                            db.save_pagination_info(user_id, 'reels', pagination_data)
                            
                            break
                    
                    if not current_batch and not current_page_has_error:
                        # Nếu không còn reels nào và không phải do lỗi
                        # Xóa thông tin pagination vì đã tải hết
                        db.clear_pagination_info(user_id, 'reels')
                        break
                    
                    # Kiểm tra xem có nên tiếp tục tải batch tiếp theo không
                    continue_fetching = should_continue_fetching_reels(
                        user_id, current_batch, downloaded_reel_ids, use_fast_update
                    )
                    
                    # Xử lý các reels trong batch hiện tại
                    found_old_reel = False
                    for reel in current_batch:
                        reel_id = str(reel.mediaid)
                        if reel_id in downloaded_reel_ids:
                            print(f"[Info] Reel {reel_id} đã tồn tại trong database, bỏ qua.")
                            continue
                            
                        downloaded, found_old = download_reel(reel, reels_folder, user_id, fast_update=use_fast_update)
                        if downloaded:
                            reels_count += 1
                            time.sleep(micro_delay)
                        
                        found_old_reel = found_old_reel or (found_old == 1)
                    
                    if found_old_reel and use_fast_update:
                        print(f"[Info] Đã tìm thấy reel cũ hơn timestamp, dừng tải reels.")
                        
                        # Lưu thông tin phân trang với lý do là tìm thấy reel cũ
                        pagination_data = {
                            'api_requests_sent': api_requests_count,
                            'total_reels_found': total_reels_found,
                            'reels_downloaded': reels_count,
                            'last_timestamp': int(time.time()),
                            'reason': 'found_old_content'
                        }
                        db.save_pagination_info(user_id, 'reels', pagination_data)
                        
                        break
                        
                    # Nếu continue_fetching = False, vòng lặp sẽ dừng sau khi xử lý batch hiện tại
                    if not continue_fetching:
                        print(f"[Info] Dừng tải reels do đã xử lý đủ dữ liệu.")
                        
                        # Lưu thông tin phân trang với lý do là đã xử lý đủ dữ liệu
                        pagination_data = {
                            'api_requests_sent': api_requests_count,
                            'total_reels_found': total_reels_found,
                            'reels_downloaded': reels_count,
                            'last_timestamp': int(time.time()),
                            'reason': 'optimized_stop'
                        }
                        db.save_pagination_info(user_id, 'reels', pagination_data)
                
                # Nếu hoàn thành mà không gặp lỗi, hiển thị thống kê API
                if api_requests_count > 0:
                    print(f"[Info] Đã gửi {api_requests_count} request API để lấy danh sách reels")
                    print(f"[Info] Tìm thấy tổng cộng {total_reels_found} reels, tải mới {reels_count} reels")
                    
                    if total_reels_found > 0 and reels_count == 0:
                        print(f"[Info] Không có reel mới nào cần tải. Các reel đã có trong database hoặc cũ hơn timestamp.")
                    
                    # Lưu thống kê khi hoàn thành tải thành công
                    if not continue_fetching:
                        pagination_data = {
                            'api_requests_sent': api_requests_count,
                            'total_reels_found': total_reels_found,
                            'reels_downloaded': reels_count,
                            'last_timestamp': int(time.time()),
                            'reason': 'completed'
                        }
                        db.save_pagination_info(user_id, 'reels', pagination_data)
            except Exception as e:
                print(f"[Error] Lỗi khi tải danh sách reels: {e}")
            
            print(f"[Info] Total reels downloaded: {reels_count}")
        time.sleep(macro_delay)

        print(f"[Info] Hoàn tất tải dữ liệu từ {username}")
        print(f"[Info] Tổng kết mới: {story_count} stories, {post_count} posts, {highlight_count} highlight items, {reels_count} reels")

    except Exception as e:
        print(f"[Error] Lỗi khi tải từ {username}: {e}")


def download_from_link(link):
    """
    Tải dữ liệu từ một link Instagram
    
    Args:
        link: URL của bài đăng Instagram
    """
    try:
        print(f"[Info] Tải dữ liệu từ link: {link}")
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
        
        if post.is_video and download_reels:
            # Nếu là video (reel)
            reels_folder = account_folder.joinpath("reels")
            reels_folder.mkdir(exist_ok=True)
            
            success, _ = download_reel(post, reels_folder, user_id, fast_update=False)
            if success:
                print(f"[Info] Đã tải reel {shortcode} của {username}")
            else:
                print(f"[Info] Bỏ qua reel {shortcode} (đã tồn tại hoặc lỗi)")
        elif download_posts:
            # Nếu là post thường
            posts_folder = account_folder.joinpath("posts")
            posts_folder.mkdir(exist_ok=True)
            
            success, _ = download_post(post, posts_folder, user_id, fast_update=False)
            if success:
                print(f"[Info] Đã tải post {shortcode} của {username}")
            else:
                print(f"[Info] Bỏ qua post {shortcode} (đã tồn tại hoặc lỗi)")
    
    except Exception as e:
        print(f"[Error] Không thể tải từ link {link}: {e}")


# Thêm hàm chuyển đổi timestamp thành ngày để hiển thị thông tin dễ đọc
def timestamp_to_date(timestamp):
    """
    Chuyển đổi timestamp thành định dạng ngày tháng
    
    Args:
        timestamp (float): Timestamp unix
        
    Returns:
        str: Chuỗi ngày tháng định dạng
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


# Vòng lặp chính
def main():
    # Tải dữ liệu từ links
    for link in links:
        download_from_link(link)
        time.sleep(macro_delay)
    
    # Tải dữ liệu từ check_accounts (không dùng fast update)
    for username in check_accounts:
        download_user_data(username, use_fast_update=False)
    
    # Tải dữ liệu từ accounts thông thường (dùng fast update)
    for username in accounts:
        download_user_data(username, use_fast_update=True)
    
    # Đóng kết nối database khi hoàn tất
    db.close()


if __name__ == "__main__":
    # Gọi hàm thiết lập khi khởi động
    setup_directories()
    main()
