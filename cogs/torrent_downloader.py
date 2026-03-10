import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import subprocess

class TorrentDownloaderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

    async def run_aria2(self, target, interaction: discord.Interaction):
        """Hàm chạy aria2 ngầm"""
        try:
            # Đường dẫn tới aria2c.exe
            aria2_path = os.path.join(os.getcwd(), 'aria2c.exe')
            download_dir = os.path.join(os.getcwd(), 'downloads')
            
            # Khởi tạo tiến trình
            process = await asyncio.create_subprocess_exec(
                aria2_path,
                '--dir', download_dir,
                '--seed-time=0', # Tải xong là dừng, không seed để đỡ tốn mạng
                target,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            await process.wait()
            
            if process.returncode == 0:
                await interaction.channel.send(f"✅ Đã tải xong Torrent vào thư mục `downloads`!")
            else:
                await interaction.channel.send(f"❌ Có lỗi khi tải. Vui lòng kiểm tra lại link/file.")
        except Exception as e:
            await interaction.channel.send(f"❌ Lỗi hệ thống: {e}")

    @app_commands.command(name="torrent_magnet", description="Tải file torrent bằng link Magnet")
    @app_commands.describe(magnet_link="Dán link magnet của bạn vào đây")
    async def torrent_magnet(self, interaction: discord.Interaction, magnet_link: str):
        if not magnet_link.startswith('magnet:?'):
            await interaction.response.send_message("❌ Link magnet không hợp lệ!", ephemeral=True)
            return

        await interaction.response.send_message(f"🚀 Đang bắt đầu tải torrent. Quá trình chạy ngầm, tôi sẽ báo khi xong!")
        
        # Chạy task ẩn
        asyncio.create_task(self.run_aria2(magnet_link, interaction))

    @app_commands.command(name="torrent_file", description="Tải file torrent bằng cách đính kèm file .torrent")
    async def torrent_file(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.filename.endswith('.torrent'):
            await interaction.response.send_message("❌ Vui lòng đính kèm file có đuôi `.torrent`!", ephemeral=True)
            return

        await interaction.response.send_message(f"🚀 Đã nhận `{file.filename}`. Đang tiến hành tải xuống...")

        temp_path = os.path.join('downloads', file.filename)
        await file.save(temp_path)

        # Chạy task ẩn và truyền đường dẫn file
        asyncio.create_task(self.run_aria2(temp_path, interaction))

async def setup(bot):
    await bot.add_cog(TorrentDownloaderCog(bot))

