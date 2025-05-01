import sqlite3
import json
import os
from pathlib import Path

class Database:
    def __init__(self, db_path="data.db"):
        """
        Khởi tạo kết nối đến cơ sở dữ liệu SQLite
        
        Args:
            db_path (str): Đường dẫn đến file database
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Kết nối đến cơ sở dữ liệu"""
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
    
    def close(self):
        """Đóng kết nối đến cơ sở dữ liệu"""
        if self.connection:
            self.connection.close()
    
    def create_tables(self):
        """Tạo các bảng cần thiết nếu chưa tồn tại"""
        # Bảng lưu thông tin về người dùng
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                full_name TEXT,
                biography TEXT,
                followers_count INTEGER,
                following_count INTEGER,
                post_count INTEGER,
                last_updated INTEGER
            )
        ''')
        
        # Bảng lưu thông tin về story
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_stories (
                user_id TEXT, 
                story_id TEXT,
                timestamp INTEGER,
                data TEXT,
                PRIMARY KEY (user_id, story_id)
            )
        ''')
        
        # Bảng lưu thông tin về post
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_posts (
                user_id TEXT, 
                post_id TEXT,
                timestamp INTEGER,
                data TEXT,
                PRIMARY KEY (user_id, post_id)
            )
        ''')
        
        # Bảng lưu thông tin về highlight
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_highlights (
                user_id TEXT, 
                highlight_id TEXT,
                timestamp INTEGER,
                data TEXT,
                PRIMARY KEY (user_id, highlight_id)
            )
        ''')
        
        # Bảng lưu thông tin về reel
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_reels (
                user_id TEXT, 
                reel_id TEXT,
                timestamp INTEGER,
                data TEXT,
                PRIMARY KEY (user_id, reel_id)
            )
        ''')
        
        # Bảng lưu thông tin về avatar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_avatars (
                user_id TEXT PRIMARY KEY,
                url TEXT,
                timestamp INTEGER
            )
        ''')
        
        # Bảng lưu timestamp cho mỗi loại content của profile
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS latest_timestamps (
                user_id TEXT,
                content_type TEXT,
                timestamp INTEGER,
                PRIMARY KEY (user_id, content_type)
            )
        ''')
        
        # Bảng lưu các items tải lỗi
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS failed_items (
                user_id TEXT,
                item_id TEXT,
                item_type TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                timestamp INTEGER,
                PRIMARY KEY (user_id, item_id, item_type)
            )
        ''')
        
        # Tạo index cho username để tìm kiếm nhanh
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON instagram_users(username)
        ''')
        
        # Thêm các phương thức để lưu và lấy thông tin pagination
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagination_info (
                user_id TEXT,
                content_type TEXT,
                page_info TEXT,
                last_updated INTEGER,
                PRIMARY KEY (user_id, content_type)
            )
        """)
        
        self.connection.commit()
    
    # Các phương thức làm việc với user
    def insert_user(self, user_id, username, full_name="", biography="", 
                     followers_count=0, following_count=0, post_count=0, timestamp=None):
        """
        Lưu thông tin về người dùng vào database
        
        Args:
            user_id (str): ID của người dùng
            username (str): Tên người dùng
            full_name (str): Tên đầy đủ
            biography (str): Tiểu sử
            followers_count (int): Số lượng người theo dõi
            following_count (int): Số lượng người đang theo dõi
            post_count (int): Số lượng bài đăng
            timestamp (int, optional): Thời gian cập nhật. Mặc định là None.
        """
        if timestamp is None:
            import time
            timestamp = int(time.time())
            
        self.cursor.execute("""
            INSERT OR REPLACE INTO instagram_users (
                user_id, username, full_name, biography, 
                followers_count, following_count, post_count, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, full_name, biography, followers_count, following_count, post_count, timestamp))
        self.connection.commit()
    
    def get_user_by_id(self, user_id):
        """
        Lấy thông tin người dùng theo user_id
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            dict: Thông tin người dùng hoặc None nếu không tìm thấy
        """
        self.cursor.execute("""
            SELECT user_id, username, full_name, biography, 
                  followers_count, following_count, post_count, last_updated
            FROM instagram_users
            WHERE user_id = ?
        """, (user_id,))
        
        result = self.cursor.fetchone()
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'full_name': result[2],
                'biography': result[3],
                'followers_count': result[4],
                'following_count': result[5],
                'post_count': result[6],
                'last_updated': result[7]
            }
        return None
    
    def get_user_by_username(self, username):
        """
        Lấy thông tin người dùng theo username
        
        Args:
            username (str): Tên người dùng
            
        Returns:
            dict: Thông tin người dùng hoặc None nếu không tìm thấy
        """
        self.cursor.execute("""
            SELECT user_id, username, full_name, biography, 
                  followers_count, following_count, post_count, last_updated
            FROM instagram_users
            WHERE username = ?
        """, (username,))
        
        result = self.cursor.fetchone()
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'full_name': result[2],
                'biography': result[3],
                'followers_count': result[4],
                'following_count': result[5],
                'post_count': result[6],
                'last_updated': result[7]
            }
        return None
    
    def get_user_id_by_username(self, username):
        """
        Lấy user_id từ username
        
        Args:
            username (str): Tên người dùng
            
        Returns:
            str: ID của người dùng hoặc None nếu không tìm thấy
        """
        self.cursor.execute("SELECT user_id FROM instagram_users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_username_by_user_id(self, user_id):
        """
        Lấy username từ user_id
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            str: Tên người dùng hoặc None nếu không tìm thấy
        """
        self.cursor.execute("SELECT username FROM instagram_users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def search_users_by_username(self, username_pattern):
        """
        Tìm kiếm người dùng theo mẫu username
        
        Args:
            username_pattern (str): Mẫu tên người dùng (có thể là một phần của username)
            
        Returns:
            list: Danh sách thông tin người dùng thỏa mãn
        """
        self.cursor.execute("""
            SELECT user_id, username, full_name, biography, 
                  followers_count, following_count, post_count, last_updated
            FROM instagram_users
            WHERE username LIKE ?
        """, (f'%{username_pattern}%',))
        
        results = self.cursor.fetchall()
        users = []
        for result in results:
            users.append({
                'user_id': result[0],
                'username': result[1],
                'full_name': result[2],
                'biography': result[3],
                'followers_count': result[4],
                'following_count': result[5],
                'post_count': result[6],
                'last_updated': result[7]
            })
        return users
    
    def get_all_users(self):
        """
        Lấy danh sách tất cả người dùng
        
        Returns:
            list: Danh sách thông tin tất cả người dùng
        """
        self.cursor.execute("""
            SELECT user_id, username, full_name, followers_count, post_count
            FROM instagram_users
            ORDER BY username
        """)
        
        results = self.cursor.fetchall()
        users = []
        for result in results:
            users.append({
                'user_id': result[0],
                'username': result[1],
                'full_name': result[2],
                'followers_count': result[3],
                'post_count': result[4]
            })
        return users
    
    # Các phương thức làm việc với story
    def get_story(self, user_id, story_id):
        """
        Lấy thông tin về một story từ database
        
        Args:
            user_id (str): ID của người dùng
            story_id (str): ID của story
            
        Returns:
            dict: Thông tin về story hoặc None nếu không tìm thấy
        """
        self.cursor.execute(
            "SELECT data FROM instagram_stories WHERE user_id = ? AND story_id = ?", 
            (user_id, story_id)
        )
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    
    def insert_story(self, user_id, story_id, data, timestamp=None):
        """
        Lưu thông tin về một story vào database
        
        Args:
            user_id (str): ID của người dùng
            story_id (str): ID của story
            data (dict): Thông tin về story
            timestamp (int, optional): Thời gian tạo. Mặc định là None.
        """
        if timestamp is None:
            import time
            timestamp = int(time.time())
            
        self.cursor.execute(
            "INSERT OR REPLACE INTO instagram_stories (user_id, story_id, timestamp, data) VALUES (?, ?, ?, ?)",
            (user_id, story_id, timestamp, json.dumps(data))
        )
        self.connection.commit()
        
        # Cập nhật timestamp cho story - chỉ nếu dữ liệu có chứa date_utc
        if 'date_utc' in data:
            # Đảm bảo story thực sự tồn tại trong database trước khi cập nhật timestamp
            self.cursor.execute(
                "SELECT COUNT(*) FROM instagram_stories WHERE user_id = ? AND story_id = ?",
                (user_id, story_id)
            )
            if self.cursor.fetchone()[0] > 0:
                # Chỉ cập nhật timestamp khi story đã được thêm vào database thành công
                story_date = data['date_utc']
                self.update_latest_timestamp(user_id, 'stories', story_date)
    
    # Các phương thức làm việc với post
    def get_post(self, user_id, post_id):
        """
        Lấy thông tin về một post từ database
        
        Args:
            user_id (str): ID của người dùng
            post_id (str): ID của post
            
        Returns:
            dict: Thông tin về post hoặc None nếu không tìm thấy
        """
        self.cursor.execute(
            "SELECT data FROM instagram_posts WHERE user_id = ? AND post_id = ?", 
            (user_id, post_id)
        )
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    
    def insert_post(self, user_id, post_id, data, timestamp=None):
        """
        Lưu thông tin về một post vào database
        
        Args:
            user_id (str): ID của người dùng
            post_id (str): ID của post
            data (dict): Thông tin về post
            timestamp (int, optional): Thời gian tạo. Mặc định là None.
        """
        if timestamp is None:
            import time
            timestamp = int(time.time())
            
        self.cursor.execute(
            "INSERT OR REPLACE INTO instagram_posts (user_id, post_id, timestamp, data) VALUES (?, ?, ?, ?)",
            (user_id, post_id, timestamp, json.dumps(data))
        )
        self.connection.commit()
        
        # Cập nhật timestamp cho post - chỉ nếu dữ liệu có chứa date_utc
        if 'date_utc' in data:
            # Đảm bảo post thực sự tồn tại trong database trước khi cập nhật timestamp
            self.cursor.execute(
                "SELECT COUNT(*) FROM instagram_posts WHERE user_id = ? AND post_id = ?",
                (user_id, post_id)
            )
            if self.cursor.fetchone()[0] > 0:
                # Chỉ cập nhật timestamp khi post đã được thêm vào database thành công
                post_date = data['date_utc']
                self.update_latest_timestamp(user_id, 'posts', post_date)
    
    # Các phương thức làm việc với highlight
    def get_highlight(self, user_id, highlight_id):
        """
        Lấy thông tin về một highlight từ database
        
        Args:
            user_id (str): ID của người dùng
            highlight_id (str): ID của highlight
            
        Returns:
            dict: Thông tin về highlight hoặc None nếu không tìm thấy
        """
        self.cursor.execute(
            "SELECT data FROM instagram_highlights WHERE user_id = ? AND highlight_id = ?", 
            (user_id, highlight_id)
        )
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    
    def insert_highlight(self, user_id, highlight_id, data, timestamp=None):
        """
        Lưu thông tin về một highlight vào database
        
        Args:
            user_id (str): ID của người dùng
            highlight_id (str): ID của highlight
            data (dict): Thông tin về highlight
            timestamp (int, optional): Thời gian tạo. Mặc định là None.
        """
        if timestamp is None:
            import time
            timestamp = int(time.time())
            
        self.cursor.execute(
            "INSERT OR REPLACE INTO instagram_highlights (user_id, highlight_id, timestamp, data) VALUES (?, ?, ?, ?)",
            (user_id, highlight_id, timestamp, json.dumps(data))
        )
        self.connection.commit()
        
        # Highlights không có timestamp của riêng nó, nên dùng thời điểm hiện tại
        self.update_latest_timestamp(user_id, 'highlights', timestamp)
    
    # Các phương thức làm việc với reel
    def get_reel(self, user_id, reel_id):
        """
        Lấy thông tin về một reel từ database
        
        Args:
            user_id (str): ID của người dùng
            reel_id (str): ID của reel
            
        Returns:
            dict: Thông tin về reel hoặc None nếu không tìm thấy
        """
        self.cursor.execute(
            "SELECT data FROM instagram_reels WHERE user_id = ? AND reel_id = ?", 
            (user_id, reel_id)
        )
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    
    def insert_reel(self, user_id, reel_id, data, timestamp=None):
        """
        Lưu thông tin về một reel vào database
        
        Args:
            user_id (str): ID của người dùng
            reel_id (str): ID của reel
            data (dict): Thông tin về reel
            timestamp (int, optional): Thời gian tạo. Mặc định là None.
        """
        if timestamp is None:
            import time
            timestamp = int(time.time())
            
        self.cursor.execute(
            "INSERT OR REPLACE INTO instagram_reels (user_id, reel_id, timestamp, data) VALUES (?, ?, ?, ?)",
            (user_id, reel_id, timestamp, json.dumps(data))
        )
        self.connection.commit()
        
        # Cập nhật timestamp cho reel - chỉ nếu dữ liệu có chứa date_utc
        if 'date_utc' in data:
            # Đảm bảo reel thực sự tồn tại trong database trước khi cập nhật timestamp
            self.cursor.execute(
                "SELECT COUNT(*) FROM instagram_reels WHERE user_id = ? AND reel_id = ?",
                (user_id, reel_id)
            )
            if self.cursor.fetchone()[0] > 0:
                # Chỉ cập nhật timestamp khi reel đã được thêm vào database thành công
                reel_date = data['date_utc']
                self.update_latest_timestamp(user_id, 'reels', reel_date)
    
    # Các phương thức làm việc với avatar
    def get_avatar(self, user_id):
        """
        Lấy thông tin về avatar của người dùng từ database
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            str: URL của avatar hoặc None nếu không tìm thấy
        """
        self.cursor.execute(
            "SELECT url FROM instagram_avatars WHERE user_id = ?", 
            (user_id,)
        )
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None
    
    def insert_avatar(self, user_id, url, timestamp=None):
        """
        Lưu thông tin về avatar của người dùng vào database
        
        Args:
            user_id (str): ID của người dùng
            url (str): URL của avatar
            timestamp (int, optional): Thời gian tạo. Mặc định là None.
        """
        if timestamp is None:
            import time
            timestamp = int(time.time())
            
        self.cursor.execute(
            "INSERT OR REPLACE INTO instagram_avatars (user_id, url, timestamp) VALUES (?, ?, ?)",
            (user_id, url, timestamp)
        )
        self.connection.commit()
        
        # Avatar không có timestamp riêng nên dùng thời điểm hiện tại
        self.update_latest_timestamp(user_id, 'avatar', timestamp)
    
    # Các phương thức bổ sung
    def get_all_downloaded_post_ids(self, user_id):
        """
        Lấy danh sách ID của tất cả các post đã tải
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            list: Danh sách ID của các post đã tải
        """
        self.cursor.execute(
            "SELECT post_id FROM instagram_posts WHERE user_id = ?", 
            (user_id,)
        )
        results = self.cursor.fetchall()
        return [result[0] for result in results]
    
    def get_all_downloaded_story_ids(self, user_id):
        """
        Lấy danh sách ID của tất cả các story đã tải
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            list: Danh sách ID của các story đã tải
        """
        self.cursor.execute(
            "SELECT story_id FROM instagram_stories WHERE user_id = ?", 
            (user_id,)
        )
        results = self.cursor.fetchall()
        return [result[0] for result in results]
    
    def get_all_downloaded_highlight_ids(self, user_id):
        """
        Lấy danh sách ID của tất cả các highlight đã tải
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            list: Danh sách ID của các highlight đã tải
        """
        self.cursor.execute(
            "SELECT highlight_id FROM instagram_highlights WHERE user_id = ?", 
            (user_id,)
        )
        results = self.cursor.fetchall()
        return [result[0] for result in results]
    
    def get_all_downloaded_reel_ids(self, user_id):
        """
        Lấy danh sách ID của tất cả các reel đã tải
        
        Args:
            user_id (str): ID của người dùng
            
        Returns:
            list: Danh sách ID của các reel đã tải
        """
        self.cursor.execute(
            "SELECT reel_id FROM instagram_reels WHERE user_id = ?", 
            (user_id,)
        )
        results = self.cursor.fetchall()
        return [result[0] for result in results]
    
    # Phương thức làm việc với latest timestamps
    def update_latest_timestamp(self, user_id, content_type, timestamp):
        """
        Cập nhật timestamp mới nhất cho một loại nội dung của user
        
        Args:
            user_id (str): ID của người dùng
            content_type (str): Loại nội dung (posts, stories, highlights, reels, avatar)
            timestamp (float): Timestamp unix
        """
        # Lấy timestamp hiện tại
        self.cursor.execute(
            "SELECT timestamp FROM latest_timestamps WHERE user_id = ? AND content_type = ?",
            (user_id, content_type)
        )
        result = self.cursor.fetchone()
        
        # Nếu timestamp mới lớn hơn timestamp hiện tại hoặc chưa có timestamp
        if not result or timestamp > result[0]:
            self.cursor.execute(
                "INSERT OR REPLACE INTO latest_timestamps (user_id, content_type, timestamp) VALUES (?, ?, ?)",
                (user_id, content_type, timestamp)
            )
            self.connection.commit()
    
    def get_latest_timestamp(self, user_id, content_type):
        """
        Lấy timestamp mới nhất cho một loại nội dung của user
        
        Args:
            user_id (str): ID của người dùng
            content_type (str): Loại nội dung (posts, stories, highlights, reels, avatar)
            
        Returns:
            float: Timestamp unix hoặc 0 nếu không có
        """
        self.cursor.execute(
            "SELECT timestamp FROM latest_timestamps WHERE user_id = ? AND content_type = ?",
            (user_id, content_type)
        )
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    # Phương thức làm việc với failed items
    def add_failed_item(self, user_id, item_id, item_type, error_message):
        """
        Thêm một item vào danh sách tải thất bại
        
        Args:
            user_id (str): ID của người dùng
            item_id (str): ID của item
            item_type (str): Loại item (post, story, highlight, reel)
            error_message (str): Thông báo lỗi
        """
        import time
        timestamp = int(time.time())
        
        # Kiểm tra xem item có trong danh sách failed chưa
        self.cursor.execute(
            "SELECT retry_count FROM failed_items WHERE user_id = ? AND item_id = ? AND item_type = ?",
            (user_id, item_id, item_type)
        )
        result = self.cursor.fetchone()
        
        if result:
            retry_count = result[0] + 1
            self.cursor.execute(
                "UPDATE failed_items SET error_message = ?, retry_count = ?, timestamp = ? WHERE user_id = ? AND item_id = ? AND item_type = ?",
                (error_message, retry_count, timestamp, user_id, item_id, item_type)
            )
        else:
            self.cursor.execute(
                "INSERT INTO failed_items (user_id, item_id, item_type, error_message, retry_count, timestamp) VALUES (?, ?, ?, ?, 1, ?)",
                (user_id, item_id, item_type, error_message, timestamp)
            )
        
        self.connection.commit()
    
    def get_failed_items(self, user_id=None):
        """
        Lấy danh sách các item tải thất bại
        
        Args:
            user_id (str, optional): ID của người dùng, mặc định là None để lấy tất cả
            
        Returns:
            list: Danh sách các item tải thất bại
        """
        if user_id:
            self.cursor.execute(
                "SELECT user_id, item_id, item_type, error_message, retry_count, timestamp FROM failed_items WHERE user_id = ?",
                (user_id,)
            )
        else:
            self.cursor.execute(
                "SELECT user_id, item_id, item_type, error_message, retry_count, timestamp FROM failed_items"
            )
            
        results = self.cursor.fetchall()
        failed_items = []
        
        for result in results:
            failed_items.append({
                'user_id': result[0],
                'item_id': result[1],
                'item_type': result[2],
                'error_message': result[3],
                'retry_count': result[4],
                'timestamp': result[5]
            })
            
        return failed_items
    
    def remove_failed_item(self, user_id, item_id, item_type):
        """
        Xóa một item khỏi danh sách tải thất bại
        
        Args:
            user_id (str): ID của người dùng
            item_id (str): ID của item
            item_type (str): Loại item (post, story, highlight, reel)
        """
        self.cursor.execute(
            "DELETE FROM failed_items WHERE user_id = ? AND item_id = ? AND item_type = ?",
            (user_id, item_id, item_type)
        )
        self.connection.commit()

    # Thêm các phương thức để lưu và lấy thông tin pagination
    def save_pagination_info(self, user_id, content_type, page_info):
        """
        Lưu thông tin phân trang cho việc tải tiếp
        
        Args:
            user_id (str): ID của người dùng
            content_type (str): Loại nội dung (reels, posts, etc)
            page_info (dict): Thông tin phân trang
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagination_info (
                user_id TEXT,
                content_type TEXT,
                page_info TEXT,
                last_updated INTEGER,
                PRIMARY KEY (user_id, content_type)
            )
        """)
        
        import time
        timestamp = int(time.time())
        
        self.cursor.execute(
            "INSERT OR REPLACE INTO pagination_info (user_id, content_type, page_info, last_updated) VALUES (?, ?, ?, ?)",
            (user_id, content_type, json.dumps(page_info), timestamp)
        )
        self.connection.commit()
    
    def get_pagination_info(self, user_id, content_type):
        """
        Lấy thông tin phân trang đã lưu
        
        Args:
            user_id (str): ID của người dùng
            content_type (str): Loại nội dung (reels, posts, etc)
            
        Returns:
            dict: Thông tin phân trang hoặc None nếu không tìm thấy
        """
        # Đảm bảo bảng tồn tại
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagination_info (
                user_id TEXT,
                content_type TEXT,
                page_info TEXT,
                last_updated INTEGER,
                PRIMARY KEY (user_id, content_type)
            )
        """)
        
        self.cursor.execute(
            "SELECT page_info, last_updated FROM pagination_info WHERE user_id = ? AND content_type = ?",
            (user_id, content_type)
        )
        
        result = self.cursor.fetchone()
        if result:
            # Kiểm tra xem thông tin phân trang có quá cũ không (hơn 24 giờ)
            import time
            current_time = int(time.time())
            if current_time - result[1] > 86400:  # 24 giờ = 86400 giây
                return None
            
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                return None
        
        return None
    
    def clear_pagination_info(self, user_id=None, content_type=None):
        """
        Xóa thông tin phân trang
        
        Args:
            user_id (str, optional): ID của người dùng, nếu None sẽ xóa tất cả
            content_type (str, optional): Loại nội dung, nếu None sẽ xóa tất cả loại của user_id
        """
        # Đảm bảo bảng tồn tại
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagination_info (
                user_id TEXT,
                content_type TEXT,
                page_info TEXT,
                last_updated INTEGER,
                PRIMARY KEY (user_id, content_type)
            )
        """)
        
        if user_id is None:
            # Xóa tất cả
            self.cursor.execute("DELETE FROM pagination_info")
        elif content_type is None:
            # Xóa tất cả loại của user_id
            self.cursor.execute("DELETE FROM pagination_info WHERE user_id = ?", (user_id,))
        else:
            # Xóa một loại cụ thể của user_id
            self.cursor.execute("DELETE FROM pagination_info WHERE user_id = ? AND content_type = ?", 
                              (user_id, content_type))
        
        self.connection.commit()
