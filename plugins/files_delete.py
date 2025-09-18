from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from settings import DELETE_CHANNELS, ADMINS
from database.db import delete_files_by_name

@Client.on_message(filters.command("delete") & filters.group)
async def delete_files(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("🚫 You don’t have permission to use this command.")

    try:
        query = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("⚠️ Usage: /delete <query>")

    if message.chat.id not in DELETE_CHANNELS:
        return await message.reply_text("❌ This chat is not in DELETE_CHANNELS list!")

    buttons = [
        [InlineKeyboardButton("✅ YES", callback_data=f"delete_{query}")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="close_data")]
    ]
    await message.reply_text(
        f"Do you really want to delete all files with query:\n\n<b>{query}</b> ❓",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
