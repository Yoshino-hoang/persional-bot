import discord
from discord import Interaction, app_commands
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Đây là cách tạo Slash Command đúng chuẩn
    @app_commands.command(name="hello", description="Chào hỏi bot")
    async def hello(self, interaction: discord.Interaction):
        # Sử dụng f-string và interaction.user để lấy tên người dùng
        await interaction.response.send_message(f"Chào {interaction.user.mention}")


    # Nếu bạn vẫn muốn dùng lệnh kiểu cũ (!hello)
    @commands.command(name="hi")
    async def hi_prefix(self, ctx):
        await ctx.send(f"Chào {ctx.author.name}")

    

async def setup(bot):
    await bot.add_cog(General(bot))