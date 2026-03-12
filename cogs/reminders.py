import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import re
from datetime import datetime, timedelta

class Reminders(commands.Cog):
    """
    Cog quản lý nhắc nhở, trả lời trực tiếp công khai trong kênh chạy lệnh.
    """
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'reminders.json'
        self.reminders = self.load_reminders()
        self.check_reminders.start()

    def load_reminders(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_reminders(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.reminders, f, ensure_ascii=False, indent=4)

    def parse_time(self, time_str):
        total_seconds = 0
        patterns = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
        matches = re.findall(r'(\d+)([dhms])', time_str.lower())
        if not matches: return None
        for amount, unit in matches:
            total_seconds += int(amount) * patterns[unit]
        return total_seconds

    remind_group = app_commands.Group(name="remind", description="Quản lý nhắc nhở")

    @remind_group.command(name="set", description="Hẹn giờ nhắc nhở")
    async def set_remind(self, interaction: discord.Interaction, time: str, content: str):
        seconds = self.parse_time(time)
        if seconds is None or seconds <= 0:
            await interaction.response.send_message("❌ Sai định dạng thời gian!", ephemeral=False)
            return

        remind_time = datetime.now() + timedelta(seconds=seconds)
        remind_id = len(self.reminders) + 1
        
        new_remind = {
            "id": remind_id,
            "user_id": interaction.user.id,
            "channel_id": interaction.channel_id,
            "content": content,
            "remind_at": remind_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.reminders.append(new_remind)
        self.save_reminders()
        
        await interaction.response.send_message(f"🔔 **{interaction.user.display_name}** đã đặt nhắc nhở ID {remind_id} sau `{time}`.", ephemeral=False)

    @remind_group.command(name="list", description="Xem nhắc nhở đang chờ")
    async def list_remind(self, interaction: discord.Interaction):
        user_reminders = [r for r in self.reminders if r['user_id'] == interaction.user.id]
        if not user_reminders:
            await interaction.response.send_message("Bạn không có nhắc nhở nào.", ephemeral=False)
            return

        embed = discord.Embed(title=f"🔔 Nhắc nhở của {interaction.user.display_name}", color=discord.Color.gold())
        for r in user_reminders:
            embed.add_field(name=f"ID: {r['id']} | Lúc: {r['remind_at']}", value=r['content'], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @remind_group.command(name="cancel", description="Hủy nhắc nhở")
    async def cancel_remind(self, interaction: discord.Interaction, remind_id: int):
        original_len = len(self.reminders)
        self.reminders = [r for r in self.reminders if not (r['id'] == remind_id and r['user_id'] == interaction.user.id)]
        if len(self.reminders) < original_len:
            self.save_reminders()
            await interaction.response.send_message(f"✅ Đã hủy nhắc nhở ID {remind_id}.", ephemeral=False)
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy nhắc nhở ID {remind_id}.", ephemeral=False)

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.now()
        reminded_indices = []
        for i, r in enumerate(self.reminders):
            remind_at = datetime.strptime(r['remind_at'], "%Y-%m-%d %H:%M:%S")
            if now >= remind_at:
                channel = self.bot.get_channel(r['channel_id'])
                if channel:
                    await channel.send(f"🔔 **NHẮC NHỞ:** <@{r['user_id']}>, đã đến lúc: `{r['content']}`")
                reminded_indices.append(i)
        if reminded_indices:
            self.reminders = [r for i, r in enumerate(self.reminders) if i not in reminded_indices]
            self.save_reminders()

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminders(bot))
