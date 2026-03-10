# Persional Bot - Trợ lý Đa năng (Google, Steam & F1)

Bot Discord cá nhân mạnh mẽ hỗ trợ quản lý công việc qua Google Calendar, theo dõi chỉ số Game từ Steam, cập nhật giải đua Công thức 1 (F1) tự động và hỗ trợ Designer tìm kiếm cảm hứng bằng AI.

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

### 🏎️ Theo dõi F1 (Fast-F1 & Ergast)
- **Lịch đua tự động:** Tự động kiểm tra và thông báo lịch đua hàng ngày vào phòng đã thiết lập.
- **Xem lịch (`/f1_next`):** Xem chặng đua tiếp theo kèm ảnh banner, địa điểm và thời gian.
- **Kết quả chặng (`/f1_results`):** Xem top 10 chặng vừa qua (thứ hạng, điểm, biến động vị trí xuất phát, khoảng cách thời gian).
- **Kết quả tay đua (`/f1_driver`):** Xem chỉ số cá nhân của 1 tay đua trong chặng gần nhất (Tìm theo tên, viết tắt hoặc số xe).
- **Bảng xếp hạng:** Xem BXH Tay đua (`/f1_wdc`) và BXH Đội đua (`/f1_wcc`) mùa giải hiện tại.

### 🎨 Công cụ cho Designer (`/ref`)
- **AI Inspiration:** Tự động vẽ ảnh minh họa ý tưởng dựa trên từ khóa bạn nhập (Sử dụng Pollinations AI).
- **Mở rộng Moodboard:** Cung cấp link tra cứu nhanh tới Pinterest và Behance đã điền sẵn từ khóa của bạn.

---

## 🛠 Cấu hình & Cài đặt

1. **Yêu cầu:** Python 3.8+, `fastf1`, `pandas`, `discord.py`...
2. **Cài đặt thư viện:** `pip install -r requirements.txt`.
3. **File `.env`:** Điền `DISCORD_TOKEN`, `STEAM_API`, và `MY_STEAM_ID`.
4. **Google API:** Đặt file `credentials.json` vào thư mục gốc và thêm email của bạn vào danh sách **Test users** trong Google Cloud Console.

## 📋 Danh sách Lệnh (Hỗ trợ cả Slash `/` và Prefix `!`)

| Lệnh | Mô tả |
| :--- | :--- |
| `/events` | Xem danh sách sự kiện sắp tới từ Lịch Google. |
| `/addevent` | Thêm sự kiện (Nhập đầy đủ: Tên, Bắt đầu, Kết thúc). |
| `/addtodayevent` | Thêm nhanh sự kiện vào **hôm nay** (Chỉ cần nhập giờ: HH:MM). |
| `/steam` | Xem chi tiết hồ sơ người chơi Steam. |
| `/cs2` | Xem chỉ số Counter-Strike 2 chi tiết của người chơi. |
| `/gamestat` | Tra cứu số người chơi và giá bán của game trên toàn hệ thống Steam. |
| `/f1_setup` | Cài đặt phòng nhận thông báo lịch đua F1 tự động. |
| `/f1_next` | Xem thông tin chặng đua F1 sắp tới. |
| `/f1_results` | Xem kết quả chặng đua F1 gần nhất (Top 10). |
| `/f1_driver` | Tra cứu kết quả của một tay đua trong chặng gần nhất. |
| `/f1_wdc` | Xem bảng xếp hạng Tay đua hiện tại. |
| `/f1_wcc` | Xem bảng xếp hạng Đội đua hiện tại. |
| `/ref` | Tìm kiếm hình ảnh cảm hứng và link tham khảo cho Designer. |

## 📝 Chú thích kỹ thuật
- Bot sử dụng **Persistent HTTP Sessions** để duy trì kết nối mạng ổn định.
- Cơ chế **xử lý song song (`asyncio.gather`)** giúp giảm thời gian phản hồi dữ liệu xuống mức thấp nhất.
- Tự động lưu **Cache FastF1** để tăng tốc độ truy xuất dữ liệu giải đua.
