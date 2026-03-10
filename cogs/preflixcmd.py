import discord
from discord.ext import commands
import datetime
import asyncio
from .extracmd import GoogleCalendarService, SteamService
import os

class Preflixcmd(commands.Cog):
    """Cog chứa các lệnh sử dụng tiền tố (!) - Đồng bộ 100% với Slash Commands"""
    def __init__(self, bot):
        self.bot = bot
        self.calendar_service = None
        self.steam_service = SteamService()
        
        if os.path.exists('credentials.json'):
            try:
                self.calendar_service = GoogleCalendarService()
            except Exception as e:
                print(f"Lỗi khởi tạo Lịch (Prefix): {e}")

    # --- NHÓM LỆNH CƠ BẢN ---

    @commands.command(name="hi")
    async def hi_prefix(self, ctx):
        """Chào người dùng theo tên"""
        await ctx.send(f"Chào {ctx.author.name}")

    @commands.command(name="hello")
    async def hello_prefix(self, ctx):
        """Chào người dùng bằng mention"""
        await ctx.send(f"Chào {ctx.author.mention}")

    # --- NHÓM LỆNH GOOGLE CALENDAR ---

    @commands.command(name="events")
    async def list_events_prefix(self, ctx, limit: int = 5):
        """Xem danh sách sự kiện sắp tới"""
        if not self.calendar_service:
            await ctx.send("❌ Lịch chưa được cấu hình credentials.json!"); return
        async with ctx.typing(): # Hiện hiệu ứng 'Bot is typing...'
            try:
                events = self.calendar_service.get_upcoming_events(limit=limit)
                if not events:
                    await ctx.send("Lịch trình trống!"); return
                embed = discord.Embed(title="📅 Lịch trình sắp tới", color=discord.Color.green())
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    clean_time = start.replace('T', ' ').split('+')[0]
                    embed.add_field(name=event.get('summary', 'Sự kiện'), value=f"`{clean_time}`", inline=False)
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Lỗi: {e}")

    @commands.command(name="addtodayevent")
    async def today_event_prefix(self, ctx, summary: str, start_time: str, end_time: str, *, description: str = ""):
        """Thêm nhanh sự kiện vào ngày hôm nay. VD: !addtodayevent 'Họp' 14:00 15:00"""
        if not self.calendar_service:
            await ctx.send("❌ Lịch chưa cấu hình!"); return
        try:
            today = datetime.date.today().isoformat()
            full_start, full_end = f"{today}T{start_time}:00", f"{today}T{end_time}:00"
            display_date = datetime.date.today().strftime('%d/%m/%Y')
            link = self.calendar_service.add_event(summary, description, full_start, full_end)
            await ctx.send(f"✅ Đã thêm: **{summary}** vào hôm nay ({display_date})\n🔗 [Xem lịch]({link})")
        except Exception as e:
            await ctx.send(f"❌ Lỗi định dạng giờ! VD: !addtodayevent 'Tên' 14:00 15:00")

    # --- NHÓM LỆNH STEAM ---

    @commands.command(name="steam")
    async def steam_prefix(self, ctx, steam_id: str):
        """Xem hồ sơ Steam chi tiết"""
        async with ctx.typing():
            if not steam_id.isdigit():
                steam_id = await self.steam_service.resolve_vanity_url(steam_id)
                if not steam_id: await ctx.send("❌ Không thấy ID!"); return

            tasks = [
                self.steam_service.get_player_summary(steam_id),
                self.steam_service.get_player_bans(steam_id),
                self.steam_service.get_owned_games(steam_id),
                self.steam_service.get_recently_played_games(steam_id)
            ]
            player, bans, owned, recent = await asyncio.gather(*tasks)

            if not player: await ctx.send("❌ Không có dữ liệu!"); return

            embed = discord.Embed(title=f"🎮 Hồ sơ: {player.get('personaname')}", url=player.get('profileurl'), color=discord.Color.blue())
            embed.set_thumbnail(url=player.get('avatarfull'))
            
            status_map = {0: "Offline", 1: "Online", 2: "Bận", 3: "Away"}
            st_text = status_map.get(player.get('personastate', 0), "Ẩn")
            if player.get('personastate') == 0 and 'lastlogoff' in player:
                diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(player['lastlogoff'])
                off = f"{diff.days} ngày" if diff.days > 0 else f"{diff.seconds//3600} giờ"
                st_text += f" (Offline {off} trước)"
            
            embed.add_field(name="Trạng thái", value=f"`{st_text}`", inline=True)
            embed.add_field(name="Quốc gia", value=f":flag_{player.get('loccountrycode', 'N/A').lower()}: {player.get('loccountrycode', 'N/A')}", inline=True)
            embed.add_field(name="Tổng game", value=f"`{owned.get('game_count', 0)}`", inline=True)

            if bans:
                b_list = [k for k, v in {"VAC": bans.get('VACBanned'), "Community": bans.get('CommunityBanned')}.items() if v]
                embed.add_field(name="Cấm", value="✅ Sạch" if not b_list else "❌: " + ", ".join(b_list), inline=True)

            if 'gameextratext' in player:
                embed.add_field(name="Đang chơi", value=f"🕹 **{player['gameextratext']}**", inline=False)
            elif recent:
                embed.add_field(name="Chơi gần nhất", value=f"• **{recent[0]['name']}** ({round(recent[0]['playtime_2weeks']/60, 1)}h)", inline=False)

            await ctx.send(embed=embed)

    @commands.command(name="cs2")
    async def cs2_prefix(self, ctx, steam_id: str):
        """Xem chỉ số Counter-Strike 2 chi tiết"""
        async with ctx.typing():
            if not steam_id.isdigit():
                steam_id = await self.steam_service.resolve_vanity_url(steam_id)
                if not steam_id: await ctx.send("❌ Sai ID!"); return

            tasks = [
                self.steam_service.get_player_summary(steam_id),
                self.steam_service.get_user_stats_for_game(steam_id, 730),
                self.steam_service.get_owned_games(steam_id)
            ]
            player, stats_list, owned = await asyncio.gather(*tasks)

            if not stats_list: await ctx.send("❌ Không lấy được stats (Hồ sơ phải Public)!"); return

            s = {st['name']: st['value'] for st in stats_list}
            kills, deaths = s.get('total_kills', 0), s.get('total_deaths', 0)
            kd = round(kills/deaths, 2) if deaths > 0 else kills
            hs = round((s.get('total_kills_headshot', 0)/kills)*100, 1) if kills > 0 else 0

            embed = discord.Embed(title=f"🔫 CS2 Stats: {player.get('personaname')}", color=discord.Color.orange())
            embed.set_thumbnail(url=player.get('avatarfull'))
            embed.add_field(name="Kills/Deaths", value=f"`{kills:,} / {deaths:,}`", inline=True)
            embed.add_field(name="K/D - HS%", value=f"`{kd} - {hs}%`", inline=True)
            
            if 'games' in owned:
                cs2 = next((g for g in owned['games'] if g['appid'] == 730), None)
                if cs2: embed.add_field(name="Giờ chơi", value=f"`{round(cs2['playtime_forever']/60, 1)}` giờ", inline=True)

            await ctx.send(embed=embed)

    @commands.command(name="gamestat")
    async def gamestat_prefix(self, ctx, *, game_name: str):
        """Tra cứu thông tin game trên toàn hệ thống Steam Store"""
        async with ctx.typing():
            search = await self.steam_service.search_game_id(game_name)
            if not search: await ctx.send("❌ Không thấy game!"); return
            
            appid = search['id']
            tasks = [self.steam_service.get_current_players(appid), self.steam_service.get_app_details(appid)]
            players, details = await asyncio.gather(*tasks)

            embed = discord.Embed(title=f"📊 {details.get('name')}", url=f"https://store.steampowered.com/app/{appid}", color=discord.Color.gold())
            embed.set_thumbnail(url=details.get('header_image'))
            embed.add_field(name="Online", value=f"`{players:,}` người", inline=True)
            
            pr = details.get('price_overview')
            price = pr.get('final_formatted', 'Free') if pr else ("Miễn phí" if details.get('is_free') else "N/A")
            embed.add_field(name="Giá", value=price, inline=True)
            embed.add_field(name="Link", value=f"[SteamDB](https://steamdb.info/app/{appid}/)", inline=True)
            await ctx.send(embed=embed)

    # --- DESIGNER ---

    @commands.command(name="ref")
    async def ref_prefix(self, ctx, *, query: str):
        """Tìm ảnh cảm hứng thiết kế bằng AI"""
        async with ctx.typing():
            import urllib.parse
            encoded = urllib.parse.quote(query)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true"
            embed = discord.Embed(title=f"🎨 Cảm hứng: {query}", color=discord.Color.from_rgb(255, 105, 180))
            embed.set_image(url=url)
            embed.add_field(name="Moodboard", value=f"[Pinterest](https://www.pinterest.com/search/pins/?q={encoded})", inline=False)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Preflixcmd(bot))
