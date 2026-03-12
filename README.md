# 🤖 Persional Bot - Trợ lý Đa năng (Smart Notes, Reminders & F1)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.7.0-blue.svg)](https://discordpy.readthedocs.io/en/stable/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Một bot Discord cá nhân mạnh mẽ được thiết kế để tối ưu hóa công việc và giải trí. Tích hợp từ quản lý ghi chú thông minh, nhắc nhở thời gian thực, đến dữ liệu chuyên sâu về giải đua Công thức 1 (F1) và chỉ số Game (Steam/CS2).

---

## 🚀 Tính năng Nổi bật

### 📝 Hệ thống Ghi chú Thông minh (Smart Notes)
Quản lý sổ tay cá nhân trực tiếp trên Discord với trải nghiệm mượt mà.
- **Hỗ trợ Đa phương tiện:** Đính kèm tối đa **5 ảnh** cho mỗi ghi chú.
- **Giao diện Lật trang (Pagination):** Xem danh sách ghi chú như một cuốn sổ tay thực thụ với các nút bấm ⬅️ Trước / Sau ➡️.
- **Hiển thị Lưới ảnh:** Tự động sắp xếp ảnh đính kèm thành lưới (Grid) đẹp mắt.
- **Quản lý linh hoạt:** Thêm, Sửa, Xóa và Xem chi tiết ghi chú công khai trong kênh chat.

### 🔔 Nhắc nhở Thời gian thực (Advanced Reminders)
Không bao giờ bỏ lỡ các mốc thời gian quan trọng.
- **Hẹn giờ linh hoạt:** Hỗ trợ định dạng thời gian tự nhiên (VD: `10m`, `1h30m`, `1d`).
- **Thông báo đa kênh:** Tự động tag người dùng trong kênh đã đặt lệnh hoặc gửi tin nhắn riêng (DM).
- **Chạy ngầm (Background Task):** Hệ thống kiểm tra liên tục mỗi 30 giây để đảm bảo độ chính xác.

### 🏎️ Theo dõi F1 Chuyên sâu (Formula 1 Insights)
Dành cho các tín đồ tốc độ với dữ liệu từ `Fast-F1` và `Ergast API`.
- **Lịch đua tự động:** Thông báo lịch chặng đua hàng ngày.
- **Kết quả & Highlights:** Xem Top 10 kèm link Video Recap YouTube ngay lập tức.
- **Phân tích Hiệu suất:** Vẽ biểu đồ so sánh Lap Time giữa các tay đua (VD: VER vs HAM).
- **Chiến thuật Lốp:** Xem chi tiết loại lốp (Tire Compounds) đã sử dụng trong chặng.

### 🎮 Steam & CS2 Statistics
- **Hồ sơ Steam:** Kiểm tra trạng thái Online, thời gian Offline, và tình trạng VAC Ban.
- **CS2 Stats:** Theo dõi K/D Ratio, tỉ lệ Headshot và tổng giờ chơi thực tế.
- **Thị trường Game:** Xem số người chơi Global và giá bán (VND) trực tiếp từ Steam Store.

### 🖥️ Giám sát Hệ thống (System Monitor)
- Theo dõi hiệu năng phần cứng (CPU, RAM, Disk) của máy chủ chạy bot.

---

## 🛠️ Cài đặt & Cấu hình

### 1. Yêu cầu Hệ thống
- Python 3.8 trở lên.
- Các API Keys: Discord Bot Token, Steam Web API Key, Google Cloud Console (cho Calendar).

### 2. Cài đặt Thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình Biến môi trường
Tạo tệp `.env` ở thư mục gốc và điền các thông tin sau:
```env
BOT_TOKEN=your_discord_bot_token
GG_API=your_google_calendar_api_key
STEAM_API=your_steam_web_api_key
OWNER_ID=your_discord_user_id
```

### 4. Google Calendar (Tùy chọn)
- Đặt file `credentials.json` vào thư mục gốc để kích hoạt tính năng lịch.

---

## 📜 Danh sách Lệnh (Slash Commands `/`)

### 📋 Quản lý Ghi chú (`/note`)
| Lệnh | Tham số | Mô tả |
| :--- | :--- | :--- |
| `/note add` | `content`, `image1...5` | Thêm ghi chú mới kèm tối đa 5 ảnh. |
| `/note list` | (Không) | Xem danh sách ghi chú dạng lật trang. |
| `/note view` | `note_id` | Xem chi tiết 1 ghi chú với ảnh lớn. |
| `/note edit` | `note_id`, `content`, `image...` | Sửa nội dung hoặc ảnh của ghi chú. |
| `/note delete` | `note_id` | Xóa ghi chú và tự động đánh lại số ID. |

### ⏰ Nhắc nhở (`/remind`)
| Lệnh | Tham số | Mô tả |
| :--- | :--- | :--- |
| `/remind set` | `time`, `content` | Đặt nhắc nhở (VD: `time: 10m`). |
| `/remind list` | (Không) | Xem các nhắc nhở đang chờ. |
| `/remind cancel`| `remind_id` | Hủy một nhắc nhở đã đặt. |

### 🏁 Formula 1
| Lệnh | Mô tả |
| :--- | :--- |
| `/f1_next` | Thông tin chặng đua F1 sắp tới. |
| `/f1_results`| Kết quả chặng gần nhất + Highlights. |
| `/f1_compare`| Biểu đồ so sánh Lap Time giữa các tay đua. |
| `/f1_wdc/wcc`| Bảng xếp hạng Tay đua / Đội đua. |

---

## 📁 Cấu trúc Thư mục
```text
├── main.py              # File khởi chạy bot chính
├── cogs/                # Thư mục chứa các module tính năng
│   ├── notes.py         # Module Ghi chú
│   ├── reminders.py     # Module Nhắc nhở
│   ├── f1.py            # Module Formula 1
│   └── system_monitor.py# Giám sát hệ thống
├── notes.json           # Cơ sở dữ liệu ghi chú
├── reminders.json       # Cơ sở dữ liệu nhắc nhở
└── requirements.txt     # Danh sách thư viện cần thiết
```

---

## 👤 Tác giả
- **Project Owner:** [Tên của bạn/GitHub]
- **Framework:** Discord.py

---
*Bot được tối ưu hóa hiệu năng bằng `asyncio` và duy trì kết nối ổn định qua `Persistent HTTP Sessions`.*
