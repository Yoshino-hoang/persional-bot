import discord # Thư viện chính để tương tác với Discord API
import os # Thư viện để làm việc với hệ điều hành (như đọc biến môi trường)
import asyncio # Thư viện hỗ trợ lập trình bất đồng bộ
from dotenv import load_dotenv # Đọc biến môi trường từ file .env
from discord.ext import commands # Cung cấp framework để tạo lệnh bot dễ dàng hơn

# 1. Tải token và API key từ file .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN") # Token của bot Discord
GG_KEY = os.getenv("GG_API") # API Key của Google
OWNER_ID = 840760431143420014 # THAY THẾ ID CỦA BẠN VÀO ĐÂY (Ví dụ: 123456789012345678)

# 2. Cấu hình Bot (lớp MyBot kế thừa từ commands.Bot)
class MyBot(commands.Bot):
    def __init__(self):
        # Thiết lập quyền hạn (Intents) cho bot
        intents = discord.Intents.default()
        intents.message_content = True # Cho phép bot đọc nội dung tin nhắn của người dùng
        
        super().__init__(
            command_prefix="!", # Tiền tố cho các lệnh cổ điển (ví dụ: !help, !ping)
            intents=intents,
            help_command=None,
            owner_id=OWNER_ID # Thiết lập ID chủ sở hữu thủ công
        )

    # Hàm setup_hook chạy một lần khi bot khởi động để nạp các module (cogs)
    async def setup_hook(self):
        print("--- Đang nạp các module lệnh ---")
        for filename in os.listdir('./cogs'):
            # Bỏ qua file extracmd.py vì nó chỉ chứa code hỗ trợ, không phải Cog
            if filename.endswith('.py') and filename != 'extracmd.py':
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Đã nạp: {filename}')
                except Exception as e:
                    print(f'Lỗi nạp {filename}: {e}')
        
        # Đồng bộ các lệnh gạch chéo (Slash Commands) lên server Discord
        await self.tree.sync()
        print("--- Đã đồng bộ Slash Commands! ---")

    async def on_ready(self):
        print(f'Đã đăng nhập: {self.user} (ID: {self.user.id})')


# Khởi tạo đối tượng bot
bot = MyBot()

# Lệnh !sync để đồng bộ nhanh slash commands vào server hiện tại
@bot.command()
@commands.is_owner()
async def sync(ctx):
    try:
        # Đồng bộ tree vào server (guild) hiện tại để nó xuất hiện ngay lập tức
        fmt = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Đã đồng bộ {len(fmt)} lệnh vào server này!")
    except Exception as e:
        await ctx.send(f"❌ Lỗi đồng bộ: {e}")

# Lệnh !reload dùng để nạp lại các module lệnh mà không cần tắt bot
@bot.command()
@commands.is_owner() # Giới hạn: Chỉ chủ sở hữu bot mới có thể chạy lệnh này
async def reload(ctx, extension):
    try:
        # Nạp lại file (module) tương ứng trong thư mục cogs
        await bot.reload_extension(f'cogs.{extension}')
        
        # Đồng bộ lại Slash Commands sau khi nạp lại module để cập nhật thay đổi
        await bot.tree.sync()
        
        await ctx.send(f'✅ Đã nạp lại và đồng bộ thành công: {extension}.py')
        print(f'--- Đã reload module: {extension} ---')
    except Exception as e:
        await ctx.send(f'❌ Lỗi khi reload: {e}')
        print(f'Lỗi reload: {e}')

# Hàm chính để khởi chạy bot
async def main():
    async with bot:
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())