import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

# --- Lớp giao diện để điều khiển lật trang ghi chú ---
class NotePagination(discord.ui.View):
    def __init__(self, notes, user_name):
        super().__init__(timeout=60) # Tự động đóng sau 60s không tương tác
        self.notes = notes
        self.user_name = user_name
        self.current_page = 0

    def create_embeds(self):
        """Tạo danh sách các Embed cho ghi chú hiện tại (hỗ trợ hiện tất cả ảnh)"""
        note = self.notes[self.current_page]
        image_urls = note.get('image_urls', [])
        
        # Hỗ trợ định dạng ảnh cũ nếu có
        if not image_urls and note.get('image_url'):
            image_urls = [note['image_url']]

        embeds = []
        # Embed chính chứa tiêu đề và nội dung văn bản
        main_embed = discord.Embed(
            title=f"📝 Ghi chú {self.current_page + 1}/{len(self.notes)} (ID: {note['id']})",
            description=note['content'],
            color=discord.Color.blue(),
            timestamp=datetime.strptime(note['timestamp'].split(" (")[0], "%Y-%m-%d %H:%M:%S")
        )
        main_embed.set_footer(text=f"Sổ tay của {self.user_name}")

        if not image_urls:
            embeds.append(main_embed)
        else:
            # Tạo lưới ảnh bằng cách gửi nhiều embed chung một nhóm
            for i, url in enumerate(image_urls):
                if i == 0:
                    main_embed.set_image(url=url)
                    embeds.append(main_embed)
                else:
                    # Các embed phụ chỉ chứa ảnh để Discord tự gom nhóm
                    extra_embed = discord.Embed(color=discord.Color.blue())
                    extra_embed.set_image(url=url)
                    embeds.append(extra_embed)
        
        return embeds[:10] # Discord giới hạn tối đa 10 embed mỗi tin nhắn

    @discord.ui.button(label="⬅️ Trước", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embeds=self.create_embeds(), view=self)
        else:
            await interaction.response.send_message("Đây là ghi chú đầu tiên rồi!", ephemeral=True)

    @discord.ui.button(label="Sau ➡️", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.notes) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embeds=self.create_embeds(), view=self)
        else:
            await interaction.response.send_message("Đây là ghi chú cuối cùng rồi!", ephemeral=True)

class Notes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'notes.json'
        self.notes = self.load_notes()

    def load_notes(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_notes(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=4)

    note_group = app_commands.Group(name="note", description="Quản lý ghi chú cá nhân")

    @note_group.command(name="add", description="Thêm ghi chú (tối đa 5 ảnh)")
    async def add(self, interaction: discord.Interaction, content: str, 
                  image1: discord.Attachment = None, image2: discord.Attachment = None, 
                  image3: discord.Attachment = None, image4: discord.Attachment = None, 
                  image5: discord.Attachment = None):
        user_id = str(interaction.user.id)
        if user_id not in self.notes: self.notes[user_id] = []
        
        note_id = len(self.notes[user_id]) + 1
        attachments = [image1, image2, image3, image4, image5]
        image_urls = [att.url for att in attachments if att is not None]
        
        new_note = {
            "id": note_id,
            "content": content,
            "image_urls": image_urls,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.notes[user_id].append(new_note)
        self.save_notes()
        await interaction.response.send_message(f"✅ Đã thêm ghi chú ID: {note_id}")

    @note_group.command(name="list", description="Xem sổ tay ghi chú (lật trang để xem tất cả ảnh)")
    async def list(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_notes = self.notes.get(user_id, [])
        
        if not user_notes:
            await interaction.response.send_message("Bạn chưa có ghi chú nào.")
            return

        # Khởi tạo bộ lật trang
        view = NotePagination(user_notes, interaction.user.display_name)
        await interaction.response.send_message(embeds=view.create_embeds(), view=view)

    @note_group.command(name="view", description="Xem nhanh chi tiết 1 ghi chú")
    async def view(self, interaction: discord.Interaction, note_id: int):
        user_id = str(interaction.user.id)
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n['id'] == note_id), None)
        
        if not note:
            await interaction.response.send_message(f"❌ Không tìm thấy ghi chú ID {note_id}.")
            return

        # Tái sử dụng logic hiển thị ảnh chi tiết
        temp_view = NotePagination([note], interaction.user.display_name)
        await interaction.response.send_message(embeds=temp_view.create_embeds())

    @note_group.command(name="edit", description="Sửa ghi chú")
    async def edit(self, interaction: discord.Interaction, note_id: int, 
                   new_content: str = None, 
                   image1: discord.Attachment = None, image2: discord.Attachment = None,
                   image3: discord.Attachment = None, image4: discord.Attachment = None,
                   image5: discord.Attachment = None):
        user_id = str(interaction.user.id)
        user_notes = self.notes.get(user_id, [])
        for note in user_notes:
            if note['id'] == note_id:
                if new_content: note['content'] = new_content
                new_attachments = [image1, image2, image3, image4, image5]
                new_urls = [att.url for att in new_attachments if att is not None]
                if new_urls: note['image_urls'] = new_urls
                self.save_notes()
                await interaction.response.send_message(f"✅ Đã sửa ghi chú {note_id}")
                return
        await interaction.response.send_message(f"❌ Không tìm thấy ghi chú {note_id}")

    @note_group.command(name="delete", description="Xóa ghi chú")
    async def delete(self, interaction: discord.Interaction, note_id: int):
        user_id = str(interaction.user.id)
        if user_id not in self.notes:
            await interaction.response.send_message("Bạn không có ghi chú nào.")
            return
        original_len = len(self.notes[user_id])
        self.notes[user_id] = [n for n in self.notes[user_id] if n['id'] != note_id]
        if len(self.notes[user_id]) < original_len:
            for i, note in enumerate(self.notes[user_id], 1): note['id'] = i
            self.save_notes()
            await interaction.response.send_message(f"✅ Đã xóa ghi chú {note_id}")
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy ghi chú {note_id}")

async def setup(bot):
    await bot.add_cog(Notes(bot))
