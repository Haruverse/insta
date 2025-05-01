# Đây là script để lấy danh sách người bạn đang follow

import instaloader
import dotenv
from pathlib import Path
import os


# Tạo đối tượng Instaloader
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

username = L.context.username

# Đăng nhập vào Instagram (nếu cần)
# username = "your_username"  # Thay thế bằng tên tài khoản của bạn
# password = "your_password"  # Thay thế bằng mật khẩu của bạn
# L.login(username, password)

# Lấy profile của bạn
profile = instaloader.Profile.from_username(L.context, username)

# In ra thông tin về tài khoản
print(f"User: {profile.username}, Followers: {profile.followers}, Following: {profile.followees}")

# Lấy danh sách những tài khoản mà bạn đang follow
followees = profile.get_followees()  # Đây là các tài khoản mà bạn đang follow

# Lưu danh sách vào file
with open("followees_list.txt", "w") as f:
    for followee in followees:
        f.write(f"{followee.username}\n")  # Ghi tên tài khoản của những người bạn đang follow vào file

print(f"Đã lưu danh sách người bạn đang follow vào 'followees_list.txt'.")
