from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import is_check_admin

# ---------------- Manage Button ---------------- #
@Client.on_message(filters.command('manage') & filters.group)
async def members_management(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text('You are not an admin in this group.')

    btn = [
        [InlineKeyboardButton('Kick Deleted Accounts', callback_data='kick_deleted_accounts_members')]
    ]
    await message.reply_text(
        "Select a function to manage members.",
        reply_markup=InlineKeyboardMarkup(btn)
    )

# ---------------- Kick Deleted Accounts ---------------- #
@Client.on_message(filters.command('kickdeleted') & filters.group)
async def kick_deleted_accounts(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text('You are not an admin in this group.')

    members = await client.get_chat_members(message.chat.id)
    kicked_count = 0

    for member in members:
        if member.user.is_deleted:
            try:
                await client.ban_chat_member(message.chat.id, member.user.id)
                await client.unban_chat_member(message.chat.id, member.user.id)
                kicked_count += 1
            except:
                continue

    await message.reply_text(f"✅ Kicked {kicked_count} deleted accounts from {message.chat.title}.")