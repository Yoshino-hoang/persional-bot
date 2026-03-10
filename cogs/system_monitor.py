import discord
from discord import app_commands
from discord.ext import commands
import psutil # Thư viện lấy thông tin hệ thống
import platform # Thư viện lấy thông tin hệ điều hành
import datetime

class SystemMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_progress_bar(self, percent):
        """Hàm tạo thanh tiến trình trực quan bằng ký tự [■■■□□□]"""
        filled_length = int(percent / 10)
        bar = '■' * filled_length + '□' * (10 - filled_length)
        return f"[{bar}] {percent}%"

    @app_commands.command(name="status", description="Xem tình trạng hệ thống hiện tại")
    async def status(self, interaction: discord.Interaction):
        # Lấy thông tin CPU và RAM
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        
        # Lấy thông tin uptime (thời gian máy đã chạy)
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        # Tạo Embed hiển thị thông tin đẹp mắt
        embed = discord.Embed(title="📊 Tình trạng hệ thống", color=discord.Color.blue())
        embed.add_field(name="💻 CPU", value=self.get_progress_bar(cpu_usage), inline=False)
        embed.add_field(name="🧠 RAM", value=self.get_progress_bar(ram.percent), inline=False)
        embed.add_field(name="📉 RAM Detail", value=f"{ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB", inline=True)
        embed.add_field(name="🕒 Uptime", value=str(uptime).split('.')[0], inline=True)
        
        # Thêm thông tin về OS và độ trễ bot
        embed.set_footer(text=f"OS: {platform.system()} {platform.release()} | Ping: {round(self.bot.latency * 1000)}ms")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="info", description="Xem thông tin chi tiết phần cứng")
    async def info(self, interaction: discord.Interaction):
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        
        embed = discord.Embed(title="⚙️ Chi tiết phần cứng", color=discord.Color.dark_gray())
        embed.add_field(name="💽 Ổ cứng (Disk)", value=f"Sử dụng: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)", inline=False)
        embed.add_field(name="🌐 Mạng (Network)", value=f"Đã gửi: {net.bytes_sent // (1024**2)}MB | Đã nhận: {net.bytes_recv // (1024**2)}MB", inline=False)
        embed.add_field(name="🔢 Số lõi CPU", value=f"Vật lý: {psutil.cpu_count(logical=False)} | Logic: {psutil.cpu_count(logical=True)}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Lệnh Prefix tương ứng để bạn có thể dùng !status
    @commands.command(name="status")
    async def status_prefix(self, ctx):
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        await ctx.send(f"📊 **Hệ thống:** CPU: {cpu_usage}% | RAM: {ram.percent}%")

async def setup(bot):
    await bot.add_cog(SystemMonitor(bot))
