# Persional Bot - Discord & Google Calendar Integration

Bot Discord cá nhân hỗ trợ quản lý lịch Google Calendar, kiểm tra thông tin Steam và giám sát hệ thống.

## 🚀 Tính năng chính
- **Google Calendar:** Xem, thêm sự kiện trực tiếp từ Discord.
- **Steam:** Xem thông tin hồ sơ người chơi Steam.
- **Hệ thống:** Giám sát thông số CPU, RAM của máy chủ chạy bot.
- **Tiện ích:** Tải file qua torrent/magnet link (sử dụng aria2c).

## 🛠 Cài đặt

1. **Yêu cầu:**
   - Python 3.8+
   - [aria2c](https://aria2.github.io/) (nếu dùng tính năng tải torrent)

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình:**
   - Tạo file `.env` và điền các mã token:
     ```env
     DISCORD_TOKEN=your_discord_bot_token
     STEAM_API=your_steam_api_key
     ```
   - **Google Calendar API:**
     - Truy cập [Google Cloud Console](https://console.cloud.google.com/).
     - Bật Google Calendar API.
     - Tạo OAuth 2.0 Client ID và tải file JSON về.
     - Đổi tên file vừa tải thành `credentials.json` và để ở thư mục gốc của bot.

## 📅 Hướng dẫn dùng Google Calendar

Vì bot đang ở chế độ thử nghiệm (Testing), bạn cần thêm email của mình vào danh sách người dùng thử:
1. Vào Google Cloud Console -> APIs & Services -> OAuth consent screen.
2. Tại phần **Test users**, nhấn **ADD USERS** và nhập email của bạn.

### Các lệnh Google Calendar:
- `/events [limit]`: Xem danh sách các sự kiện sắp tới (mặc định là 5).
- `/addevent`: Thêm sự kiện với đầy đủ thông tin ngày và giờ.
  - Định dạng thời gian: `YYYY-MM-DDTHH:MM:SS` (Ví dụ: `2026-03-10T14:30:00`).
- `/addtodayevent`: Thêm nhanh sự kiện vào **ngày hôm nay**.
  - Định dạng thời gian: `HH:MM` (Ví dụ: `14:30`).

## 🎮 Các lệnh khác
- `/steam_profile [id]`: Xem thông tin Steam (chấp nhận cả SteamID64 hoặc Custom URL).
- `/system_monitor`: Xem tình trạng CPU, RAM của máy chủ.
- `!torrent [link]`: Tải file qua link magnet hoặc torrent (Lệnh tiền tố `!`).

## 📝 Lưu ý
- Khi chạy lần đầu, bot sẽ mở trình duyệt để yêu cầu bạn cấp quyền truy cập Lịch Google. Sau khi đồng ý, file `token.json` sẽ được tạo ra để duy trì đăng nhập.
- Luôn giữ file `credentials.json` và `.env` bảo mật.
