import random
import os
import sys
from hydrogram import Client, filters, enums
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from hydrogram.errors.exceptions.bad_request_400 import MessageTooLong
from info import ADMINS, LOG_CHANNEL, PICS, SUPPORT_LINK, UPDATES_LINK
from database.users_chats_db import db
from utils import temp, get_settings
from Script import script

# ---------------- Welcome / Bot Added ---------------- #
@Client.on_chat_member_updated()
async def welcome(bot, message):
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return

    if message.new_chat_member and not message.old_chat_member:
        # Bot added
        if message.new_chat_member.user.id == temp.ME:
            buttons = [[
                InlineKeyboardButton('ᴜᴘᴅᴀᴛᴇ', url=UPDATES_LINK),
                InlineKeyboardButton('ꜱᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
            ]]
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=random.choice(PICS),
                caption=f"👋 Hello {message.from_user.mention if message.from_user else 'Dear'},\n"
                        f"Thanks for adding me to <b>{message.chat.title}</b>.\nMake me admin for full functionality 😘",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            if not await db.get_chat(message.chat.id):
                total = await bot.get_chat_members_count(message.chat.id)
                username = f'@{message.chat.username}' if message.chat.username else 'Private'
                await bot.send_message(LOG_CHANNEL, script.NEW_GROUP_TXT.format(
                    message.chat.title, message.chat.id, username, total
                ))
                await db.add_chat(message.chat.id, message.chat.title)
            return

        # Normal user welcome
        settings = await get_settings(message.chat.id)
        if settings.get("welcome"):
            welcome_msg = settings.get("welcome_text", "Welcome {mention}!").format(
                mention=message.new_chat_member.user.mention,
                title=message.chat.title
            )
            await bot.send_message(message.chat.id, welcome_msg)

# ---------------- Admin Commands ---------------- #
@Client.on_message(filters.command('restart') & filters.user(ADMINS))
async def restart_bot(bot, message):
    msg = await message.reply("Restarting...")
    with open('restart.txt', 'w+') as f:
        f.write(f"{msg.chat.id}\n{msg.id}")
    os.execl(sys.executable, sys.executable, "bot.py")


@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_group(bot, message):
    if len(message.command) < 2:
        return await message.reply("Provide chat ID.")
    chat_id = message.command[1]
    reason = "No reason provided." if len(message.command) < 3 else " ".join(message.command[2:])
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass

    try:
        await bot.send_message(chat_id, f"Leaving group. Reason: <code>{reason}</code>",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", url=SUPPORT_LINK)]]))
        await bot.leave_chat(chat_id)
        await message.reply(f"✅ Left group `{chat_id}` successfully")
    except Exception as e:
        await message.reply(f"Error: {e}")


@Client.on_message(filters.command(['ban_grp', 'disable_chat']) & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("Provide chat ID.")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply("Provide a valid chat ID.")

    reason = "No reason provided." if len(message.command) < 3 else " ".join(message.command[2:])
    chat_data = await db.get_chat(chat_id)
    if not chat_data:
        return await message.reply("Chat not found in database.")
    if chat_data.get("is_disabled"):
        return await message.reply(f"Chat already disabled. Reason: <code>{chat_data['reason']}</code>")

    await db.disable_chat(chat_id, reason)
    temp.BANNED_CHATS.append(chat_id)
    await message.reply("Chat successfully disabled.")

    try:
        await bot.send_message(chat_id, f"My owner told me to leave this group. Reason: <code>{reason}</code>",
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", url=SUPPORT_LINK)]]))
        await bot.leave_chat(chat_id)
    except Exception as e:
        await message.reply(f"Error: {e}")


@Client.on_message(filters.command('unban_grp') & filters.user(ADMINS))
async def enable_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("Provide chat ID.")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply("Provide a valid chat ID.")

    chat_data = await db.get_chat(chat_id)
    if not chat_data:
        return await message.reply("Chat not found in database.")
    if not chat_data.get("is_disabled"):
        return await message.reply("This chat is not disabled.")

    await db.re_enable_chat(chat_id)
    if chat_id in temp.BANNED_CHATS:
        temp.BANNED_CHATS.remove(chat_id)
    await message.reply("Chat successfully re-enabled.")


@Client.on_message(filters.command('invite_link') & filters.user(ADMINS))
async def gen_invite_link(bot, message):
    if len(message.command) < 2:
        return await message.reply("Provide chat ID.")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply("Provide a valid chat ID.")

    try:
        link = await bot.create_chat_invite_link(chat_id)
        await message.reply(f"Invite link: {link.invite_link}")
    except Exception as e:
        await message.reply(f"Error: {e}")


# ---------------- List Users / Chats ---------------- #
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    raju = await message.reply("Fetching users...")
    users = await db.get_all_users()
    out = "Users in database:\n\n"
    for user in users:
        out += f"**Name:** {user['name']}\n**ID:** `{user['id']}`"
        if user['verify_status'].get("is_verified"):
            out += " (Verified)"
        out += "\n\n"
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open("users.txt", "w+", encoding="utf-8") as f:
            f.write(out)
        await message.reply_document("users.txt", caption="Users list")
        await raju.delete()
        os.remove("users.txt")


@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    raju = await message.reply("Fetching chats...")
    chats = await db.get_all_chats()
    out = "Chats in database:\n\n"
    for chat in chats:
        out += f"**Title:** {chat['title']}\n**ID:** `{chat['id']}`"
        if chat['chat_status'].get("is_disabled"):
            out += " (Disabled)"
        out += "\n\n"
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open("chats.txt", "w+", encoding="utf-8") as f:
            f.write(out)
        await message.reply_document("chats.txt", caption="Chats list")
        await raju.delete()
        os.remove("chats.txt")


# ---------------- Join Requests ---------------- #
@Client.on_chat_join_request()
async def join_requests(client, message: ChatJoinRequest):
    stg = await db.get_bot_sttgs()
    if message.chat.id == int(stg.get("REQUEST_FORCE_SUB_CHANNELS", 0)):
        if not await db.find_join_req(message.from_user.id):
            await db.add_join_req(message.from_user.id)


@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def delete_join_requests(client, message):
    await db.del_join_req()
    await message.reply("Deleted all join requests.")