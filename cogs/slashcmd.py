import discord
from discord import Interaction, app_commands
from discord.ext import commands
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from .extracmd import GoogleCalendarService, SteamService
import os
# Cog chứa các lệnh gạch chéo (Slash Commands)
class Slashcmd(commands.Cog): # Lớp Slashcmd đại diện cho một nhóm lệnh
    def __init__(self, bot):
        self.bot = bot
        self.calendar_service = None
        self.steam_service = SteamService()
        
        # Chỉ khởi tạo CalendarService nếu có file credentials.json
        if os.path.exists('credentials.json'):
            try:
                self.calendar_service = GoogleCalendarService()
            except Exception as e:
                print(f"Lỗi khởi tạo Google Calendar: {e}")

    @app_commands.command(name="hello", description="Chào hỏi bot")
    async def hello(self, interaction: discord.Interaction):
        # Phản hồi người dùng bằng cách nhắc (mention) tên của họ
        await interaction.response.send_message(f"Chào {interaction.user.mention}")

    @app_commands.command(name="hi", description="Chào hỏi bot (ngắn gọn)")
    async def hi_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Chào {interaction.user.name}")


    
    @app_commands.command(name="events", description="Xem danh sách sự kiện")
    async def list_events(self, interaction: discord.Interaction, limit: int = 5):
        if not self.calendar_service:
            await interaction.response.send_message("❌ Google Calendar Service chưa được cấu hình. Vui lòng kiểm tra file credentials.json!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Lấy danh sách sự kiện từ Google Calendar Service
            events = self.calendar_service.get_upcoming_events(limit=limit)

            if not events:
                await interaction.followup.send("Hôm nay bạn 'ế' show rồi, không có sự kiện nào cả!")
                return

            embed = discord.Embed(title="Lịch trình sắp tới", color=discord.Color.green())
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                clean_time = start.replace('T', ' ').split('+')[0]
                embed.add_field(
                    name=event.get('summary', 'Sự kiện không tên'),
                    value=f"`{clean_time}`",
                    inline=False
                )

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Đã có lỗi xẩy ra: {e}")

    @app_commands.command(name="addevent", description="Thêm sự kiện mới vào Lịch Google")
    @app_commands.describe(
        summary="Tên sự kiện",
        start_time="Thời gian bắt đầu (YYYY-MM-DDTHH:MM:SS) vd: 2023-10-25T15:30:00",
        end_time="Thời gian kết thúc (YYYY-MM-DDTHH:MM:SS) vd: 2023-10-25T16:30:00",
        description="Mô tả sự kiện (không bắt buộc)"
    )
    async def add_event(self, interaction: discord.Interaction, summary: str, start_time: str, end_time: str, description: str = ""):
        """Lệnh thêm sự kiện vào Google Calendar với đầy đủ ngày giờ"""
        if not self.calendar_service:
            await interaction.response.send_message("❌ Google Calendar Service chưa được cấu hình. Vui lòng kiểm tra file credentials.json!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Gọi service để thêm sự kiện
            link = self.calendar_service.add_event(summary, description, start_time, end_time)
            await interaction.followup.send(f"✅ Đã thêm sự kiện thành công! Xem tại: {link}")
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi khi thêm sự kiện (kiểm tra lại định dạng thời gian: YYYY-MM-DDTHH:MM:SS):\n`{e}`")

    @app_commands.command(name="addtodayevent", description="Thêm sự kiện nhanh vào NGÀY HÔM NAY")
    @app_commands.describe(
        summary="Tên sự kiện",
        start_time="Giờ bắt đầu (HH:MM) vd: 14:30",
        end_time="Giờ kết thúc (HH:MM) vd: 15:30",
        description="Mô tả sự kiện (không bắt buộc)"
    )
    async def today_event(self, interaction: discord.Interaction, summary: str, start_time: str, end_time: str, description: str = ""):
        """Lệnh thêm sự kiện nhanh cho ngày hôm nay, chỉ yêu cầu nhập giờ"""
        if not self.calendar_service:
            await interaction.response.send_message("❌ Google Calendar Service chưa được cấu hình!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Lấy ngày hiện tại định dạng YYYY-MM-DD (ISO format)
            today = datetime.date.today().isoformat()
            
            # Ghép ngày hiện tại với giờ người dùng nhập để tạo định dạng ISO chuẩn
            # Thêm :00 cho phần giây để đảm bảo đúng định dạng API yêu cầu
            full_start = f"{today}T{start_time}:00"
            full_end = f"{today}T{end_time}:00"

            # Định dạng ngày để hiển thị trong câu thông báo (VD: 10/03/2026)
            display_date = datetime.date.today().strftime('%d/%m/%Y')

            # Gọi service để thực hiện việc chèn sự kiện
            link = self.calendar_service.add_event(summary, description, full_start, full_end)
            
            # Phản hồi lại người dùng kèm theo thông tin tóm tắt và link xem lịch
            await interaction.followup.send(f"✅ Đã thêm sự kiện cho HÔM NAY ({display_date}) thành công!\n📌 **{summary}** ({start_time} - {end_time})\n🔗 Xem tại: {link}")
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi! Hãy đảm bảo bạn nhập đúng định dạng giờ HH:MM (vd: 09:00, 14:30).\nChi tiết: `{e}`")

    # Lệnh lấy thông tin hồ sơ Steam và hiển thị trên Discord
    @app_commands.command(name="steam_profile", description="Xem thông tin hồ sơ Steam")
    @app_commands.describe(steam_id="Nhập SteamID64 hoặc Tên định danh (Custom URL) của bạn")
    async def steam_profile(self, interaction: discord.Interaction, steam_id: str):
        await interaction.response.defer()
        
        # Nếu steam_id không phải là số (tức là người dùng nhập Custom URL)
        if not steam_id.isdigit():
            # Thử chuyển đổi tên sang ID
            resolved_id = await self.steam_service.resolve_vanity_url(steam_id)
            if resolved_id:
                steam_id = resolved_id
            else:
                await interaction.followup.send(f"❌ Không tìm thấy ID Steam cho tên: `{steam_id}`.")
                return

        player = await self.steam_service.get_player_summary(steam_id)
        
        if not player:
            await interaction.followup.send("❌ Không tìm thấy thông tin hoặc SteamID sai.")
            return

        embed = discord.Embed(
            title=f"Hồ sơ của {player.get('personaname')}",
            url=player.get('profileurl'),
            color=discord.Color.dark_blue()
        )
        embed.set_thumbnail(url=player.get('avatarfull'))
        
        # Ánh xạ mã trạng thái Steam sang chữ viết dễ hiểu
        status_map = {0: "Offline", 1: "Online", 2: "Bận", 3: "Away"}
        status = status_map.get(player.get('personastate', 0), "Ẩn")
        
        embed.add_field(name="Trạng thái", value=status, inline=True)
        if 'gameextratext' in player:
            embed.add_field(name="Đang chơi", value=player['gameextratext'], inline=True)

        await interaction.followup.send(embed=embed)
    

async def setup(bot):
    await bot.add_cog(Slashcmd(bot))