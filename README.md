# Instagram Scraper với Database

Đây là giải pháp scrape Instagram với khả năng lưu trữ cơ sở dữ liệu để tránh tải lại nội dung đã tải trước đó, giúp tiết kiệm request và thời gian.

## Tính năng

- Tải và lưu trữ posts, stories, highlights, reels và avatar của người dùng
- Lưu thông tin vào cơ sở dữ liệu SQLite để tránh tải lại nội dung trùng lặp
- Công cụ quản lý database để xem thống kê, kiểm tra dữ liệu đã lưu
- Hỗ trợ xuất/nhập dữ liệu để sao lưu hoặc chuyển đổi
- Tìm kiếm theo username thay vì user_id
- Quản lý thông tin đăng nhập riêng biệt trong file .env
- **[Mới]** Fast-update mode giúp tăng tốc quá trình cập nhật bằng cách chỉ tải nội dung mới
- **[Mới]** Hệ thống retry giúp tự động thử lại khi gặp lỗi
- **[Mới]** Nhập danh sách tài khoản từ nhiều nguồn khác nhau
- **[Mới]** Cấu hình linh hoạt qua file config.yml
- **[Mới]** Tải trực tiếp từ liên kết Instagram

## Cài đặt

1. Cài đặt các thư viện cần thiết:
```
pip install instaloader requests python-dotenv pyyaml
```

2. Chuẩn bị file danh sách tài khoản:
Tạo file `list_accounts.txt` và `check_accounts.txt` chứa danh sách tên người dùng cần tải, mỗi tên một dòng.

3. Cấu hình thông tin đăng nhập:
Khi chạy lần đầu, script sẽ tạo file `.env` mẫu. Chỉnh sửa file này để thêm thông tin đăng nhập Instagram của bạn:

```
# Instagram credentials
IG_USERNAME=your_username
IG_CSRFTOKEN=your_csrf_token
IG_SESSIONID=your_session_id
IG_DS_USER_ID=your_user_id
IG_MID=your_mid
IG_DID=your_ig_did
```

## Cách sử dụng

### Tải dữ liệu

Chạy script chính để tải dữ liệu:

```
python main.py
```

Script sẽ:
- Đọc cấu hình từ file `config.yml`
- Đọc thông tin đăng nhập từ file `.env`
- Đọc danh sách tài khoản từ các file nguồn được cấu hình
- Kiểm tra trong database những nội dung đã tải
- Chỉ tải những nội dung mới chưa tồn tại trong database
- Lưu dữ liệu mới vào database và thư mục `downloads`

### Tải nội dung từ liên kết

Thêm các liên kết Instagram vào file `links.txt`, mỗi liên kết một dòng, sau đó chạy:

```
python download_links.py
```

Script này sẽ tải các bài đăng, reels hoặc avatar từ các liên kết được cung cấp.

### Cấu hình

Tất cả cấu hình có thể được chỉnh sửa trong file `config.yml`:

```yaml
# Download
download:
  retry_times: 10           # Thử lại nhiều hơn khi lỗi
  timeout: 30               # Timeout lâu hơn nếu mạng delay

# Download options
avatar: true
stories: true
posts: true
reels: true
highlights: true

# Download source:
sources:
  - list_accounts.txt
  - links.txt
  - check_accounts.txt
  - .......
```

#### Các file nguồn đặc biệt

- `list_accounts.txt`: Danh sách tài khoản thông thường, được tải với chế độ fast-update
- `check_accounts.txt`: Danh sách tài khoản được tải đầy đủ (không dùng fast-update)
- `links.txt`: Danh sách các liên kết Instagram cần tải

### Cấu trúc thư mục

Dữ liệu sẽ được lưu theo cấu trúc sau:

```
instascraper/
├── downloads/
│   ├── account_folder1/
│   │   ├── highlights/
│   │   ├── posts/
│   │   ├── reels/
│   │   ├── stories/
│   │   └── account_folder1_avatar.jpg
│   ├── account_folder2/
│   │   ├── highlights/
│   │   ├── posts/
│   │   ├── reels/
│   │   ├── stories/
│   │   └── account_folder2_avatar.jpg
├── instagram_data.db
├── .env
├── config.yml
└── list_accounts.txt
└── check_accounts.txt
└── links.txt
```

### Thiết lập session

Để tránh bị giới hạn tần suất truy cập và truy cập được nội dung riêng tư, bạn cần cấu hình thông tin đăng nhập trong file `.env`.

