import discord
from discord.ext import commands
from .extracmd import GoogleCalendarService, SteamService
import os

# Cog này chứa các lệnh sử dụng tiền tố (!)
class Preflixcmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.calendar_service = None
        self.steam_service = SteamService()
        
        # Kiểm tra credentials cho Google Calendar
        if os.path.exists('credentials.json'):
            try:
                self.calendar_service = GoogleCalendarService()
            except Exception as e:
                print(f"Lỗi khởi tạo Google Calendar (Prefix): {e}")

    @commands.command(name="hi")
    async def hi_prefix(self, ctx):
        await ctx.send(f"Chào {ctx.author.name}")

    @commands.command(name="hello")
    async def hello_prefix(self, ctx):
        await ctx.send(f"Chào {ctx.author.mention}")

    @commands.command(name="events")
    async def events_prefix(self, ctx, limit: int = 5):
        if not self.calendar_service:
            await ctx.send("❌ Google Calendar Service chưa được cấu hình. Vui lòng kiểm tra file credentials.json!")
            return

        try:
            events = self.calendar_service.get_upcoming_events(limit=limit)
            if not events:
                await ctx.send("Hôm nay bạn 'ế' show rồi, không có sự kiện nào cả!")
                return

            embed = discord.Embed(title="Lịch trình sắp tới", color=discord.Color.green())
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                clean_time = start.replace('T', ' ').split('+')[0]
                embed.add_field(name=event.get('summary', 'Sự kiện không tên'), value=f"`{clean_time}`", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Đã có lỗi xảy ra: {e}")

    @commands.command(name="steam_profile")
    async def steam_prefix(self, ctx, steam_id: str):
        player = await self.steam_service.get_player_summary(steam_id)
        if not player:
            await ctx.send("❌ Không tìm thấy thông tin hoặc SteamID sai.")
            return

        embed = discord.Embed(title=f"Hồ sơ của {player.get('personaname')}", url=player.get('profileurl'), color=discord.Color.dark_blue())
        embed.set_thumbnail(url=player.get('avatarfull'))
        status_map = {0: "Offline", 1: "Online", 2: "Bận", 3: "Away"}
        status = status_map.get(player.get('personastate', 0), "Ẩn")
        embed.add_field(name="Trạng thái", value=status, inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Preflixcmd(bot))