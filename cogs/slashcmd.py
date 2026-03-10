import discord
from discord import Interaction, app_commands
from discord.ext import commands
import datetime
import asyncio
from .extracmd import GoogleCalendarService, SteamService
import os

class Slashcmd(commands.Cog):
    """
    Lớp quản lý các lệnh gạch chéo (Slash Commands) của Bot.
    Bao gồm các nhóm tính năng: Google Calendar, Steam API, và Công cụ Designer.
    """
    def __init__(self, bot):
        self.bot = bot
        self.calendar_service = None
        self.steam_service = SteamService()
        
        # Kiểm tra file cấu hình Google trước khi khởi tạo dịch vụ Lịch
        if os.path.exists('credentials.json'):
            try:
                self.calendar_service = GoogleCalendarService()
            except Exception as e:
                print(f"Lỗi khởi tạo Lịch: {e}")

    # --- NHÓM LỆNH CƠ BẢN ---

    @app_commands.command(name="hello", description="Chào hỏi bot")
    async def hello(self, interaction: discord.Interaction):
        """Phản hồi chào hỏi người dùng bằng cách mention"""
        await interaction.response.send_message(f"Chào {interaction.user.mention}")

    @app_commands.command(name="hi", description="Chào hỏi bot (ngắn gọn)")
    async def hi_slash(self, interaction: discord.Interaction):
        """Phản hồi chào hỏi bằng tên hiển thị của người dùng"""
        await interaction.response.send_message(f"Chào {interaction.user.name}")

    # --- NHÓM LỆNH GOOGLE CALENDAR ---

    @app_commands.command(name="events", description="Xem danh sách sự kiện sắp tới trong Lịch Google")
    @app_commands.describe(limit="Số lượng sự kiện muốn xem (mặc định là 5)")
    async def list_events(self, interaction: discord.Interaction, limit: int = 5):
        """
        Lấy và hiển thị các sự kiện sắp tới.
        Tham số:
            limit (int): Giới hạn số lượng sự kiện trả về.
        """
        if not self.calendar_service:
            await interaction.response.send_message("❌ Chưa cấu hình credentials.json! Vui lòng liên hệ Admin.", ephemeral=True)
            return
        
        await interaction.response.defer() # Duy trì kết nối nếu API Google phản hồi chậm
        try:
            events = self.calendar_service.get_upcoming_events(limit=limit)
            if not events:
                await interaction.followup.send("Hiện tại không có sự reply nào trong lịch trình sắp tới.")
                return

            embed = discord.Embed(title="📅 Lịch trình sắp tới", color=discord.Color.green())
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Chuyển đổi định dạng 2026-03-10T15:30:00+07:00 sang 2026-03-10 15:30:00
                clean_time = start.replace('T', ' ').split('+')[0]
                embed.add_field(name=event.get('summary', 'Sự kiện không tên'), value=f"`{clean_time}`", inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Đã xảy ra lỗi khi lấy lịch: {e}")

    @app_commands.command(name="addtodayevent", description="Thêm nhanh sự kiện vào ngày HÔM NAY")
    @app_commands.describe(
        summary="Tên ngắn gọn của sự kiện",
        start_time="Giờ bắt đầu (định dạng HH:MM, ví dụ: 09:00)",
        end_time="Giờ kết thúc (định dạng HH:MM, ví dụ: 10:30)",
        description="Chi tiết thêm về sự kiện (không bắt buộc)"
    )
    async def today_event(self, interaction: discord.Interaction, summary: str, start_time: str, end_time: str, description: str = ""):
        """
        Tự động lấy ngày hiện tại và ghép với giờ người dùng nhập để tạo sự kiện nhanh.
        Tham số:
            summary (str): Tên sự kiện.
            start_time (str): Chuỗi giờ bắt đầu (HH:MM).
            end_time (str): Chuỗi giờ kết thúc (HH:MM).
        """
        if not self.calendar_service:
            await interaction.response.send_message("❌ Dịch vụ Lịch chưa được kích hoạt!", ephemeral=True)
            return

        await interaction.response.defer()
        try:
            today = datetime.date.today().isoformat()
            # Ghép thành chuẩn ISO 8601: YYYY-MM-DDTHH:MM:00
            full_start, full_end = f"{today}T{start_time}:00", f"{today}T{end_time}:00"
            display_date = datetime.date.today().strftime('%d/%m/%Y')
            
            link = self.calendar_service.add_event(summary, description, full_start, full_end)
            await interaction.followup.send(f"✅ Đã thêm sự kiện: **{summary}** vào lịch hôm nay ({display_date})\n🔗 [Xem chi tiết trên Google Calendar]({link})")
        except Exception as e:
            await interaction.followup.send(f"❌ Định dạng giờ không hợp lệ! Vui lòng dùng HH:MM (ví dụ: 14:00).\nChi tiết: `{e}`")

    # --- NHÓM LỆNH STEAM ---

    @app_commands.command(name="steam", description="Xem thông tin chi tiết hồ sơ người chơi Steam")
    @app_commands.describe(steam_id="Nhập SteamID64 (dãy số) hoặc Custom URL (tên định danh trong link profile)")
    async def steam_profile(self, interaction: discord.Interaction, steam_id: str):
        """
        Tra cứu hồ sơ người chơi từ nhiều API Steam cùng lúc.
        Tham số:
            steam_id (str): Có thể là dãy số 17 chữ số hoặc tên tùy chỉnh (Vanity URL).
        """
        await interaction.response.defer()
        
        # Tự động xử lý nếu người dùng nhập Custom URL thay vì SteamID64
        if not steam_id.isdigit():
            resolved = await self.steam_service.resolve_vanity_url(steam_id)
            if not resolved:
                await interaction.followup.send(f"❌ Không tìm thấy người chơi nào có tên định danh: `{steam_id}`"); return
            steam_id = resolved

        # Kỹ thuật Parallel Request: Chạy 4 tác vụ lấy dữ liệu cùng lúc để phản hồi siêu tốc
        tasks = [
            self.steam_service.get_player_summary(steam_id),
            self.steam_service.get_player_bans(steam_id),
            self.steam_service.get_owned_games(steam_id),
            self.steam_service.get_recently_played_games(steam_id)
        ]
        player, bans, owned, recent = await asyncio.gather(*tasks)

        if not player:
            await interaction.followup.send("❌ Không thể lấy dữ liệu từ Steam. Hãy kiểm tra lại ID."); return

        embed = discord.Embed(title=f"🎮 Hồ sơ Steam: {player.get('personaname')}", url=player.get('profileurl'), color=discord.Color.blue())
        embed.set_thumbnail(url=player.get('avatarfull'))
        
        # Tính toán thời gian offline nếu người dùng không Online
        status_map = {0: "Offline", 1: "Online", 2: "Bận", 3: "Away", 4: "Snooze"}
        st_text = status_map.get(player.get('personastate', 0), "Ẩn")
        if player.get('personastate') == 0 and 'lastlogoff' in player:
            diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(player['lastlogoff'])
            off_time = f"{diff.days} ngày" if diff.days > 0 else f"{diff.seconds//3600} giờ"
            st_text += f" (Cách đây {off_time})"
        
        embed.add_field(name="Trạng thái", value=f"`{st_text}`", inline=True)
        # Quốc gia (kèm flag biểu tượng)
        country = player.get('loccountrycode', 'N/A')
        embed.add_field(name="Quốc gia", value=f":flag_{country.lower()}: {country}" if country != 'N/A' else "N/A", inline=True)
        embed.add_field(name="Tổng số game", value=f"`{owned.get('game_count', 0)}` games", inline=True)

        # Ngày tạo tài khoản (convert từ timestamp)
        if 'timecreated' in player:
            date = datetime.datetime.fromtimestamp(player['timecreated']).strftime('%d/%m/%Y')
            embed.add_field(name="Ngày tạo", value=f"`{date}`", inline=True)

        # Kiểm tra các lệnh cấm của hệ thống
        if bans:
            b_list = []
            if bans.get('VACBanned'): b_list.append("VAC")
            if bans.get('CommunityBanned'): b_list.append("Community")
            ban_msg = "✅ Sạch sẽ" if not b_list else "❌ Bị cấm: " + ", ".join(b_list)
            embed.add_field(name="Tình trạng cấm", value=f"`{ban_msg}`", inline=True)

        # Hiển thị game đang chơi hoặc game chơi gần nhất trong 2 tuần
        if 'gameextratext' in player:
            embed.add_field(name="Đang chơi", value=f"🕹 **{player['gameextratext']}**", inline=False)
        elif recent:
            g = recent[0]
            embed.add_field(name="Hoạt động gần nhất", value=f"• **{g['name']}** ({round(g['playtime_2weeks']/60, 1)} giờ trong 2 tuần)", inline=False)

        embed.set_footer(text=f"SteamID64: {steam_id}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="cs2", description="Xem chỉ số kỹ năng Counter-Strike 2 chi tiết")
    @app_commands.describe(steam_id="Nhập SteamID64 hoặc Custom URL của người chơi")
    async def cs2_stats(self, interaction: discord.Interaction, steam_id: str):
        """
        Lấy thông số chiến đấu trong CS2 (Kills, HS, Winrate) và giờ chơi thực tế.
        """
        await interaction.response.defer()
        if not steam_id.isdigit():
            steam_id = await self.steam_service.resolve_vanity_url(steam_id)
            if not steam_id: await interaction.followup.send("❌ Sai định dạng ID!"); return

        # Kết hợp dữ liệu từ hồ sơ, chỉ số game và thư viện (để lấy giờ chơi chuẩn)
        tasks = [
            self.steam_service.get_player_summary(steam_id),
            self.steam_service.get_user_stats_for_game(steam_id, 730),
            self.steam_service.get_owned_games(steam_id)
        ]
        player, stats_list, owned = await asyncio.gather(*tasks)

        if not stats_list:
            await interaction.followup.send("❌ Không thể lấy chỉ số! Hãy đảm bảo hồ sơ Steam & Game Details của bạn là 'Công khai'."); return

        # Chuyển list stats của Steam sang dictionary để truy xuất nhanh
        s = {st['name']: st['value'] for st in stats_list}
        kills, deaths = s.get('total_kills', 0), s.get('total_deaths', 0)
        kd = round(kills/deaths, 2) if deaths > 0 else kills
        hs_ratio = round((s.get('total_kills_headshot', 0)/kills)*100, 1) if kills > 0 else 0

        embed = discord.Embed(title=f"🔫 Chỉ số CS2: {player.get('personaname')}", color=discord.Color.orange())
        embed.set_thumbnail(url=player.get('avatarfull'))
        embed.add_field(name="Mạng hạ gục (Kills)", value=f"`{kills:,}`", inline=True)
        embed.add_field(name="Số lần chết (Deaths)", value=f"`{deaths:,}`", inline=True)
        embed.add_field(name="Tỉ lệ K/D", value=f"`{kd}`", inline=True)
        embed.add_field(name="Tỉ lệ Headshot", value=f"`{hs_ratio}%`", inline=True)
        
        # Lấy giờ chơi từ thư viện game sẽ chính xác hơn số giờ trong trận
        if 'games' in owned:
            game = next((g for g in owned['games'] if g['appid'] == 730), None)
            if game: embed.add_field(name="Tổng giờ chơi", value=f"`{round(game['playtime_forever']/60, 1)}` giờ", inline=True)

        embed.set_footer(text="Dữ liệu tổng hợp toàn thời gian (All-time)")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gamestat", description="Tra cứu số người chơi Online và giá bán game trên hệ thống Steam")
    @app_commands.describe(game_name="Tên game cần tìm (ví dụ: Black Myth Wukong, Elden Ring...)")
    async def global_game_stats(self, interaction: discord.Interaction, game_name: str):
        """
        Xem thông tin thị trường của game: Số người chơi hiện tại và giá Store VN.
        """
        await interaction.response.defer()
        # Tìm AppID từ tên chữ
        search = await self.steam_service.search_game_id(game_name)
        if not search: await interaction.followup.send(f"❌ Không tìm thấy game nào có tên `{game_name}`!"); return
        
        appid = search['id']
        tasks = [self.steam_service.get_current_players(appid), self.steam_service.get_app_details(appid)]
        players, details = await asyncio.gather(*tasks)

        embed = discord.Embed(title=f"📊 Thông tin game: {details.get('name')}", url=f"https://store.steampowered.com/app/{appid}", color=discord.Color.gold())
        embed.set_thumbnail(url=details.get('header_image'))
        embed.add_field(name="👥 Đang Online", value=f"`{players:,}` người chơi", inline=True)
        
        # Xử lý giá tiền (VNĐ) hoặc trạng thái miễn phí
        price = details.get('price_overview')
        price_txt = price.get('final_formatted', 'Free') if price else ("Miễn phí" if details.get('is_free') else "N/A")
        embed.add_field(name="💰 Giá hiện tại", value=price_txt, inline=True)
        
        embed.add_field(name="📈 Biểu đồ chi tiết", value=f"[Xem Peak Player & Giá rẻ nhất trên SteamDB](https://steamdb.info/app/{appid}/)", inline=False)
        await interaction.followup.send(embed=embed)

    # --- NHÓM LỆNH CHO DESIGNER ---

    @app_commands.command(name="ref", description="Tìm kiếm ý tưởng và hình ảnh cảm hứng (AI Generated References)")
    @app_commands.describe(query="Mô tả ý tưởng muốn tìm (ví dụ: Cyberpunk UI, Cute character design...)")
    async def design_ref(self, interaction: discord.Interaction, query: str):
        """
        Vẽ ảnh minh họa bằng AI và cung cấp bộ link moodboard tra cứu thực tế.
        """
        await interaction.response.defer()
        import urllib.parse
        encoded = urllib.parse.quote(query)
        # Sử dụng dịch vụ tạo ảnh AI của Pollinations (Tốc độ cao, chất lượng tốt)
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true"
        
        embed = discord.Embed(title=f"🎨 Ý tưởng cho: {query}", description="Hình ảnh dưới đây được tạo ngẫu nhiên bởi AI để gợi ý cảm hứng.", color=discord.Color.from_rgb(255, 105, 180))
        embed.set_image(url=img_url)
        # Cung cấp bộ link tới các sàn thiết kế lớn để designer tìm reference thực tế
        embed.add_field(name="🔗 Mở rộng tìm kiếm thực tế tại", value=f"[Pinterest](https://www.pinterest.com/search/pins/?q={encoded}) | [Behance](https://www.behance.net/search/projects?search={encoded}) | [Dribbble](https://dribbble.com/search/{encoded})", inline=False)
        
        embed.set_footer(text="Lưu ý: Ảnh AI chỉ mang tính chất tham khảo ý tưởng thị giác.")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Slashcmd(bot))
