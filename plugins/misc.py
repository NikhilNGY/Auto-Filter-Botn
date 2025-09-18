from info import ADMINS
from hydrogram import Client, filters, enums
from hydrogram.errors import UserNotParticipant
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from datetime import datetime


# ---------------- /id Command ---------------- #
@Client.on_message(filters.command('id'))
async def showid(client, message):
    chat_type = message.chat.type
    replied_to_msg = message.reply_to_message

    if replied_to_msg:
        if replied_to_msg.forward_from_chat:
            await message.reply_text(
                f"The forwarded message is from channel <b>{replied_to_msg.forward_from_chat.title}</b>\n"
                f"ID: <code>{replied_to_msg.forward_from_chat.id}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"The message is from user <b>{replied_to_msg.from_user.first_name}</b>\n"
                f"ID: <code>{replied_to_msg.from_user.id}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        return

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text(f'★ User ID: <code>{message.from_user.id}</code>', parse_mode=enums.ParseMode.HTML)
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await message.reply_text(f'★ Group ID: <code>{message.chat.id}</code>', parse_mode=enums.ParseMode.HTML)
    elif chat_type == enums.ChatType.CHANNEL:
        await message.reply_text(f'★ Channel ID: <code>{message.chat.id}</code>', parse_mode=enums.ParseMode.HTML)


# ---------------- /info Command ---------------- #
@Client.on_message(filters.command("info"))
async def who_is(client, message):
    status_message = await message.reply_text("Fetching user info... ⏳")

    # Determine user
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        user_id = message.command[1]
    else:
        user_id = message.from_user.id

    try:
        user = await client.get_users(user_id)
    except Exception as e:
        await status_message.edit(f"❌ Error: {e}")
        return

    username = f"@{user.username}" if user.username else "Not available"
    last_name = user.last_name or "Not available"
    dc_id = getattr(user, 'dc_id', 'Unknown')

    info_text = (
        f"<b>➲ First Name:</b> {user.first_name}\n"
        f"<b>➲ Last Name:</b> {last_name}\n"
        f"<b>➲ Telegram ID:</b> <code>{user.id}</code>\n"
        f"<b>➲ Username:</b> {username}\n"
        f"<b>➲ Data Centre:</b> <code>{dc_id}</code>\n"
        f"<b>➲ Last Online:</b> {last_online(user)}\n"
        f"<b>➲ User Link:</b> <a href='tg://user?id={user.id}'>Click Here</a>\n"
    )

    # Chat join date (if applicable)
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            member = await message.chat.get_member(user.id)
            if member.joined_date:
                info_text += f"<b>➲ Joined This Chat:</b> <code>{member.joined_date.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
        except UserNotParticipant:
            pass

    # Send photo if available
    if getattr(user, 'photo', None):
        local_photo = await client.download_media(user.photo.big_file_id)
        await message.reply_photo(photo=local_photo, caption=info_text, parse_mode=enums.ParseMode.HTML)
        os.remove(local_photo)
    else:
        await message.reply_text(info_text, parse_mode=enums.ParseMode.HTML)

    await status_message.delete()


def last_online(user):
    if getattr(user, 'is_bot', False):
        return "🤖 Bot"

    status = getattr(user, 'status', None)
    if status == enums.UserStatus.ONLINE:
        return "Currently Online"
    elif status == enums.UserStatus.RECENTLY:
        return "Recently"
    elif status == enums.UserStatus.LAST_WEEK:
        return "Within Last Week"
    elif status == enums.UserStatus.LAST_MONTH:
        return "Within Last Month"
    elif status == enums.UserStatus.LONG_AGO:
        return "A long time ago"
    elif status == enums.UserStatus.OFFLINE:
        last_seen = getattr(user, 'last_online_date', None)
        return last_seen.strftime("%a, %d %b %Y, %H:%M:%S") if last_seen else "Offline"
    return "Unknown"