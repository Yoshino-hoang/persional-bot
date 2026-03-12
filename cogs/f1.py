import discord
from discord.ext import commands, tasks
import fastf1
import pandas as pd
import datetime
import os
import asyncio

class F1(commands.Cog):
    """
    Cog quản lý dữ liệu đua xe Công thức 1 (F1) sử dụng thư viện Fast-F1.
    Hỗ trợ xem lịch đua, kết quả chặng, so sánh tay đua và thông báo tự động.
    """
    def __init__(self, bot):
        self.bot = bot
        # Lấy ID kênh thông báo từ biến môi trường
        self.channel_id = os.getenv("F1_CHANNEL_ID")
        
        # Bắt đầu vòng lặp kiểm tra lịch đua hàng ngày
        self.check_f1_schedule.start()
        
        # Thiết lập bộ nhớ đệm (cache) cho FastF1 để tăng tốc độ tải dữ liệu từ máy chủ F1
        if not os.path.exists('f1_cache'):
            os.makedirs('f1_cache')
        fastf1.Cache.enable_cache('f1_cache')

    def cog_unload(self):
        """Hủy vòng lặp khi Cog bị gỡ bỏ"""
        self.check_f1_schedule.cancel()

    # --- TÁC VỤ CHẠY NGẦM (BACKGROUND TASK) ---
    @tasks.loop(hours=24)
    async def check_f1_schedule(self):
        """Kiểm tra xem hôm nay có sự kiện F1 nào không và tự động gửi thông báo vào kênh đã thiết lập."""
        if not self.channel_id:
            return

        channel = self.bot.get_channel(int(self.channel_id))
        if not channel:
            return

        try:
            # Lấy lịch trình của năm hiện tại
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)

            # Lọc các sự kiện diễn ra vào ngày hôm nay
            today = now.date()
            today_events = schedule[schedule['EventDate'].dt.date == today]

            if not today_events.empty:
                event = today_events.iloc[0]
                embed = discord.Embed(
                    title=f"🏎️ THÔNG BÁO F1: {event['EventName']}",
                    description=f"Hôm nay có sự kiện F1 tại **{event['Location']}**!",
                    color=discord.Color.red()
                )
                embed.add_field(name="Chặng đua chính thức", value=event['OfficialEventName'], inline=False)
                embed.set_footer(text="Đừng bỏ lỡ những giây phút tốc độ!")
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Lỗi khi kiểm tra lịch F1: {e}")

    @check_f1_schedule.before_loop
    async def before_check_f1(self):
        """Đợi bot sẵn sàng trước khi bắt đầu kiểm tra lịch"""
        await self.bot.wait_until_ready()

    # --- LỆNH THIẾT LẬP (SETUP) ---

    @discord.app_commands.command(name="f1_setup", description="Thiết lập phòng nhận thông báo F1 tự động hàng ngày")
    @discord.app_commands.describe(channel="Chọn phòng chat muốn nhận thông báo")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def f1_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Lưu ID kênh vào file .env để bot nhớ phòng thông báo sau khi khởi động lại."""
        await interaction.response.defer(ephemeral=True)

        try:
            env_path = '.env'
            key = "F1_CHANNEL_ID"
            value = str(channel.id)

            # Đọc nội dung file .env
            lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            # Cập nhật hoặc thêm mới ID kênh
            found = False
            new_line = f"{key}={value}\n"
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = new_line
                    found = True
                    break
            if not found:
                if lines and not lines[-1].endswith('\n'): lines[-1] += '\n'
                lines.append(new_line)

            # Ghi lại cấu hình vào file .env
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            # Cập nhật giá trị đang chạy trong bot
            self.channel_id = value
            await interaction.followup.send(f"✅ Đã thiết lập phòng thông báo F1: {channel.mention}")
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi khi lưu cấu hình: {e}")

    # --- CÁC LỆNH SLASH (SLASH COMMANDS) ---

    @discord.app_commands.command(name="f1_next", description="Xem thông tin chi tiết chặng đua F1 sắp tới")
    async def f1_next(self, interaction: discord.Interaction):
        """Hiển thị thời gian, địa điểm và hình ảnh của chặng đua tiếp theo."""
        await interaction.response.defer()
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            future_events = schedule[schedule['EventDate'] >= now]

            if future_events.empty:
                await interaction.followup.send("🏁 Mùa giải đã kết thúc. Hẹn gặp lại vào năm sau!")
                return

            next_event = future_events.iloc[0]
            banner_url = "https://images.alphacoders.com/131/1311111.png" # Ảnh minh họa chất lượng cao

            embed = discord.Embed(
                title=f"🏎️ CHẶNG TIẾP THEO: {next_event['EventName']}",
                description=f"**{next_event['OfficialEventName']}**",
                color=discord.Color.red()
            )
            embed.set_image(url=banner_url)
            embed.add_field(name="📍 Địa điểm", value=f"`{next_event['Location']}`", inline=True)
            embed.add_field(name="🔢 Vòng đua", value=f"`{next_event['RoundNumber']}`", inline=True)
            embed.add_field(name="📅 Ngày đua chính", value=f"**{next_event['EventDate'].strftime('%d/%m/%Y')}**", inline=False)
            
            # Thêm lịch trình các buổi tập (nếu có dữ liệu)
            if 'Session1' in next_event and pd.notna(next_event['Session1']):
                embed.add_field(name="🕒 Lịch trình dự kiến (UTC)", value=(
                    f"• Practice 1: {next_event['Session1Date'].strftime('%d/%m %H:%M')}\n"
                    f"• Qualifying: {next_event['Session4Date'].strftime('%d/%m %H:%M')}"
                ), inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi lấy dữ liệu: {e}")

    @discord.app_commands.command(name="f1_results", description="Xem kết quả Top 10 chặng đua gần nhất kèm Highlights")
    async def f1_results(self, interaction: discord.Interaction):
        """Lấy kết quả cuộc đua chính (Race) và cung cấp link xem lại trên YouTube."""
        await interaction.response.defer()
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            past_events = schedule[schedule['EventDate'] < now]

            if past_events.empty:
                await interaction.followup.send("Chưa có chặng đua nào diễn ra.")
                return

            last_event = past_events.iloc[-1]
            session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
            # Sử dụng asyncio.to_thread để tránh làm treo bot khi tải dữ liệu nặng từ FastF1
            await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)

            results = session.results.head(10)
            embed = discord.Embed(title=f"🏆 Kết quả: {last_event['EventName']}", color=discord.Color.gold())
            
            # Tạo link YouTube Highlights tự động dựa trên tên chặng đua
            yt_query = f"F1 {now.year} {last_event['EventName']} Race Highlights".replace(" ", "+")
            yt_link = f"https://www.youtube.com/results?search_query={yt_query}"

            res_text = ""
            for _, row in results.iterrows():
                # Tính toán sự thay đổi vị trí so với lúc xuất phát
                grid_diff = int(row['GridPosition']) - int(row['Position'])
                change = f"(+{grid_diff})" if grid_diff > 0 else (f"({grid_diff})" if grid_diff < 0 else "(=)")
                res_text += f"**{int(row['Position'])}. {row['FullName']}** {change}\n└ {row['TeamName']} | `{int(row['Points'])} pts`\n"

            embed.description = res_text
            embed.add_field(name="📺 Xem Highlights", value=f"[Click để xem trên YouTube]({yt_link})", inline=False)
            embed.set_footer(text="Dữ liệu cung cấp bởi Fast-F1 API")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi: {e}")

    @discord.app_commands.command(name="f1_driver", description="Tra cứu kết quả cá nhân của một tay đua trong chặng gần nhất")
    @discord.app_commands.describe(driver_name="Tên hoặc tên viết tắt (VD: VER, HAM, Norris)")
    async def f1_driver(self, interaction: discord.Interaction, driver_name: str):
        """Xem chi tiết về Fastest Lap, chiến thuật lốp và vị trí của một tay đua cụ thể."""
        await interaction.response.defer()
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            last_event = schedule[schedule['EventDate'] < now].iloc[-1]
            session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
            await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)

            # Tìm tay đua trong danh sách kết quả
            driver_info = session.results[
                (session.results['Abbreviation'].str.contains(driver_name.upper())) | 
                (session.results['FullName'].str.contains(driver_name, case=False))
            ]

            if driver_info.empty:
                await interaction.followup.send(f"Không tìm thấy tay đua: `{driver_name}`"); return

            d = driver_info.iloc[0]
            laps = session.laps.pick_driver(d['Abbreviation'])
            fastest_lap = laps.pick_fastest()
            
            # Lấy danh sách các loại lốp đã sử dụng
            compounds = ", ".join(laps['Compound'].unique())

            embed = discord.Embed(title=f"📊 Chỉ số: {d['FullName']}", color=discord.Color.blue())
            embed.add_field(name="Vị trí", value=f"P{int(d['Position'])} (Xuất phát: P{int(d['GridPosition'])})", inline=True)
            embed.add_field(name="Điểm số", value=f"{int(d['Points'])} pts", inline=True)
            embed.add_field(name="Tình trạng", value=d['Status'], inline=True)
            
            if pd.notna(fastest_lap['LapTime']):
                time_str = str(fastest_lap['LapTime']).split('.')[-1][:8]
                embed.add_field(name="⏱️ Fastest Lap", value=f"`{time_str}` (Vòng {int(fastest_lap['LapNumber'])})", inline=False)
            
            embed.add_field(name="🛞 Chiến thuật lốp", value=f"`{compounds}`", inline=False)
            embed.set_footer(text=f"Dữ liệu chặng: {last_event['EventName']}")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi: {e}")

async def setup(bot):
    await bot.add_cog(F1(bot))
