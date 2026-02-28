import discord
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import commands # Sửa lại chỗ này

# 1. Load token
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. Cấu hình Bot lớp kế thừa từ commands.Bot
class MyBot(commands.Bot):
    def __init__(self):
        # Thiết lập quyền hạn (Intents)
        intents = discord.Intents.default()
        intents.message_content = True # Cho phép đọc nội dung tin nhắn
        
        super().__init__(
            command_prefix="!", # Tiền tố cho lệnh chat (nếu bạn vẫn muốn dùng)
            intents=intents,
            help_command=None
        )

    # Hàm chạy khi bot khởi động để nạp các file trong thư mục cogs
    async def setup_hook(self):
        print("--- Đang nạp các module lệnh ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Đã nạp: {filename}')
                except Exception as e:
                    print(f'Lỗi nạp {filename}: {e}')
        
        # Đồng bộ Slash Commands với Discord
        await self.tree.sync()
        print("--- Đã đồng bộ Slash Commands! ---")

    async def on_ready(self):
        print(f'Đã đăng nhập: {self.user} (ID: {self.user.id})')

# 3. Chạy Bot
bot = MyBot()

async def main():
    async with bot:
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())