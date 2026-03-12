import aiohttp
import json
import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GoogleCalendarService:
    """
    Lớp xử lý tương tác với Google Calendar API.
    Bao gồm xác thực (OAuth2) và các hành động: lấy sự kiện, thêm sự kiện.
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.creds = self._authenticate()
        # Xây dựng dịch vụ API Google Calendar v3
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _authenticate(self):
        """Xử lý quy trình xác thực người dùng bằng OAuth2."""
        creds = None
        # Kiểm tra nếu token đã được lưu (token.json)
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # Nếu không có token hoặc token hết hạn, thực hiện đăng nhập mới
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Lưu lại token mới cho lần sử dụng sau
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def get_upcoming_events(self, limit=5):
        """Lấy danh sách các sự kiện sắp tới từ lịch chính của người dùng."""
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=limit, singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def add_event(self, summary, description, start_time, end_time):
        """Tạo một sự kiện mới trên lịch chính."""
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Ho_Chi_Minh'},
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Ho_Chi_Minh'},
        }
        event = self.service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')

class SteamService:
    """
    Lớp xử lý tương tác với Steam Web API.
    Hỗ trợ tra cứu hồ sơ người chơi, danh sách game và thống kê người chơi toàn cầu.
    """
    def __init__(self):
        # Lấy API Key Steam từ biến môi trường
        self.api_key = os.getenv("STEAM_API")
        self.base_url = "https://api.steampowered.com"

    async def get_player_summary(self, steam_id):
        """Lấy thông tin tóm tắt hồ sơ (Avatar, Trạng thái, URL cá nhân)."""
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={steam_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                data = await r.json()
                players = data.get('response', {}).get('players', [])
                return players[0] if players else None

    async def get_current_players(self, appid):
        """Lấy số lượng người đang chơi một game cụ thể hiện tại (Online Count)."""
        url = f"{self.base_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                data = await r.json()
                return data.get('response', {}).get('player_count', 0)

    async def get_app_details(self, appid):
        """Lấy thông tin chi tiết về game từ Steam Store (Giá, Ảnh bìa, Đánh giá)."""
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=VN&l=vietnamese"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                data = await r.json()
                # Steam API Store trả về dictionary với key là AppID
                app_data = data.get(str(appid), {})
                return app_data.get('data', {}) if app_data.get('success') else {}
