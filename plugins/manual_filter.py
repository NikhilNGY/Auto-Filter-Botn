import re
import asyncio
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup
from database.ia_filterdb import filters_col
from info import AUTO_DELETE, ADMINS

# ------------------------------
# Add a manual filter with optional media
# ------------------------------
@Client.on_message(filters.command("addfilter") & filters.group)
async def add_filter(client, message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply_text("❌ You are not authorized to add filters.")

    reply_msg = message.reply_to_message
    try:
        _, keyword, *reply_text = message.text.split(" ")
        reply_text = " ".join(reply_text)
    except ValueError:
        return await message.reply_text(
            "Usage: /addfilter <keyword> <reply_text> (or reply to media with /addfilter <keyword>)"
        )

    file_id = None
    file_type = None

    if reply_msg:
        if reply_msg.photo:
            file_id = reply_msg.photo.file_id
            file_type = "photo"
        elif reply_msg.video:
            file_id = reply_msg.video.file_id
            file_type = "video"
        elif reply_msg.document:
            file_id = reply_msg.document.file_id
            file_type = "document"
        elif reply_msg.sticker:
            file_id = reply_msg.sticker.file_id
            file_type = "sticker"
        elif reply_msg.voice:
            file_id = reply_msg.voice.file_id
            file_type = "voice"
        elif reply_msg.audio:
            file_id = reply_msg.audio.file_id
            file_type = "audio"

    # Save filter in database
    filters_col.insert_one({
        "chat_id": message.chat.id,
        "keyword": keyword.lower(),
        "reply": reply_text,
        "file_id": file_id,
        "file_type": file_type,
        "buttons": None
    })
    await message.reply_text(f"✅ Filter '{keyword}' added successfully!")

# ------------------------------
# Delete a manual filter
# ------------------------------
@Client.on_message(filters.command("delfilter") & filters.group)
async def delete_filter(client, message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply_text("❌ You are not authorized to delete filters.")

    try:
        _, keyword = message.text.split(" ")
    except ValueError:
        return await message.reply_text("Usage: /delfilter <keyword>")

    result = filters_col.delete_one({"chat_id": message.chat.id, "keyword": keyword.lower()})
    if result.deleted_count:
        await message.reply_text(f"✅ Filter '{keyword}' deleted successfully!")
    else:
        await message.reply_text(f"⚠️ No filter found with keyword '{keyword}'.")

# ------------------------------
# List all filters
# ------------------------------
@Client.on_message(filters.command("filters") & filters.group)
async def list_filters(client, message):
    chat_id = message.chat.id
    all_filters = list(filters_col.find({"chat_id": chat_id}))
    if not all_filters:
        return await message.reply_text("No filters set in this group.")

    text = "**Filters in this group:**\n\n"
    for f in all_filters:
        text += f"- {f['keyword']}\n"
    await message.reply_text(text)

# ------------------------------
# Trigger filters with auto-delete support
# ------------------------------
@Client.on_message(filters.text & filters.group)
async def manual_filter_reply(client, message):
    text = message.text.lower()
    chat_id = message.chat.id
    filters_data = list(filters_col.find({"chat_id": chat_id}))

    for data in filters_data:
        pattern = data["keyword"]
        if re.search(pattern, text, re.IGNORECASE):
            reply_markup = InlineKeyboardMarkup(data["buttons"]) if data["buttons"] else None
            sent = None

            # Send reply
            if data["file_id"]:
                if data["file_type"] == "photo":
                    sent = await message.reply_photo(data["file_id"], caption=data["reply"], reply_markup=reply_markup)
                elif data["file_type"] == "video":
                    sent = await message.reply_video(data["file_id"], caption=data["reply"], reply_markup=reply_markup)
                elif data["file_type"] == "document":
                    sent = await message.reply_document(data["file_id"], caption=data["reply"], reply_markup=reply_markup)
                elif data["file_type"] == "sticker":
                    sent = await message.reply_sticker(data["file_id"])
                elif data["file_type"] == "voice":
                    sent = await message.reply_voice(data["file_id"], caption=data["reply"], reply_markup=reply_markup)
                elif data["file_type"] == "audio":
                    sent = await message.reply_audio(data["file_id"], caption=data["reply"], reply_markup=reply_markup)
            else:
                sent = await message.reply_text(data["reply"], reply_markup=reply_markup)

            # Auto delete both user and bot messages
            if AUTO_DELETE:
                try:
                    await asyncio.sleep(DELETE_TIME)
                    await message.delete()
                    if sent:
                        await sent.delete()
                except:
                    pass
            break  # Stop after first match