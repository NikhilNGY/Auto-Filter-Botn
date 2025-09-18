from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import DELETE_CHANNELS, ADMINS, LOG_CHANNEL
import motor.motor_asyncio
import os, time

# MongoDB setup
DATABASE_URL = os.getenv("DATABASE_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "AutoFilter")

client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
db = client[DATABASE_NAME]
files = db["FILES"]

# Cooldown (per admin, in seconds)
DELETE_COOLDOWN = 30  
cooldowns = {}

# Delete function with partial matching
async def delete_files_by_name(query: str) -> int:
    regex = {"$regex": query, "$options": "i"}
    result = await files.delete_many({
        "$or": [
            {"file_name": regex},
            {"caption": regex},
            {"title": regex}
        ]
    })
    return result.deleted_count


# Handle /delete command
@Client.on_message(filters.command("delete") & filters.group)
async def delete_files(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("🚫 You don’t have permission to use this command.")

    # ✅ Cooldown check
    now = time.time()
    last_used = cooldowns.get(message.from_user.id, 0)
    if now - last_used < DELETE_COOLDOWN:
        wait_time = int(DELETE_COOLDOWN - (now - last_used))
        return await message.reply_text(
            f"⏳ Please wait <b>{wait_time} sec</b> before using /delete again."
        )
    cooldowns[message.from_user.id] = now

    try:
        query = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("⚠️ Usage: /delete <query>")

    if message.chat.id not in DELETE_CHANNELS:
        return await message.reply_text("❌ This chat is not in DELETE_CHANNELS list!")

    buttons = [
        [InlineKeyboardButton("✅ YES", callback_data=f"delete_{query}")],
        [InlineKeyboardButton("❌ CANCEL", callback_data=f"cancel_{query}")]
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
        log_msg = (
            f"⚠️ <b>Delete Attempt (No Files Found)</b>\n\n"
            f"👤 Admin: {query.from_user.mention} (`{query.from_user.id}`)\n"
            f"💬 Group: {query.message.chat.title} (`{query.message.chat.id}`)\n"
            f"🔍 Query: <b>{query_text}</b>\n"
            f"📦 Deleted: <b>0</b> files"
        )
    else:
        await query.message.edit(f"✅ Deleted <b>{deleted}</b> files with query: <b>{query_text}</b>")
        log_msg = (
            f"🗑️ <b>Files Deleted</b>\n\n"
            f"👤 Admin: {query.from_user.mention} (`{query.from_user.id}`)\n"
            f"💬 Group: {query.message.chat.title} (`{query.message.chat.id}`)\n"
            f"🔍 Query: <b>{query_text}</b>\n"
            f"📦 Deleted: <b>{deleted}</b> files"
        )

    try:
        await client.send_message(LOG_CHANNEL, log_msg)
    except Exception as e:
        print(f"Failed to log delete action: {e}")


# Handle cancel button
@Client.on_callback_query(filters.regex(r"^cancel_"))
async def cancel_delete(client, query):
    query_text = query.data.split("_", 1)[1]

    await query.message.edit(f"❌ Delete cancelled for query: <b>{query_text}</b>")

    log_msg = (
        f"🚫 <b>Delete Cancelled</b>\n\n"
        f"👤 Admin: {query.from_user.mention} (`{query.from_user.id}`)\n"
        f"💬 Group: {query.message.chat.title} (`{query.message.chat.id}`)\n"
        f"🔍 Query: <b>{query_text}</b>"
    )

    try:
        await client.send_message(LOG_CHANNEL, log_msg)
    except Exception as e:
        print(f"Failed to log cancel action: {e}")