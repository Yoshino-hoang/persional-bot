import discord
from discord.ext import commands, tasks
import psutil
import platform
import datetime

class SystemMonitor(commands.Cog):
    """
    Cog giám sát tài nguyên hệ thống (CPU, RAM, Disk, Network).
    Hỗ trợ lệnh xem nhanh và có thể mở rộng để cảnh báo nếu quá tải.
    """
    def __init__(self, bot):
        self.bot = bot
        # Lưu thời điểm bot bắt đầu chạy để tính thời gian hoạt động (Uptime)
        self.start_time = datetime.datetime.now()

    @discord.app_commands.command(name="status", description="Kiểm tra trạng thái và tài nguyên hệ thống của máy chủ chạy bot")
    async def status(self, interaction: discord.Interaction):
        """Hiển thị thông tin chi tiết về phần cứng và phần mềm máy chủ."""
        await interaction.response.defer()

        # Lấy thông tin CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Lấy thông tin RAM
        memory = psutil.virtual_memory()
        memory_used = round(memory.used / (1024 ** 3), 2)
        memory_total = round(memory.total / (1024 ** 3), 2)
        memory_percent = memory.percent

        # Lấy thông tin Disk (Ổ cứng)
        disk = psutil.disk_usage('/')
        disk_used = round(disk.used / (1024 ** 3), 2)
        disk_total = round(disk.total / (1024 ** 3), 2)
        disk_percent = disk.percent

        # Tính toán thời gian bot đã chạy (Uptime)
        uptime = datetime.datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        # Tạo Embed hiển thị
        embed = discord.Embed(title="🖥️ Trạng thái Hệ thống", color=discord.Color.green())
        
        # Thông tin hệ điều hành
        embed.add_field(name="Hệ điều hành", value=f"`{platform.system()} {platform.release()}`", inline=False)
        
        # Tài nguyên phần cứng
        embed.add_field(name="CPU Usage", value=f"`{cpu_usage}%` ({cpu_count} Cores)", inline=True)
        embed.add_field(name="RAM Usage", value=f"`{memory_used}GB / {memory_total}GB` ({memory_percent}%)", inline=True)
        embed.add_field(name="Disk Usage", value=f"`{disk_used}GB / {disk_total}GB` ({disk_percent}%)", inline=True)
        
        # Thời gian hoạt động
        embed.add_field(name="Uptime", value=f"`{days}d {hours}h {minutes}m {seconds}s`", inline=False)
        
        # Độ trễ của Bot (Ping)
        embed.add_field(name="Bot Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)

        embed.set_footer(text=f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')}")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SystemMonitor(bot))
