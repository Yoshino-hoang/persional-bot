import discord
from discord.ext import commands
import datetime
import asyncio
import os
from .extracmd import GoogleCalendarService, SteamService

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
        """Lệnh cơ bản: Chào người dùng theo tên"""
        await ctx.send(f"Chào {ctx.author.name}")

    @commands.command(name="hello")
    async def hello_prefix(self, ctx):
        """Lệnh cơ bản: Chào người dùng bằng mention"""
        await ctx.send(f"Chào {ctx.author.mention}")

    # --- NHÓM LỆNH GOOGLE CALENDAR ---

    @commands.command(name="events")
    async def list_events_prefix(self, ctx, limit: int = 5):
        """Lệnh (!events): Xem danh sách sự kiện sắp tới"""
        if not self.calendar_service:
            await ctx.send("❌ Lịch chưa được cấu hình credentials.json!"); return
        async with ctx.typing():
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
        """Lệnh (!addtodayevent): Thêm nhanh sự kiện vào ngày hôm nay."""
        if not self.calendar_service:
            await ctx.send("❌ Lịch chưa cấu hình!"); return
        try:
            today = datetime.date.today().isoformat()
            full_start, full_end = f"{today}T{start_time}:00", f"{today}T{end_time}:00"
            display_date = datetime.date.today().strftime('%d/%m/%Y')
            link = self.calendar_service.add_event(summary, description, full_start, full_end)
            await ctx.send(f"✅ Đã thêm: **{summary}** vào hôm nay ({display_date})\n🔗 [Xem lịch]({link})")
        except Exception as e:
            await ctx.send(f"❌ Lỗi định dạng giờ! VD chuẩn: !addtodayevent 'Họp Team' 14:00 15:00")

    # --- NHÓM LỆNH STEAM & GAME ---

    @commands.command(name="steam")
    async def steam_prefix(self, ctx, steam_id: str):
        """Lệnh (!steam): Xem hồ sơ Steam chi tiết"""
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
        """Lệnh (!cs2): Xem chỉ số kỹ năng Counter-Strike 2"""
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
        """Lệnh (!gamestat): Tra cứu số lượng người chơi và giá game"""
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

    # --- NHÓM LỆNH F1 ---
    
    @commands.command(name="f1_results")
    async def f1_results_prefix(self, ctx):
        """Lệnh (!f1_results): Xem kết quả chặng đua F1 gần nhất (Top 10)"""
        async with ctx.typing():
            try:
                import fastf1
                import pandas as pd
                now = datetime.datetime.now()
                schedule = fastf1.get_event_schedule(now.year)
                
                past_events = schedule[schedule['EventDate'] < now]
                if past_events.empty:
                    await ctx.send("Chưa có chặng đua nào diễn ra trong năm nay."); return

                last_event = past_events.iloc[-1]
                session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
                await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)
                
                results = session.results.head(10) # Lấy top 10
                
                embed = discord.Embed(title=f"🏆 Kết quả: {last_event['EventName']}", color=discord.Color.gold())
                
                result_text = ""
                for index, row in results.iterrows():
                    time_diff = str(row.get('Time')).split('.')[-1][:8] if pd.notna(row.get('Time')) else row['Status']
                    grid_diff = int(row['GridPosition']) - int(row['Position'])
                    grid_str = f"({'+' if grid_diff > 0 else ''}{grid_diff})" if grid_diff != 0 else "(-)"
                    
                    result_text += f"**{int(row['Position'])}. {row['FullName']}** {grid_str}\n"
                    result_text += f"└ {row['TeamName']} | `{int(row['Points'])} pts` | ⏱️ {time_diff}\n\n"
                
                embed.description = result_text
                embed.set_footer(text="Dữ liệu từ Fast-F1 | Mũi tên hiển thị thay đổi vị trí so với lúc xuất phát")
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Lỗi lấy kết quả: {e}")

    @commands.command(name="f1_wdc")
    async def f1_wdc_prefix(self, ctx):
        """Lệnh (!f1_wdc): Xem Bảng xếp hạng Tay đua (WDC) hiện tại"""
        async with ctx.typing():
            try:
                from fastf1.ergast import Ergast
                ergast = Ergast()
                now = datetime.datetime.now()
                standings = await asyncio.to_thread(ergast.get_driver_standings, season=now.year)
                if not standings or not standings.content or standings.content[0].empty:
                    await ctx.send("❌ Chưa có dữ liệu bảng xếp hạng cho mùa giải này."); return

                df = standings.content[0].head(10)
                embed = discord.Embed(title=f"🏆 Bảng xếp hạng Tay đua (WDC) {now.year}", color=discord.Color.gold())
                
                desc = ""
                for _, row in df.iterrows():
                    team = row['constructorNames'][0] if row['constructorNames'] else 'N/A'
                    desc += f"**{row['position']}. {row['givenName']} {row['familyName']}** ({team})\n└ Điểm: `{row['points']} pts` | Thắng: `{row['wins']}`\n\n"
                
                embed.description = desc
                embed.set_footer(text="Dữ liệu từ Ergast API (Top 10)")
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ Lỗi lấy dữ liệu WDC: {e}")

    @commands.command(name="f1_wcc")
    async def f1_wcc_prefix(self, ctx):
        """Lệnh (!f1_wcc): Xem Bảng xếp hạng Đội đua (WCC) hiện tại"""
        async with ctx.typing():
            try:
                from fastf1.ergast import Ergast
                ergast = Ergast()
                now = datetime.datetime.now()
                standings = await asyncio.to_thread(ergast.get_constructor_standings, season=now.year)
                if not standings or not standings.content or standings.content[0].empty:
                    await ctx.send("❌ Chưa có dữ liệu bảng xếp hạng cho mùa giải này."); return

                df = standings.content[0]
                embed = discord.Embed(title=f"🏎️ Bảng xếp hạng Đội đua (WCC) {now.year}", color=discord.Color.blue())
                
                desc = ""
                for _, row in df.iterrows():
                    desc += f"**{row['position']}. {row['constructorName']}**\n└ Điểm: `{row['points']} pts` | Thắng: `{row['wins']}`\n\n"
                
                embed.description = desc
                embed.set_footer(text="Dữ liệu từ Ergast API")
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ Lỗi lấy dữ liệu WCC: {e}")

    @commands.command(name="f1_compare")
    async def f1_compare_prefix(self, ctx, *, drivers: str):
        """
        Lệnh (!f1_compare): Vẽ biểu đồ so sánh Lap Time.
        Cú pháp: !f1_compare VER, HAM, NOR
        """
        async with ctx.typing():
            try:
                import matplotlib.pyplot as plt
                import fastf1
                import fastf1.plotting
                now = datetime.datetime.now()
                schedule = fastf1.get_event_schedule(now.year)
                past_events = schedule[schedule['EventDate'] < now]
                if past_events.empty:
                    await ctx.send("Chưa có dữ liệu."); return
                
                last_event = past_events.iloc[-1]
                session = fastf1.get_session(now.year, last_event['RoundNumber'], 'R')
                await asyncio.to_thread(session.load, telemetry=False, weather=False, messages=False)

                driver_list = [d.strip().upper() for d in drivers.split(',')]
                plt.style.use('dark_background')
                fig, ax = plt.subplots(figsize=(10, 6))
                
                found_any = False
                for drv in driver_list:
                    try:
                        laps = session.laps.pick_drivers(drv)
                        if laps.empty: continue
                        laps = laps.pick_wo_box() 
                        
                        y_values = laps['LapTime'].dt.total_seconds()
                        x_values = laps['LapNumber']
                        
                        color = fastf1.plotting.get_driver_color(drv, session=session) if drv in session.results['Abbreviation'].values else None
                        
                        ax.plot(x_values, y_values, label=drv, color=color, linewidth=2)
                        found_any = True
                    except Exception as e:
                        print(f"Lỗi vẽ tay đua {drv}: {e}")
                        continue

                if not found_any:
                    await ctx.send("❌ Không tìm thấy dữ liệu cho các tay đua đã nhập."); return

                ax.set_title(f"Lap Time Comparison: {last_event['EventName']} {now.year}", fontsize=14, pad=15)
                ax.set_xlabel("Lap Number", fontsize=12)
                ax.set_ylabel("Lap Time (Seconds)", fontsize=12)
                ax.legend(loc='upper right')
                ax.grid(color='gray', linestyle='--', alpha=0.3)
                
                plot_path = 'f1_comparison.png'
                plt.savefig(plot_path, dpi=150, bbox_inches='tight')
                plt.close(fig)

                file = discord.File(plot_path, filename="comparison.png")
                await ctx.send(content=f"📊 Biểu đồ so sánh Lap Time tại **{last_event['EventName']}**", file=file)
                
                if os.path.exists(plot_path):
                    os.remove(plot_path)
            except Exception as e:
                await ctx.send(f"❌ Lỗi vẽ biểu đồ: {e}")

    # --- DESIGNER ---

    @commands.command(name="ref")
    async def ref_prefix(self, ctx, *, query: str):
        """Lệnh (!ref): Tìm ảnh cảm hứng thiết kế bằng AI"""
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