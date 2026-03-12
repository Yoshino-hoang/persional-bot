import discord
from discord.ext import commands, tasks
import fastf1
import pandas as pd
import datetime
import os
import asyncio

class F1(commands.Cog):
    """Cog quản lý dữ liệu đua xe Công thức 1 (F1) sử dụng Fast-F1"""
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = os.getenv("F1_CHANNEL_ID")
        # Khởi động vòng lặp kiểm tra lịch đua hàng ngày
        self.check_f1_schedule.start()
        # Thiết lập cache cho FastF1 để tăng tốc độ tải dữ liệu (tạo thư mục f1_cache)
        if not os.path.exists('f1_cache'):
            os.makedirs('f1_cache')
        fastf1.Cache.enable_cache('f1_cache')

    def cog_unload(self):
        self.check_f1_schedule.cancel()

    # --- BACKGROUND TASK ---
    @tasks.loop(hours=24)
    async def check_f1_schedule(self):
        """Kiểm tra xem hôm nay có chặng đua nào không và thông báo vào phòng quy định"""
        if not self.channel_id:
            return

        channel = self.bot.get_channel(int(self.channel_id))
        if not channel:
            print(f"DEBUG: Không tìm thấy kênh F1 với ID {self.channel_id}")
            return

        try:
            # Lấy lịch trình của năm hiện tại
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            
            # Tìm các sự kiện diễn ra trong hôm nay
            today = now.date()
            today_events = schedule[schedule['EventDate'].dt.date == today]

            if not today_events.empty:
                event = today_events.iloc[0]
                embed = discord.Embed(
                    title=f"🏎️ THÔNG BÁO F1: {event['EventName']}",
                    description=f"Hôm nay có sự kiện F1 tại **{event['Location']}**!",
                    color=discord.Color.red()
                )
                embed.add_field(name="Chặng", value=event['OfficialEventName'], inline=False)
                embed.set_footer(text="Hãy sẵn sàng theo dõi!")
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Lỗi khi kiểm tra lịch F1: {e}")

    @check_f1_schedule.before_loop
    async def before_check_f1(self):
        await self.bot.wait_until_ready()

    # --- SETUP COMMAND ---

    @discord.app_commands.command(name="f1_setup", description="Thiết lập phòng nhận thông báo F1 tự động")
    @discord.app_commands.describe(channel="Chọn phòng chat bạn muốn bot gửi thông báo vào")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def f1_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Lưu ID kênh vào file .env và cập nhật cấu hình bot"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            env_path = '.env'
            key = "F1_CHANNEL_ID"
            value = str(channel.id)
            
            # Đọc nội dung file .env hiện tại
            lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Kiểm tra xem biến đã tồn tại chưa để ghi đè hoặc thêm mới
            found = False
            new_line = f"{key}={value}\n"
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = new_line
                    found = True
                    break
            
            if not found:
                # Nếu file không kết thúc bằng xuống dòng, thêm một cái
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
                lines.append(new_line)
            
            # Ghi lại vào file .env
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # Cập nhật biến trong bộ nhớ bot ngay lập tức
            self.channel_id = value
            
            await interaction.followup.send(f"✅ Đã thiết lập phòng thông báo F1 thành công: {channel.mention}\n(Thông tin đã được lưu vào file .env)")
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi khi lưu cấu hình: {e}")

    # --- SLASH COMMANDS ---

    @discord.app_commands.command(name="f1_next", description="Xem thông tin chặng đua F1 sắp tới kèm hình ảnh")
    async def f1_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            
            # Lọc các sự kiện sắp diễn ra (EventDate > hiện tại)
            future_events = schedule[schedule['EventDate'] >= now]
            
            if future_events.empty:
                await interaction.followup.send("🏁 Hết mùa giải rồi, hãy đợi năm sau nhé!")
                return

            next_event = future_events.iloc[0]
            
            # Tạo link ảnh banner dựa trên vị trí chặng đua (Logic giả lập hoặc dùng ảnh F1 đẹp)
            # F1 thường có cấu trúc ảnh banner: https://media.formula1.com/content/dam/fom-website/2024/United%20States/GP%20Preview/F1%202024%20USA%20GP%20Preview%20Banner.jpg
            location = next_event['Location']
            # Link ảnh nền F1 cực đẹp mặc định
            banner_url = "https://images.alphacoders.com/131/1311111.png" # Một ảnh F1 4K chất lượng cao
            
            embed = discord.Embed(
                title=f"🏎️ CHẶNG TIẾP THEO: {next_event['EventName']}",
                description=f"**{next_event['OfficialEventName']}**",
                color=discord.Color.red()
            )
            
            embed.set_image(url=banner_url)
            embed.add_field(name="📍 Địa điểm", value=f"`{location}`", inline=True)
            embed.add_field(name="🔢 Vòng đua (Round)", value=f"`{next_event['RoundNumber']}`", inline=True)
            embed.add_field(name="📅 Ngày đua chính", value=f"**{next_event['EventDate'].strftime('%d/%m/%Y')}**", inline=False)
            
            # Thêm thông tin các phiên tập (nếu có)
            if 'Session1' in next_event and pd.notna(next_event['Session1']):
                embed.add_field(name="⏱️ Lịch trình (UTC)", value=(
                    f"• Practice 1: {next_event['Session1Date'].strftime('%d/%m %H:%M')}\n"
                    f"• Qualifying: {next_event['Session4Date'].strftime('%d/%m %H:%M')}"
                ), inline=False)

            embed.set_footer(text="Formula 1 World Championship")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi lấy dữ liệu: {e}")

    @discord.app_commands.command(name="f1_results", description="Xem kết quả chặng đua gần nhất")
    async def f1_results(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            
            # Lấy sự kiện vừa mới kết thúc
            past_events = schedule[schedule['EventDate'] < now]
            if past_events.empty:
                await interaction.followup.send("Chưa có chặng đua nào diễn ra trong năm nay.")
                return

            last_event = past_events.iloc[-1]
            session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
            
            # Chỉ nạp kết quả (không nạp telemetry để chạy cho nhanh)
            await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)
            
            results = session.results.head(10) # Lấy top 10
            
            # Tạo link tìm kiếm highlights trên YouTube
            year = last_event['EventDate'].year
            event_name = last_event['EventName']
            search_query = f"F1 {year} {event_name} Race Highlights".replace(" ", "+")
            highlights_url = f"https://www.youtube.com/results?search_query={search_query}"

            embed = discord.Embed(
                title=f"🏆 Kết quả: {last_event['EventName']}", 
                description=f"**[📺 Xem Video Recap (Highlights)]({highlights_url})**\n\n",
                color=discord.Color.gold()
            )
            
            result_text = ""
            for index, row in results.iterrows():
                # Xử lý thời gian định dạng chuẩn đua xe
                if pd.notna(row.get('Time')):
                    t = row['Time']
                    total_seconds = t.total_seconds()
                    minutes = int(total_seconds // 60)
                    seconds = total_seconds % 60
                    time_diff = f"{minutes}:{seconds:06.3f}"
                else:
                    time_diff = row['Status']

                grid_diff = int(row['GridPosition']) - int(row['Position'])
                grid_str = f"({'+' if grid_diff > 0 else ''}{grid_diff})" if grid_diff != 0 else "(-)"
                
                result_text += f"**{int(row['Position'])}. {row['FullName']}** {grid_str}\n"
                result_text += f"└ {row['TeamName']} | `{int(row['Points'])} pts` | ⏱️ {time_diff}\n\n"
            
            embed.description += result_text
            embed.set_footer(text="Dữ liệu từ Fast-F1 | Mũi tên hiển thị thay đổi vị trí so với lúc xuất phát")
            
            # Thêm Button để xem highlights
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Xem Video Recap", url=highlights_url, style=discord.ButtonStyle.link, emoji="📺"))
            
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(f"Lỗi lấy kết quả: {e}. (Có thể dữ liệu chặng mới nhất chưa được cập nhật)")

    @discord.app_commands.command(name="f1_wdc", description="Xem Bảng xếp hạng Tay đua (WDC) hiện tại")
    async def f1_wdc(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            from fastf1.ergast import Ergast
            ergast = Ergast()
            now = datetime.datetime.now()
            
            # Chạy trong thread để không block bot
            standings = await asyncio.to_thread(ergast.get_driver_standings, season=now.year)
            if not standings or not standings.content or standings.content[0].empty:
                await interaction.followup.send("❌ Chưa có dữ liệu bảng xếp hạng cho mùa giải này.")
                return

            df = standings.content[0].head(10) # Lấy top 10
            
            embed = discord.Embed(title=f"🏆 Bảng xếp hạng Tay đua (WDC) {now.year}", color=discord.Color.gold())
            
            desc = ""
            for _, row in df.iterrows():
                team = row['constructorNames'][0] if row['constructorNames'] else 'N/A'
                desc += f"**{row['position']}. {row['givenName']} {row['familyName']}** ({team})\n└ Điểm: `{row['points']} pts` | Thắng: `{row['wins']}`\n\n"
            
            embed.description = desc
            embed.set_footer(text="Dữ liệu từ Ergast API (Top 10)")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi lấy dữ liệu WDC: {e}")

    @discord.app_commands.command(name="f1_wcc", description="Xem Bảng xếp hạng Đội đua (WCC) hiện tại")
    async def f1_wcc(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            from fastf1.ergast import Ergast
            ergast = Ergast()
            now = datetime.datetime.now()
            
            standings = await asyncio.to_thread(ergast.get_constructor_standings, season=now.year)
            if not standings or not standings.content or standings.content[0].empty:
                await interaction.followup.send("❌ Chưa có dữ liệu bảng xếp hạng cho mùa giải này.")
                return

            df = standings.content[0] # Lấy toàn bộ
            
            embed = discord.Embed(title=f"🏎️ Bảng xếp hạng Đội đua (WCC) {now.year}", color=discord.Color.blue())
            
            desc = ""
            for _, row in df.iterrows():
                desc += f"**{row['position']}. {row['constructorName']}**\n└ Điểm: `{row['points']} pts` | Thắng: `{row['wins']}`\n\n"
            
            embed.description = desc
            embed.set_footer(text="Dữ liệu từ Ergast API")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi lấy dữ liệu WCC: {e}")

    @discord.app_commands.command(name="f1_driver", description="Xem kết quả chặng gần nhất của 1 tay đua cụ thể")
    @discord.app_commands.describe(driver="Nhập tên (Max), viết tắt (VER) hoặc số xe (1)")
    async def f1_driver_result(self, interaction: discord.Interaction, driver: str):
        await interaction.response.defer()
        try:
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            past_events = schedule[schedule['EventDate'] < now]
            
            if past_events.empty:
                await interaction.followup.send("Chưa có chặng đua nào diễn ra."); return

            last_event = past_events.iloc[-1]
            session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
            # Nạp thêm dữ liệu laps để lấy thông tin lốp và vòng chạy nhanh nhất
            await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)
            
            results = session.results
            query = driver.lower()

            # Tìm kiếm tay đua trong danh sách kết quả
            driver_data = results[
                (results['FullName'].str.lower().str.contains(query)) | 
                (results['Abbreviation'].str.lower() == query) | 
                (results['DriverNumber'] == query)
            ]

            if driver_data.empty:
                await interaction.followup.send(f"❌ Không tìm thấy tay đua nào khớp với `{driver}`."); return

            d = driver_data.iloc[0]
            driver_code = d['Abbreviation']
            
            # Lấy thông tin vòng chạy của tay đua này
            driver_laps = session.laps.pick_drivers(driver_code)
            
            # 1. Lấy vòng chạy nhanh nhất
            fastest_lap = driver_laps.pick_fastest()
            fastest_lap_time = "N/A"
            if fastest_lap is not None and pd.notna(fastest_lap['LapTime']):
                # Định dạng thời gian MM:SS.mmm
                t = fastest_lap['LapTime']
                minutes = int(t.total_seconds() // 60)
                seconds = t.total_seconds() % 60
                fastest_lap_time = f"{minutes:02d}:{seconds:06.3f}"

            # 2. Lấy danh sách lốp đã sử dụng
            compounds = driver_laps['Compound'].unique().tolist()
            # Lọc bỏ các giá trị rác hoặc rỗng
            compounds = [c for g in [compounds] for c in g if pd.notna(c)]
            tire_str = " -> ".join(compounds) if compounds else "Không rõ"

            embed = discord.Embed(
                title=f"🏎️ Kết quả của {d['FullName']} ({driver_code})",
                description=f"Chặng: **{last_event['EventName']}**",
                color=discord.Color.blue()
            )
            
            team_color = d.get('TeamColor', 'FF0000')
            if pd.notna(team_color): embed.color = int(team_color, 16)

            embed.add_field(name="🏁 Thứ hạng", value=f"**P{int(d['Position'])}**", inline=True)
            embed.add_field(name="🚦 Xuất phát", value=f"P{int(d['GridPosition'])}", inline=True)
            embed.add_field(name="➕ Điểm số", value=f"{int(d['Points'])} pts", inline=True)
            
            embed.add_field(name="⏱️ Fastest Lap", value=f"`{fastest_lap_time}`", inline=True)
            embed.add_field(name="🛞 Chiến thuật lốp", value=f"`{tire_str}`", inline=True)
            embed.add_field(name="📊 Trạng thái", value=d['Status'], inline=True)
            
            embed.add_field(name="🏎️ Đội đua", value=d['TeamName'], inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi: {e}")

    @discord.app_commands.command(name="f1_compare", description="Vẽ biểu đồ so sánh Lap Time giữa các tay đua")
    @discord.app_commands.describe(drivers="Nhập tên các tay đua cách nhau bằng dấu phẩy (vd: VER, HAM, NOR)")
    async def f1_compare(self, interaction: discord.Interaction, drivers: str):
        await interaction.response.defer()
        try:
            import matplotlib.pyplot as plt
            import matplotlib as mpl
            import fastf1.plotting
            
            # 1. Chuẩn bị dữ liệu chặng gần nhất
            now = datetime.datetime.now()
            schedule = fastf1.get_event_schedule(now.year)
            past_events = schedule[schedule['EventDate'] < now]
            if past_events.empty:
                await interaction.followup.send("Chưa có dữ liệu."); return
            
            last_event = past_events.iloc[-1]
            session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
            await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)

            # 2. Xử lý danh sách tay đua nhập vào
            driver_list = [d.strip().upper() for d in drivers.split(',')]
            
            # 3. Thiết lập biểu đồ (Dark Theme giống ảnh mẫu)
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            found_any = False
            for drv in driver_list:
                try:
                    # Lấy dữ liệu vòng chạy của từng tay đua
                    laps = session.laps.pick_drivers(drv)
                    if laps.empty: continue
                    
                    # Lọc bỏ các vòng không hợp lệ (ví dụ: vòng vào pit) để biểu đồ mượt hơn
                    laps = laps.pick_wo_box() 
                    
                    # Chuyển LapTime sang giây để vẽ
                    y_values = laps['LapTime'].dt.total_seconds()
                    x_values = laps['LapNumber']
                    
                    # Lấy màu đặc trưng của tay đua/đội đua
                    color = fastf1.plotting.get_driver_color(drv, session=session) if drv in session.results['Abbreviation'].values else None
                    
                    ax.plot(x_values, y_values, label=drv, color=color, linewidth=2)
                    found_any = True
                except Exception as e:
                    print(f"Lỗi vẽ tay đua {drv}: {e}")
                    continue

            if not found_any:
                await interaction.followup.send("❌ Không tìm thấy dữ liệu cho các tay đua đã nhập."); return

            # 4. Trang trí biểu đồ
            ax.set_title(f"Lap Time Comparison: {last_event['EventName']} {now.year}", fontsize=14, pad=15)
            ax.set_xlabel("Lap Number", fontsize=12)
            ax.set_ylabel("Lap Time (Seconds)", fontsize=12)
            ax.legend(loc='upper right')
            ax.grid(color='gray', linestyle='--', alpha=0.3)
            
            # Lưu ảnh vào file tạm
            plot_path = 'f1_comparison.png'
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

            # 5. Gửi ảnh lên Discord
            file = discord.File(plot_path, filename="comparison.png")
            await interaction.followup.send(content=f"📊 Biểu đồ so sánh Lap Time tại **{last_event['EventName']}**", file=file)
            
            # Xóa file sau khi gửi để dọn dẹp
            if os.path.exists(plot_path):
                os.remove(plot_path)

        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi vẽ biểu đồ: {e}")

async def setup(bot):
    await bot.add_cog(F1(bot))
