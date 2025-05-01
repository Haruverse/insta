# Đây là script để quản lý cơ sở dữ liệu database

import os
import json
import argparse
import time
from datetime import datetime
from database import Database
from pathlib import Path

def print_table(headers, data):
    """
    In bảng dữ liệu đẹp hơn
    """
    # Tính toán độ rộng cột
    col_widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # In header
    header_str = ' | '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_str)
    print('-' * len(header_str))
    
    # In dữ liệu
    for row in data:
        print(' | '.join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))

def timestamp_to_date(timestamp):
    """
    Chuyển đổi timestamp thành định dạng ngày tháng
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def view_stats(db):
    """
    Hiển thị thống kê tổng quan về database
    """
    # Đếm tổng số lượng mỗi loại
    db.cursor.execute("SELECT COUNT(*) FROM instagram_posts")
    total_posts = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(*) FROM instagram_stories")
    total_stories = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(*) FROM instagram_highlights")
    total_highlights = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(*) FROM instagram_reels")
    total_reels = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(*) FROM instagram_avatars")
    total_avatars = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(DISTINCT user_id) FROM instagram_posts")
    total_users_with_posts = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(DISTINCT user_id) FROM instagram_stories")
    total_users_with_stories = db.cursor.fetchone()[0]
    
    # Tính tổng số người dùng duy nhất
    db.cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM (
            SELECT user_id FROM instagram_posts
            UNION
            SELECT user_id FROM instagram_stories
            UNION
            SELECT user_id FROM instagram_highlights
            UNION
            SELECT user_id FROM instagram_reels
            UNION
            SELECT user_id FROM instagram_avatars
        )
    """)
    total_unique_users = db.cursor.fetchone()[0]
    
    print("===== THỐNG KÊ DATABASE =====")
    print(f"Tổng số người dùng: {total_unique_users}")
    print(f"Tổng số bài viết: {total_posts}")
    print(f"Tổng số stories: {total_stories}")
    print(f"Tổng số highlights: {total_highlights}")
    print(f"Tổng số reels: {total_reels}")
    print(f"Tổng số avatars: {total_avatars}")
    print("=============================")

