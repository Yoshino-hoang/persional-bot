import discord
from discord import Interaction, app_commands
from discord.ext import commands
import datetime
import asyncio
from .extracmd import GoogleCalendarService, SteamService
import os

class Slashcmd(commands.Cog):
    """
    Cog quản lý các lệnh gạch chéo (Slash Commands) của Bot.
    Tích hợp các dịch vụ từ Google Calendar, Steam API và các công cụ tiện ích.
    """
    def __init__(self, bot):
        self.bot = bot
        self.calendar_service = None
        self.steam_service = SteamService()

        # Kiểm tra sự tồn tại của file credentials.json trước khi khởi tạo Google Calendar
        if os.path.exists('credentials.json'):
            try:
                self.calendar_service = GoogleCalendarService()
            except Exception as e:
                print(f"Lỗi khởi tạo Google Calendar: {e}")

    # --- NHÓM LỆNH CƠ BẢN ---

    @app_commands.command(name="hello", description="Chào hỏi Bot")
    async def hello(self, interaction: discord.Interaction):
        """Phản hồi câu chào bằng cách nhắc tên người dùng (mention)."""
        await interaction.response.send_message(f"Chào {interaction.user.mention}! Chúc bạn một ngày tốt lành.")

    # --- NHÓM LỆNH GOOGLE CALENDAR ---

    @app_commands.command(name="events", description="Xem danh sách các sự kiện sắp tới trong Google Calendar")
    @app_commands.describe(limit="Số lượng sự kiện tối đa (mặc định: 5)")
    async def list_events(self, interaction: discord.Interaction, limit: int = 5):
        """Lấy danh sách các sự kiện tương lai từ lịch chính."""
        if not self.calendar_service:
            await interaction.response.send_message("❌ Dịch vụ Lịch chưa được cấu hình. Vui lòng kiểm tra credentials.json.", ephemeral=True)
            return

        await interaction.response.defer() # Sử dụng defer() nếu API phản hồi chậm
        try:
            events = self.calendar_service.get_upcoming_events(limit=limit)
            if not events:
                await interaction.followup.send("Lịch trình của bạn đang trống.")
                return

            embed = discord.Embed(title="📅 Lịch trình sắp tới", color=discord.Color.green())
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Chuyển đổi định dạng thời gian ISO sang dạng dễ đọc hơn
                clean_time = start.replace('T', ' ').split('+')[0]
                embed.add_field(name=event.get('summary', 'Sự kiện'), value=f"`{clean_time}`", inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi lấy lịch: {e}")

    # --- NHÓM LỆNH STEAM ---

    @app_commands.command(name="gamestat", description="Tra cứu số người chơi Online và giá bán game trên Steam Store")
    @app_commands.describe(game_name="Tên game muốn tìm (VD: Black Myth Wukong)")
    async def global_game_stats(self, interaction: discord.Interaction, game_name: str):
        """
        Tìm kiếm AppID từ tên game và hiển thị thông tin giá cả, đánh giá và lượng người chơi.
        """
        await interaction.response.defer()
        # Bước 1: Tìm ID game
        search_url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=vietnamese&cc=VN"
        async with asyncio.Lock(): # Một cách quản lý session đơn giản
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as r:
                    data = await r.json()
                    items = data.get('items', [])
                    if not items:
                        await interaction.followup.send(f"❌ Không tìm thấy game `{game_name}`."); return
                    appid = items[0]['id']

        # Bước 2: Lấy thông tin chi tiết bằng Parallel Tasks
        tasks = [
            self.steam_service.get_current_players(appid),
            self.steam_service.get_app_details(appid)
        ]
        players, details = await asyncio.gather(*tasks)

        embed = discord.Embed(title=f"📈 {details.get('name')}", url=f"https://store.steampowered.com/app/{appid}", color=discord.Color.gold())
        embed.set_thumbnail(url=details.get('header_image'))
        embed.add_field(name="Online hiện tại", value=f"`{players:,}` người", inline=True)
        
        price_info = details.get('price_overview')
        price_text = price_info.get('final_formatted', 'Free') if price_info else "N/A"
        embed.add_field(name="Giá Store VN", value=f"`{price_text}`", inline=True)
        
        embed.add_field(name="Xem thêm", value=f"[SteamDB](https://steamdb.info/app/{appid}/)", inline=False)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Slashcmd(bot))
