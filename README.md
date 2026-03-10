# Persional Bot - Trợ lý Đa năng (Google & Steam Integration)

Bot Discord cá nhân mạnh mẽ hỗ trợ quản lý công việc qua Google Calendar, theo dõi chỉ số Game chuyên sâu từ Steam và hỗ trợ Designer tìm kiếm cảm hứng bằng AI.

## 🌟 Tính năng chính

### 📅 Quản lý Lịch (Google Calendar)
- **Xem lịch trình:** Lấy các sự kiện sắp tới một cách nhanh chóng.
- **Thêm nhanh (`/addtodayevent`):** Tự động nhận diện ngày hôm nay, chỉ cần nhập giờ (HH:MM).
- **Tạo sự kiện đầy đủ (`/addevent`):** Hỗ trợ đầy đủ ngày giờ và mô tả.

### 🎮 Hệ thống Steam & Game Stats
- **Hồ sơ chi tiết (`/steam`):** 
  - Xem trạng thái (Online/Offline/Bận).
  - Tự động tính thời gian đã Offline (VD: Cách đây 2 ngày).
  - Kiểm tra quốc gia, ngày tạo tài khoản và tình trạng cấm (VAC/Community Ban).
  - Xem hoạt động đang chơi hoặc game chơi gần nhất.
- **Chỉ số Counter-Strike 2 (`/cs2`):**
  - Xem Kills, Deaths, K/D Ratio, tỉ lệ Headshot.
  - Lấy tổng giờ chơi chính xác từ thư viện (thay vì in-game stats bị thiếu).
- **Tra cứu Game toàn cầu (`/gamestat`):**
  - Xem số lượng người chơi Online hiện tại trên toàn thế giới.
  - Xem giá bán thực tế (VNĐ) và trạng thái giảm giá.
  - Link nhanh tới SteamDB để soi biểu đồ Peak Player và giá rẻ nhất lịch sử.

### 🎨 Công cụ cho Designer (`/ref`)
- **AI Inspiration:** Tự động vẽ ảnh minh họa ý tưởng dựa trên từ khóa bạn nhập (Sử dụng Pollinations AI).
- **Mở rộng Moodboard:** Cung cấp link tra cứu nhanh tới Pinterest và Behance đã điền sẵn từ khóa của bạn.

---

## 🛠 Cấu hình & Cài đặt

1. **Yêu cầu:** Python 3.8+, [aria2c](https://aria2.github.io/).
2. **Cài đặt thư viện:** `pip install -r requirements.txt`.
3. **File `.env`:** Điền `DISCORD_TOKEN`, `STEAM_API`, và `MY_STEAM_ID`.
4. **Google API:** Đặt file `credentials.json` vào thư mục gốc và thêm email của bạn vào danh sách **Test users** trong Google Cloud Console.

## 📝 Chú thích kỹ thuật
- Bot sử dụng **Persistent HTTP Sessions** để duy trì kết nối mạng ổn định.
- Cơ chế **xử lý song song (`asyncio.gather`)** giúp giảm thời gian phản hồi dữ liệu xuống mức thấp nhất.
- Hệ thống **Logging & Timeout** giúp bot luôn hoạt động mượt mà, không bị treo khi API bên thứ ba gặp sự cố.