def show_user_details(db, user_id):
    """
    Hiển thị thông tin chi tiết về một người dùng
    
    Args:
        db: Database instance
        user_id: ID của người dùng
    """
    # Kiểm tra xem user có tồn tại không
    db.cursor.execute("""
        SELECT 1 FROM (
            SELECT user_id FROM instagram_posts WHERE user_id = ?
            UNION
            SELECT user_id FROM instagram_stories WHERE user_id = ?
            UNION
            SELECT user_id FROM instagram_highlights WHERE user_id = ?
            UNION 
            SELECT user_id FROM instagram_reels WHERE user_id = ?
            UNION
            SELECT user_id FROM instagram_avatars WHERE user_id = ?
        ) LIMIT 1
    """, (user_id, user_id, user_id, user_id, user_id))
    
    if not db.cursor.fetchone():
        print(f"Không tìm thấy người dùng với ID: {user_id}")
        return
    
    # Lấy username nếu có trong bảng instagram_users
    username = None
    db.cursor.execute("SELECT username FROM instagram_users WHERE user_id = ?", (user_id,))
    result = db.cursor.fetchone()
    if result:
        username = result[0]
        print(f"===== THÔNG TIN CHI TIẾT NGƯỜI DÙNG: {username} (ID: {user_id}) =====")
    else:
        print(f"===== THÔNG TIN CHI TIẾT NGƯỜI DÙNG: ID {user_id} =====")
    
    # Kiểm tra avatar
    db.cursor.execute("SELECT url, timestamp FROM instagram_avatars WHERE user_id = ?", (user_id,))
    avatar_data = db.cursor.fetchone()
    if avatar_data:
        print(f"Avatar URL: {avatar_data[0]}")
        print(f"Cập nhật lần cuối: {timestamp_to_date(avatar_data[1])}")
    else:
        print("Avatar: Không có")
    
    # Thống kê posts
    db.cursor.execute("SELECT COUNT(*) FROM instagram_posts WHERE user_id = ?", (user_id,))
    post_count = db.cursor.fetchone()[0]
    print(f"\nTổng số posts: {post_count}")
    
    if post_count > 0:
        db.cursor.execute("""
            SELECT post_id, timestamp FROM instagram_posts 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (user_id,))
        recent_posts = db.cursor.fetchall()
        print("5 posts gần đây nhất:")
        for post in recent_posts:
            print(f"  - ID: {post[0]}, Thời gian: {timestamp_to_date(post[1])}")
    
    # Thống kê stories
    db.cursor.execute("SELECT COUNT(*) FROM instagram_stories WHERE user_id = ?", (user_id,))
    story_count = db.cursor.fetchone()[0]
    print(f"\nTổng số stories: {story_count}")
    
    if story_count > 0:
        db.cursor.execute("""
            SELECT story_id, timestamp FROM instagram_stories 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (user_id,))
        recent_stories = db.cursor.fetchall()
        print("5 stories gần đây nhất:")
        for story in recent_stories:
            print(f"  - ID: {story[0]}, Thời gian: {timestamp_to_date(story[1])}")
    
    # Thống kê highlights
    db.cursor.execute("SELECT COUNT(*) FROM instagram_highlights WHERE user_id = ?", (user_id,))
    highlight_count = db.cursor.fetchone()[0]
    print(f"\nTổng số highlights: {highlight_count}")
    
    if highlight_count > 0:
        db.cursor.execute("""
            SELECT highlight_id, data FROM instagram_highlights 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        """, (user_id,))
        highlights = db.cursor.fetchall()
        print("Danh sách highlights:")
        for highlight in highlights:
            highlight_data = json.loads(highlight[1])
            print(f"  - ID: {highlight[0]}, Tên: {highlight_data.get('title', 'N/A')}")
    
    # Thống kê reels
    db.cursor.execute("SELECT COUNT(*) FROM instagram_reels WHERE user_id = ?", (user_id,))
    reel_count = db.cursor.fetchone()[0]
    print(f"\nTổng số reels: {reel_count}")
    
    if reel_count > 0:
        db.cursor.execute("""
            SELECT reel_id, timestamp FROM instagram_reels 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (user_id,))
        recent_reels = db.cursor.fetchall()
        print("5 reels gần đây nhất:")
        for reel in recent_reels:
            print(f"  - ID: {reel[0]}, Thời gian: {timestamp_to_date(reel[1])}")
    
    print("=" * 50)

def show_user_details_by_username(db, username):
    """
    Hiển thị thông tin chi tiết về một người dùng dựa trên username
    
    Args:
        db: Database instance
        username: Tên người dùng
    """
    # Kiểm tra xem username có trong bảng instagram_users không
    db.cursor.execute("SELECT user_id FROM instagram_users WHERE username = ?", (username,))
    result = db.cursor.fetchone()
    
    if result:
        user_id = result[0]
        show_user_details(db, user_id)
    else:
        print(f"Không tìm thấy người dùng với username: {username}")
        
        # Hỗ trợ tìm kiếm mờ nếu không tìm thấy kết quả chính xác
        db.cursor.execute("SELECT user_id, username FROM instagram_users WHERE username LIKE ?", (f'%{username}%',))
        similar_results = db.cursor.fetchall()
        
        if similar_results:
            print("\nCó thể bạn đang tìm một trong những người dùng sau:")
            for user in similar_results:
                print(f"- {user[1]} (ID: {user[0]})")

def find_username(db, pattern):
    """
    Tìm kiếm người dùng theo mẫu username
    
    Args:
        db: Database instance
        pattern: Mẫu tên người dùng
    """
    db.cursor.execute("SELECT user_id, username FROM instagram_users WHERE username LIKE ?", (f'%{pattern}%',))
    results = db.cursor.fetchall()
    
    if not results:
        print(f"Không tìm thấy người dùng nào khớp với mẫu: {pattern}")
        return
    
    print(f"Tìm thấy {len(results)} người dùng khớp với mẫu '{pattern}':")
    
    # Thu thập thông tin chi tiết cho mỗi user_id
    users_info = []
    for user_id, username in results:
        # Đếm số lượng posts
        db.cursor.execute("SELECT COUNT(*) FROM instagram_posts WHERE user_id = ?", (user_id,))
        post_count = db.cursor.fetchone()[0]
        
        # Đếm số lượng stories
        db.cursor.execute("SELECT COUNT(*) FROM instagram_stories WHERE user_id = ?", (user_id,))
        story_count = db.cursor.fetchone()[0]
        
        # Đếm số lượng highlights
        db.cursor.execute("SELECT COUNT(*) FROM instagram_highlights WHERE user_id = ?", (user_id,))
        highlight_count = db.cursor.fetchone()[0]
        
        # Đếm số lượng reels
        db.cursor.execute("SELECT COUNT(*) FROM instagram_reels WHERE user_id = ?", (user_id,))
        reel_count = db.cursor.fetchone()[0]
        
        # Kiểm tra xem có avatar không
        db.cursor.execute("SELECT COUNT(*) FROM instagram_avatars WHERE user_id = ?", (user_id,))
        has_avatar = db.cursor.fetchone()[0] > 0
        
        users_info.append([
            username,
            user_id,
            post_count,
            story_count,
            highlight_count,
            reel_count,
            "Có" if has_avatar else "Không"
        ])
    
    # In bảng thông tin
    headers = ["Username", "User ID", "Posts", "Stories", "Highlights", "Reels", "Avatar"]
    print_table(headers, users_info)

def cleanup_database(db, days_old=30):
    """
    Xóa các bản ghi cũ hơn một số ngày
    
    Args:
        db: Database instance
        days_old: Số ngày, mặc định là 30
    """
    current_time = int(time.time())
    threshold = current_time - (days_old * 24 * 60 * 60)
    
    tables = [
        "instagram_posts",
        "instagram_stories",
        "instagram_highlights",
        "instagram_reels",
        "instagram_avatars"
    ]
    
    deleted_count = 0
    
    for table in tables:
        db.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE timestamp < ?", (threshold,))
        count = db.cursor.fetchone()[0]
        
        if count > 0:
            db.cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (threshold,))
            deleted_count += count
            print(f"Đã xóa {count} bản ghi từ bảng {table}")
    
    db.connection.commit()
    print(f"Tổng cộng đã xóa {deleted_count} bản ghi cũ hơn {days_old} ngày")

def export_database(db, output_file="instagram_export.json"):
    """
    Xuất tất cả dữ liệu từ database ra file JSON
    
    Args:
        db: Database instance
        output_file: Tên file xuất, mặc định là "instagram_export.json"
    """
    data = {
        "users": [],
        "posts": [],
        "stories": [],
        "highlights": [],
        "reels": [],
        "avatars": []
    }
    
    # Xuất thông tin người dùng
    db.cursor.execute("SELECT user_id, username, full_name, biography, followers_count, following_count, post_count, last_updated FROM instagram_users")
    for row in db.cursor.fetchall():
        user_id, username, full_name, biography, followers_count, following_count, post_count, last_updated = row
        data["users"].append({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "biography": biography,
            "followers_count": followers_count,
            "following_count": following_count,
            "post_count": post_count,
            "last_updated": last_updated,
            "date": timestamp_to_date(last_updated) if last_updated else None
        })
    
    # Xuất posts
    db.cursor.execute("SELECT user_id, post_id, timestamp, data FROM instagram_posts")
    for row in db.cursor.fetchall():
        user_id, post_id, timestamp, post_data = row
        data["posts"].append({
            "user_id": user_id,
            "post_id": post_id,
            "timestamp": timestamp,
            "date": timestamp_to_date(timestamp),
            "data": json.loads(post_data)
        })
    
    # Xuất stories
    db.cursor.execute("SELECT user_id, story_id, timestamp, data FROM instagram_stories")
    for row in db.cursor.fetchall():
        user_id, story_id, timestamp, story_data = row
        data["stories"].append({
            "user_id": user_id,
            "story_id": story_id,
            "timestamp": timestamp,
            "date": timestamp_to_date(timestamp),
            "data": json.loads(story_data)
        })
    
    # Xuất highlights
    db.cursor.execute("SELECT user_id, highlight_id, timestamp, data FROM instagram_highlights")
    for row in db.cursor.fetchall():
        user_id, highlight_id, timestamp, highlight_data = row
        data["highlights"].append({
            "user_id": user_id,
            "highlight_id": highlight_id,
            "timestamp": timestamp,
            "date": timestamp_to_date(timestamp),
            "data": json.loads(highlight_data)
        })
    
    # Xuất reels
    db.cursor.execute("SELECT user_id, reel_id, timestamp, data FROM instagram_reels")
    for row in db.cursor.fetchall():
        user_id, reel_id, timestamp, reel_data = row
        data["reels"].append({
            "user_id": user_id,
            "reel_id": reel_id,
            "timestamp": timestamp,
            "date": timestamp_to_date(timestamp),
            "data": json.loads(reel_data)
        })
    
    # Xuất avatars
    db.cursor.execute("SELECT user_id, url, timestamp FROM instagram_avatars")
    for row in db.cursor.fetchall():
        user_id, url, timestamp = row
        data["avatars"].append({
            "user_id": user_id,
            "url": url,
            "timestamp": timestamp,
            "date": timestamp_to_date(timestamp)
        })
    
    # Ghi ra file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Đã xuất dữ liệu thành công ra file: {output_file}")
    print(f"- {len(data['users'])} users")
    print(f"- {len(data['posts'])} posts")
    print(f"- {len(data['stories'])} stories")
    print(f"- {len(data['highlights'])} highlights")
    print(f"- {len(data['reels'])} reels")
    print(f"- {len(data['avatars'])} avatars")

def import_database(db, input_file):
    """
    Nhập dữ liệu từ file JSON vào database
    
    Args:
        db: Database instance
        input_file: Đường dẫn đến file JSON
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Đếm số bản ghi đã nhập
        import_counts = {
            "users": 0,
            "posts": 0,
            "stories": 0,
            "highlights": 0,
            "reels": 0,
            "avatars": 0
        }
        
        # Nhập users
        for user in data.get("users", []):
            db.insert_user(
                user["user_id"],
                user["username"],
                user.get("full_name", ""),
                user.get("biography", ""),
                user.get("followers_count", 0),
                user.get("following_count", 0),
                user.get("post_count", 0),
                user.get("last_updated")
            )
            import_counts["users"] += 1
        
        # Nhập posts
        for post in data.get("posts", []):
            db.insert_post(
                post["user_id"], 
                post["post_id"], 
                post["data"], 
                post["timestamp"]
            )
            import_counts["posts"] += 1
        
        # Nhập stories
        for story in data.get("stories", []):
            db.insert_story(
                story["user_id"], 
                story["story_id"], 
                story["data"], 
                story["timestamp"]
            )
            import_counts["stories"] += 1
        
        # Nhập highlights
        for highlight in data.get("highlights", []):
            db.insert_highlight(
                highlight["user_id"], 
                highlight["highlight_id"], 
                highlight["data"], 
                highlight["timestamp"]
            )
            import_counts["highlights"] += 1
        
        # Nhập reels
        for reel in data.get("reels", []):
            db.insert_reel(
                reel["user_id"], 
                reel["reel_id"], 
                reel["data"], 
                reel["timestamp"]
            )
            import_counts["reels"] += 1
        
        # Nhập avatars
        for avatar in data.get("avatars", []):
            db.insert_avatar(
                avatar["user_id"], 
                avatar["url"], 
                avatar["timestamp"]
            )
            import_counts["avatars"] += 1
        
        print(f"Đã nhập dữ liệu thành công từ file: {input_file}")
        print(f"- {import_counts['users']} users")
        print(f"- {import_counts['posts']} posts")
        print(f"- {import_counts['stories']} stories")
        print(f"- {import_counts['highlights']} highlights")
        print(f"- {import_counts['reels']} reels")
        print(f"- {import_counts['avatars']} avatars")
        
    except Exception as e:
        print(f"Lỗi khi nhập dữ liệu: {e}")

def list_users(db):
    """
    Liệt kê tất cả người dùng trong database
    """
    # Lấy danh sách user_id từ bảng posts
    db.cursor.execute("SELECT DISTINCT user_id FROM instagram_posts")
    user_ids_from_posts = db.cursor.fetchall()
    
    # Lấy danh sách user_id từ bảng stories
    db.cursor.execute("SELECT DISTINCT user_id FROM instagram_stories")
    user_ids_from_stories = db.cursor.fetchall()
    
    # Lấy danh sách user_id từ bảng highlights
    db.cursor.execute("SELECT DISTINCT user_id FROM instagram_highlights")
    user_ids_from_highlights = db.cursor.fetchall()
    
    # Lấy danh sách user_id từ bảng reels
    db.cursor.execute("SELECT DISTINCT user_id FROM instagram_reels")
    user_ids_from_reels = db.cursor.fetchall()
    
    # Lấy danh sách user_id từ bảng avatars
    db.cursor.execute("SELECT DISTINCT user_id FROM instagram_avatars")
    user_ids_from_avatars = db.cursor.fetchall()
    
    # Kết hợp danh sách
    user_ids = set([
        user_id[0] for user_id in 
        user_ids_from_posts + 
        user_ids_from_stories + 
        user_ids_from_highlights + 
        user_ids_from_reels +
        user_ids_from_avatars
    ])
    
    if not user_ids:
        print("Không có người dùng nào trong database.")
        return
    
    # Thu thập thông tin chi tiết cho mỗi user_id
    users_info = []
    for user_id in user_ids:
        # Tìm username nếu có
        db.cursor.execute("SELECT username FROM instagram_users WHERE user_id = ?", (user_id,))
        result = db.cursor.fetchone()
        username = result[0] if result else "N/A"
        
        # Đếm số lượng posts
        db.cursor.execute("SELECT COUNT(*) FROM instagram_posts WHERE user_id = ?", (user_id,))
        post_count = db.cursor.fetchone()[0]
        
        # Đếm số lượng stories
        db.cursor.execute("SELECT COUNT(*) FROM instagram_stories WHERE user_id = ?", (user_id,))
        story_count = db.cursor.fetchone()[0]
        
        # Đếm số lượng highlights
        db.cursor.execute("SELECT COUNT(*) FROM instagram_highlights WHERE user_id = ?", (user_id,))
        highlight_count = db.cursor.fetchone()[0]
        
        # Đếm số lượng reels
        db.cursor.execute("SELECT COUNT(*) FROM instagram_reels WHERE user_id = ?", (user_id,))
        reel_count = db.cursor.fetchone()[0]
        
        # Kiểm tra xem có avatar không
        db.cursor.execute("SELECT COUNT(*) FROM instagram_avatars WHERE user_id = ?", (user_id,))
        has_avatar = db.cursor.fetchone()[0] > 0
        
        users_info.append([
            username,
            user_id,
            post_count,
            story_count,
            highlight_count,
            reel_count,
            "Có" if has_avatar else "Không"
        ])
    
    # In bảng thông tin
    headers = ["Username", "User ID", "Posts", "Stories", "Highlights", "Reels", "Avatar"]
    print_table(headers, users_info)

def main():
    """
    Hàm chính xử lý các tham số dòng lệnh
    """
    parser = argparse.ArgumentParser(description="Công cụ quản lý cơ sở dữ liệu Instagram Scraper")
    parser.add_argument("--db", default="instagram_data.db", help="Đường dẫn đến file database SQLite (mặc định: instagram_data.db)")
    
    subparsers = parser.add_subparsers(dest="command", help="Lệnh cần thực hiện")
    
    # Lệnh stats - Hiển thị thống kê
    parser_stats = subparsers.add_parser("stats", help="Hiển thị thống kê tổng quan về database")
    
    # Lệnh list-users - Liệt kê người dùng
    parser_list = subparsers.add_parser("list-users", help="Liệt kê tất cả người dùng trong database")
    
    # Lệnh find-username - Tìm kiếm người dùng theo username
    parser_find = subparsers.add_parser("find-username", help="Tìm kiếm người dùng theo mẫu username")
    parser_find.add_argument("pattern", help="Mẫu username cần tìm kiếm")
    
    # Lệnh user-detail - Xem chi tiết một người dùng
    parser_detail = subparsers.add_parser("user-detail", help="Xem chi tiết về một người dùng")
    parser_detail.add_argument("user_id", help="ID của người dùng cần xem chi tiết")
    
    # Lệnh user-detail-by-username - Xem chi tiết một người dùng bằng username
    parser_detail_username = subparsers.add_parser("user-detail-by-username", help="Xem chi tiết về một người dùng dựa trên username")
    parser_detail_username.add_argument("username", help="Username của người dùng cần xem chi tiết")
    
    # Lệnh cleanup - Xóa dữ liệu cũ
    parser_cleanup = subparsers.add_parser("cleanup", help="Xóa dữ liệu cũ hơn một số ngày")
    parser_cleanup.add_argument("--days", type=int, default=30, help="Xóa dữ liệu cũ hơn số ngày này (mặc định: 30)")
    
    # Lệnh export - Xuất dữ liệu
    parser_export = subparsers.add_parser("export", help="Xuất dữ liệu ra file JSON")
    parser_export.add_argument("--output", default="instagram_export.json", help="Đường dẫn đến file xuất (mặc định: instagram_export.json)")
    
    # Lệnh import - Nhập dữ liệu
    parser_import = subparsers.add_parser("import", help="Nhập dữ liệu từ file JSON")
    parser_import.add_argument("input", help="Đường dẫn đến file JSON cần nhập")
    
    args = parser.parse_args()
    
    # Khởi tạo database
    db = Database(args.db)
    
    try:
        if args.command == "stats":
            view_stats(db)
        elif args.command == "list-users":
            list_users(db)
        elif args.command == "find-username":
            find_username(db, args.pattern)
        elif args.command == "user-detail":
            show_user_details(db, args.user_id)
        elif args.command == "user-detail-by-username":
            show_user_details_by_username(db, args.username)
        elif args.command == "cleanup":
            cleanup_database(db, args.days)
        elif args.command == "export":
            export_database(db, args.output)
        elif args.command == "import":
            import_database(db, args.input)
        elif args.command is None:
            parser.print_help()
    finally:
        db.close()

if __name__ == "__main__":
    main()
