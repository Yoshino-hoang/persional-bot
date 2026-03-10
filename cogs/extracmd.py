import asyncio
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import aiohttp
import os

# Quyền hạn truy cập Google Calendar (đọc và ghi sự kiện)
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class GoogleCalendarService:
    """Dịch vụ quản lý kết nối và thao tác với Google Calendar API"""
    def __init__(self):
        self.creds = self._authenticate()
        # Khởi tạo instance API chính thức từ Google
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _authenticate(self):
        """Xử lý quy trình xác thực OAuth 2.0 (Lưu token vào file token.json)"""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def get_upcoming_events(self, limit=5):
        """Lấy danh sách các sự kiện sắp tới trong lịch chính (primary)"""
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' cho múi giờ UTC
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=limit,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    
    def add_event(self, summary, description, start_time_str, end_time_str):
        """Thêm sự kiện mới. Định dạng thời gian yêu cầu: YYYY-MM-DDTHH:MM:SS"""
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time_str,
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'dateTime': end_time_str,
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }
        event_result = self.service.events().insert(calendarId='primary', body=event).execute()
        return event_result.get('htmlLink')

class SteamService:
    """Dịch vụ kết nối Steam Web API, tối ưu hóa bằng Persistent Session và Async"""
    def __init__(self):
        self.api_key = os.getenv("STEAM_API")
        self.base_url = "http://api.steampowered.com"
        self._session = None # Session dùng chung để không phải mở kết nối nhiều lần

    async def get_session(self):
        """Khởi tạo session nếu chưa có (Tăng tốc độ request mạng)"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Đóng session khi bot tắt để giải phóng tài nguyên hệ thống"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get(self, url, params):
        """Hàm thực hiện yêu cầu GET với cơ chế Timeout (10s) và Logging theo dõi hiệu năng"""
        session = await self.get_session()
        start_time = datetime.datetime.now()
        api_name = url.split('/')[-2]
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, params=params, timeout=timeout) as response:
                duration = (datetime.datetime.now() - start_time).total_seconds()
                if response.status == 200:
                    print(f"DEBUG: [Steam API] {api_name} - Thành công ({duration}s)")
                    return await response.json()
                else:
                    print(f"DEBUG: [Steam API] {api_name} - Lỗi {response.status} ({duration}s)")
                    return None
        except asyncio.TimeoutError:
            print(f"DEBUG: [Steam API] {api_name} - TIMEOUT/NGHẼN")
            return None
        except Exception as e:
            print(f"DEBUG: [Steam API] Error: {e}")
            return None

    async def get_player_summary(self, steam_id_64):
        """Lấy thông tin cơ bản: Tên, Avatar, Trạng thái Online, Ngày tạo tài khoản"""
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {'key': self.api_key, 'steamids': steam_id_64}
        data = await self._get(url, params)
        if data:
            players = data.get('response', {}).get('players', [])
            return players[0] if players else None
        return None

    async def resolve_vanity_url(self, vanity_url):
        """Chuyển đổi Custom URL (tên chữ) sang SteamID64 (dãy số)"""
        url = f"{self.base_url}/ISteamUser/ResolveVanityURL/v0001/"
        params = {'key': self.api_key, 'vanityurl': vanity_url}
        data = await self._get(url, params)
        if data and data.get('response', {}).get('success') == 1:
            return data['response']['steamid']
        return None

    async def get_player_bans(self, steam_id_64):
        """Kiểm tra xem người chơi có bị cấm (VAC, Community, Economy) hay không"""
        url = f"{self.base_url}/ISteamUser/GetPlayerBans/v1/"
        params = {'key': self.api_key, 'steamids': steam_id_64}
        data = await self._get(url, params)
        if data:
            players = data.get('players', [])
            return players[0] if players else None
        return None

    async def get_owned_games(self, steam_id_64):
        """Lấy danh sách toàn bộ game trong thư viện (Yêu cầu Game Details: Public)"""
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            'key': self.api_key,
            'steamid': steam_id_64,
            'include_appinfo': True, 
            'include_played_free_games': True
        }
        data = await self._get(url, params)
        return data.get('response', {}) if data else {}

    async def get_recently_played_games(self, steam_id_64):
        """Lấy thông tin các game chơi nhiều nhất trong 2 tuần gần đây"""
        url = f"{self.base_url}/IPlayerService/GetRecentlyPlayedGames/v1/"
        params = {'key': self.api_key, 'steamid': steam_id_64, 'count': 3}
        data = await self._get(url, params)
        return data.get('response', {}).get('games', []) if data else []

    async def search_game_id(self, game_name):
        """Tìm AppID của một game trên Store dựa trên từ khóa tên"""
        url = "https://store.steampowered.com/api/storesearch/"
        params = {'term': game_name, 'l': 'english', 'cc': 'VN'}
        data = await self._get(url, params)
        if data and data.get('total') > 0:
            return data['items'][0] 
        return None

    async def get_current_players(self, app_id):
        """Lấy số lượng người chơi đang Online hiện tại của một game cụ thể"""
        url = f"{self.base_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        params = {'appid': app_id}
        data = await self._get(url, params)
        return data.get('response', {}).get('player_count', 0) if data else 0

    async def get_app_details(self, app_id):
        """Lấy chi tiết Store: Giá tiền, Thành tựu (Achievements), Ảnh bìa, Mô tả"""
        url = "https://store.steampowered.com/api/appdetails"
        params = {'appids': app_id, 'cc': 'VN', 'l': 'vietnamese'}
        data = await self._get(url, params)
        if data and str(app_id) in data and data[str(app_id)].get('success'):
            return data[str(app_id)]['data']
        return None

    async def get_user_stats_for_game(self, steam_id_64, app_id=730):
        """Lấy chỉ số in-game (Kills, Deaths, Wins...) cho một game (Mặc định CS2)"""
        url = f"{self.base_url}/ISteamUserStats/GetUserStatsForGame/v0002/"
        params = {'key': self.api_key, 'steamid': steam_id_64, 'appid': app_id}
        data = await self._get(url, params)
        return data.get('playerstats', {}).get('stats', []) if data else None
