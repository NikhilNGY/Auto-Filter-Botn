from hydrogram import Client, filters
from utils import temp
from hydrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from database.users_chats_db import db
from info import SUPPORT_LINK

# -------------------------
# Filter for banned users
# -------------------------
async def banned_users_filter(_, __, message: Message):
    """Returns True if the user is banned."""
    return message.from_user and not message.sender_chat and message.from_user.id in temp.BANNED_USERS

banned_user = filters.create(banned_users_filter)

# -------------------------
# Filter for disabled chats
# -------------------------
async def disabled_chat_filter(_, __, message: Message):
    """Returns True if chat is disabled."""
    return message.chat.id in temp.BANNED_CHATS

disabled_group = filters.create(disabled_chat_filter)

# -------------------------
# Private message: banned user
# -------------------------
@Client.on_message(filters.private & banned_user & filters.incoming)
async def is_user_banned(bot, message: Message):
    buttons = [[InlineKeyboardButton('Support Group', url=SUPPORT_LINK)]]
    reply_markup = InlineKeyboardMarkup(buttons)

    ban_info = await db.get_ban_status(message.from_user.id)
    reason = ban_info.get("ban_reason", "No reason provided")

    await message.reply(
        f"Sorry {message.from_user.mention},\n"
        f"My owner has banned you from using me! Contact support for more info.\n"
        f"Reason - <code>{reason}</code>",
        reply_markup=reply_markup
    )

# -------------------------
# Group message: disabled chat
# -------------------------
@Client.on_message(filters.group & disabled_group & filters.incoming)
async def is_group_disabled(bot, message: Message):
    buttons = [[InlineKeyboardButton('Support Group', url=SUPPORT_LINK)]]
    reply_markup = InlineKeyboardMarkup(buttons)

    chat_info = await db.get_chat(message.chat.id)
    reason = chat_info.get("reason", "No reason provided")

    warning_msg = await message.reply(
        text=f"<b><u>Chat Not Allowed</u></b>\n\n"
             f"My owner has restricted me from working here! Contact support for more info.\n"
             f"Reason - <code>{reason}</code>",
        reply_markup=reply_markup
    )

    # Try to pin the warning message
    try:
        await warning_msg.pin()
    except:
        pass

    # Leave the disabled group
    try:
        await bot.leave_chat(message.chat.id)
    except:
        pass