Cách lấy thông tin đăng nhập:
1. Đăng nhập vào Instagram trên trình duyệt
2. Mở DevTools (F12), vào tab Application (Chrome) hoặc Storage (Firefox)
3. Tìm phần Cookies và trang instagram.com
4. Sao chép các giá trị cookie: csrftoken, sessionid, ds_user_id, mid và ig_did
5. Cập nhật vào file .env

### Quản lý database

Sử dụng công cụ `db_manager.py` để quản lý dữ liệu đã lưu:

```
python db_manager.py [lệnh]
```

Các lệnh có sẵn:

1. Xem thống kê tổng quan:
```
python db_manager.py stats
```

2. Liệt kê tất cả người dùng trong database:
```
python db_manager.py list-users
```

3. Tìm kiếm người dùng theo username:
```
python db_manager.py find-username [USERNAME]
```

4. Xem chi tiết về một người dùng (bằng user_id hoặc username):
```
python db_manager.py user-detail [USER_ID]
python db_manager.py user-detail-by-username [USERNAME]
```

5. Xóa dữ liệu cũ:
```
python db_manager.py cleanup --days 30
```

6. Xuất dữ liệu ra file JSON:
```
python db_manager.py export --output data_backup.json
```

7. Nhập dữ liệu từ file JSON:
```
python db_manager.py import data_backup.json
```

## Cách hoạt động của Fast-Update

Tính năng Fast-Update giúp tăng tốc quá trình tải dữ liệu bằng cách:

1. Lưu trữ timestamp của nội dung mới nhất đã tải cho mỗi loại (post, story, reel)
2. Khi tải dữ liệu mới, nếu timestamp của nội dung cũ hơn timestamp đã lưu, sẽ bỏ qua
3. Khi gặp nội dung cũ hơn timestamp, quá trình tải sẽ dừng lại

Điều này giúp giảm đáng kể số lượng request và thời gian tải, đặc biệt với các tài khoản có nhiều nội dung.

## Cơ chế Retry

Khi gặp lỗi trong quá trình tải, hệ thống sẽ:

1. Thử lại với số lần được cấu hình trong `config.yml` (mặc định: 10 lần)
2. Chờ khoảng thời gian timeout giữa các lần thử (mặc định: 30 giây)
3. Lưu thông tin lỗi vào database để kiểm tra sau
4. Chỉ bỏ qua khi đã thử hết số lần quy định

## Xử lý lỗi 403 Forbidden

Nếu bạn thường xuyên gặp lỗi 403 Forbidden, hãy thử các giải pháp sau:

1. Tăng khoảng thời gian chờ giữa các request (điều chỉnh biến `micro_delay`, `macro_delay`, `account_delay`)
2. Tăng số lần retry và timeout trong file `config.yml`
3. Đảm bảo thông tin đăng nhập trong `.env` là hợp lệ và mới
4. Chạy script vào thời điểm ít người truy cập
5. Hạn chế số lượng tài khoản xử lý trong một lần chạy
6. Sử dụng VPN hoặc proxy để thay đổi IP

### Tính năng mới: Tối ưu hóa requests API (v1.2.0)

Phiên bản mới đã cải thiện cách xử lý lỗi 403 Forbidden khi tải reels:

- **Smart Batch Processing**: Giảm số lượng requests API bằng cách kiểm tra toàn bộ batch reels thay vì từng reel một
- **Caching và Pagination**: Lưu thông tin phân trang để tiếp tục tải từ vị trí dừng khi gặp lỗi 403
- **Thông báo thông minh**: Hiển thị thông báo hữu ích và rõ ràng khi gặp lỗi 403 
- **Thống kê API**: Hiển thị số lượng requests API đã gửi và hiệu quả của việc tải (reels đã tìm thấy so với reels mới tải)
- **Early-Stop**: Dừng tải sớm khi phát hiện nhiều reel đã tồn tại hoặc cũ hơn timestamp

Khi gặp lỗi 403 Forbidden, script sẽ:
1. Thử lại tối đa 3 lần với khoảng thời gian chờ dài hơn (30-60 giây)
2. Lưu thông tin phân trang để lần tải tiếp theo không cần bắt đầu từ đầu
3. Lưu các reels đã tải thành công vào database
4. Hiển thị thông báo chi tiết về vấn đề và cách giải quyết

Các thông tin phân trang sẽ được lưu vào database và tự động sử dụng trong lần tải tiếp theo.

## Cấu trúc dữ liệu

Dữ liệu được lưu trữ trong thư mục tương ứng với tên người dùng:
- `/{username}/posts/` - Chứa các bài đăng
- `/{username}/stories/` - Chứa các story
- `/{username}/highlights/` - Chứa các highlight
- `/{username}/reels/` - Chứa các reel
- `/{username}_avatar.jpg` - Avatar của người dùng
