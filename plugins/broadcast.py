from hydrogram import Client, filters
import time
import asyncio
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.users_chats_db import db
from info import ADMINS
from utils import broadcast_messages, groups_broadcast_messages, temp, get_readable_time

# -------------------------
# Lock to prevent simultaneous broadcasts
# -------------------------
lock = asyncio.Lock()

# -------------------------
# Callback to cancel broadcasting
# -------------------------
@Client.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    _, ident = query.data.split("#")
    if ident == 'users':
        temp.USERS_CANCEL = True
        await query.message.edit("Trying to cancel users broadcasting...")
    elif ident == 'groups':
        temp.GROUPS_CANCEL = True
        await query.message.edit("Trying to cancel groups broadcasting...")

# -------------------------
# Broadcast messages to users
# -------------------------
@Client.on_message(filters.command(["broadcast", "pin_broadcast"]) & filters.user(ADMINS) & filters.reply)
async def users_broadcast(bot, message):
    if lock.locked():
        return await message.reply('Currently processing a broadcast, please wait...')
    
    pin = message.command[0] == 'pin_broadcast'
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    b_status = await message.reply_text('Broadcasting message to users...')
    start_time = time.time()
    total_users = await db.total_users_count()
    done = success = failed = 0

    async with lock:
        for user in users:
            elapsed_time = get_readable_time(time.time() - start_time)
            if temp.USERS_CANCEL:
                temp.USERS_CANCEL = False
                await b_status.edit(
                    f"Users broadcast cancelled!\nCompleted in {elapsed_time}\n\n"
                    f"Total Users: <code>{total_users}</code>\nCompleted: <code>{done}/{total_users}</code>\n"
                    f"Success: <code>{success}</code>"
                )
                return

            sts = await broadcast_messages(int(user['id']), b_msg, pin)
            if sts == 'Success':
                success += 1
            elif sts == 'Error':
                failed += 1
            done += 1

            if done % 20 == 0:
                btn = [[InlineKeyboardButton('CANCEL', callback_data='broadcast_cancel#users')]]
                await b_status.edit(
                    f"Users broadcast in progress...\n\n"
                    f"Total Users: <code>{total_users}</code>\nCompleted: <code>{done}/{total_users}</code>\n"
                    f"Success: <code>{success}</code>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        await b_status.edit(
            f"Users broadcast completed!\nCompleted in {elapsed_time}\n\n"
            f"Total Users: <code>{total_users}</code>\nCompleted: <code>{done}/{total_users}</code>\n"
            f"Success: <code>{success}</code>"
        )

# -------------------------
# Broadcast messages to groups
# -------------------------
@Client.on_message(filters.command(["grp_broadcast", "pin_grp_broadcast"]) & filters.user(ADMINS) & filters.reply)
async def groups_broadcast(bot, message):
    if lock.locked():
        return await message.reply('Currently processing a broadcast, please wait...')
    
    pin = message.command[0] == 'pin_grp_broadcast'
    chats = await db.get_all_chats()
    b_msg = message.reply_to_message
    b_status = await message.reply_text('Broadcasting message to groups...')
    start_time = time.time()
    total_chats = await db.total_chat_count()
    done = success = failed = 0

    async with lock:
        for chat in chats:
            elapsed_time = get_readable_time(time.time() - start_time)
            if temp.GROUPS_CANCEL:
                temp.GROUPS_CANCEL = False
                await b_status.edit(
                    f"Groups broadcast cancelled!\nCompleted in {elapsed_time}\n\n"
                    f"Total Groups: <code>{total_chats}</code>\nCompleted: <code>{done}/{total_chats}</code>\n"
                    f"Success: <code>{success}</code>\nFailed: <code>{failed}</code>"
                )
                return

            sts = await groups_broadcast_messages(int(chat['id']), b_msg, pin)
            if sts == 'Success':
                success += 1
            elif sts == 'Error':
                failed += 1
            done += 1

            if done % 20 == 0:
                btn = [[InlineKeyboardButton('CANCEL', callback_data='broadcast_cancel#groups')]]
                await b_status.edit(
                    f"Groups broadcast in progress...\n\n"
                    f"Total Groups: <code>{total_chats}</code>\nCompleted: <code>{done}/{total_chats}</code>\n"
                    f"Success: <code>{success}</code>\nFailed: <code>{failed}</code>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )

        await b_status.edit(
            f"Groups broadcast completed!\nCompleted in {elapsed_time}\n\n"
            f"Total Groups: <code>{total_chats}</code>\nCompleted: <code>{done}/{total_chats}</code>\n"
            f"Success: <code>{success}</code>\nFailed: <code>{failed}</code>"
        )