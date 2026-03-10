import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import aiohttp
import os

# Quyền hạn cần thiết để truy cập Google Calendar (đọc và ghi sự kiện)
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Lớp dịch vụ quản lý việc kết nối và lấy dữ liệu từ Google Calendar
class GoogleCalendarService:
    def __init__(self):
        self.creds = self._authenticate() # Lấy chứng chỉ xác thực
        # Khởi tạo dịch vụ API của Google Calendar
        self.service = build('calendar', 'v3', credentials=self.creds)

    # Hàm ẩn (private) dùng để xử lý xác thực OAuth 2.0 với Google
    def _authenticate(self):
        creds = None
        # Kiểm tra xem file token.json có tồn tại (đã từng đăng nhập) chưa
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Nếu chưa có chứng chỉ hợp lệ
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Nếu token hết hạn nhưng có refresh_token, thì làm mới lại
                creds.refresh(Request())
            else:
                # Mở trình duyệt để người dùng cấp quyền truy cập
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Lưu lại chứng chỉ vào token.json cho lần chạy sau
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def get_upcoming_events(self, limit=5):
        """Hàm lấy danh sách các sự kiện sắp tới từ Lịch Google"""
        # Lấy thời gian hiện tại theo chuẩn UTC (Z)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        # Gọi API lấy sự kiện
        events_result = self.service.events().list(
            calendarId='primary', # Lịch chính của tài khoản
            timeMin=now,          # Chỉ lấy sự kiện từ bây giờ trở đi
            maxResults=limit,     # Giới hạn số lượng trả về
            singleEvents=True,
            orderBy='startTime'   # Sắp xếp theo thời gian bắt đầu
        ).execute()
        return events_result.get('items', [])
    
    def add_event(self, summary, description, start_time_str, end_time_str):
        """
        Thêm sự kiện mới vào Lịch Google.
        
        Args:
            summary (str): Tiêu đề sự kiện.
            description (str): Mô tả chi tiết.
            start_time_str (str): Thời gian bắt đầu (định dạng ISO 8601).
            end_time_str (str): Thời gian kết thúc (định dạng ISO 8601).
            
        Returns:
            str: Đường dẫn (link) đến sự kiện vừa tạo trên Google Calendar.
        """
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time_str,
                'timeZone': 'Asia/Ho_Chi_Minh', # Múi giờ Việt Nam
            },
            'end': {
                'dateTime': end_time_str,
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }
        # Gọi API để chèn sự kiện mới vào lịch chính (primary)
        event_result = self.service.events().insert(calendarId='primary', body=event).execute()
        return event_result.get('htmlLink')

# Lớp dịch vụ quản lý việc kết nối với Steam API
class SteamService:
    def __init__(self):
        # Lấy Steam API Key từ biến môi trường
        self.api_key = os.getenv("STEAM_API")
        self.base_url = "http://api.steampowered.com"

    # Hàm bất đồng bộ lấy thông tin người dùng từ Steam
    async def get_player_summary(self, steam_id_64):
        # Lấy thông tin cơ bản của một người chơi qua SteamID64
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            'key': self.api_key,
            'steamids': steam_id_64
        }

        # Sử dụng aiohttp để gọi HTTP request mà không làm chặn (block) bot Discord
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200: # Nếu API trả về thành công
                    data = await response.json()
                    players = data.get('response', {}).get('players', [])
                    # Trả về người chơi đầu tiên trong mảng hoặc None nếu không có
                    return players[0] if players else None
                return None

    async def resolve_vanity_url(self, vanity_url):
        """Chuyển đổi Custom URL (tên) sang SteamID64"""
        url = f"{self.base_url}/ISteamUser/ResolveVanityURL/v0001/"
        params = {
            'key': self.api_key,
            'vanityurl': vanity_url
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('response', {}).get('success') == 1:
                        return data['response']['steamid']
                return None