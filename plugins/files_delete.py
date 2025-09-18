from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import DELETE_CHANNELS, ADMINS
import motor.motor_asyncio
import os

# MongoDB setup
DATABASE_URL = os.getenv("DATABASE_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "AutoFilter")

client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
db = client[DATABASE_NAME]
files = db["FILES"]

# Delete function inside this file
async def delete_files_by_name(query: str) -> int:
    """
    Delete all files from MongoDB where file_name matches the query.
    Returns number of deleted documents.
    """
    result = await files.delete_many({"file_name": {"$regex": query, "$options": "i"}})
    return result.deleted_count


# Handle /delete command
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


# Handle confirmation button
@Client.on_callback_query(filters.regex(r"^delete_"))
async def confirm_delete(client, query):
    query_text = query.data.split("_", 1)[1]

    if query.message.chat.id not in DELETE_CHANNELS:
        return await query.answer("❌ Not allowed in this chat!", show_alert=True)

    deleted = await delete_files_by_name(query_text)

    if deleted == 0:
        await query.message.edit(f"⚠️ No files found for query: <b>{query_text}</b>")
    else:
        await query.message.edit(f"✅ Deleted <b>{deleted}</b> files with query: <b>{query_text}</b>")