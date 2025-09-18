from hydrogram import Client, filters
from hydrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from utils import is_check_admin

# ---------------- Manage Button ---------------- #
@Client.on_message(filters.command('manage') & filters.group)
async def members_management(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text('You are not admin in this group.')
    
    btn = [
        [InlineKeyboardButton('Unmute All', callback_data='unmute_all_members'),
         InlineKeyboardButton('Unban All', callback_data='unban_all_members')],
        [InlineKeyboardButton('Kick Muted Users', callback_data='kick_muted_members'),
         InlineKeyboardButton('Kick Deleted Accounts', callback_data='kick_deleted_accounts_members')]
    ]
    await message.reply_text(
        "Select one of the functions to manage members.",
        reply_markup=InlineKeyboardMarkup(btn)
    )

# ---------------- Ban Command ---------------- #
@Client.on_message(filters.command('ban') & filters.group)
async def ban_chat_user(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text('You are not admin in this group.')

    # Get target user
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply_text("Reply to a user or provide user ID/username.")
    
    try:
        user_id = int(user_id)
    except ValueError:
        pass

    try:
        user = (await client.get_chat_member(message.chat.id, user_id)).user
    except:
        return await message.reply_text("Cannot find this user in the group.")

    try:
        await client.ban_chat_member(message.chat.id, user_id)
    except:
        return await message.reply_text("I don't have permission to ban this user.")

    await message.reply_text(f'Successfully banned {user.mention} from {message.chat.title}.')

# ---------------- Mute Command ---------------- #
@Client.on_message(filters.command('mute') & filters.group)
async def mute_chat_user(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text('You are not admin in this group.')

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply_text("Reply to a user or provide user ID/username.")

    try:
        user_id = int(user_id)
    except ValueError:
        pass

    try:
        user = (await client.get_chat_member(message.chat.id, user_id)).user
    except:
        return await message.reply_text("Cannot find this user in the group.")

    try:
        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
    except:
        return await message.reply_text("I don't have permission to mute this user.")

    await message.reply_text(f'Successfully muted {user.mention} in {message.chat.title}.')

# ---------------- Unban / Unmute ---------------- #
@Client.on_message(filters.command(["unban", "unmute"]) & filters.group)
async def unban_chat_user(client, message):
    if not await is_check_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text('You are not admin in this group.')

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
        except IndexError:
            return await message.reply_text("Reply to a user or provide user ID/username.")

    try:
        user_id = int(user_id)
    except ValueError:
        pass

    try:
        user = (await client.get_chat_member(message.chat.id, user_id)).user
    except:
        return await message.reply_text("Cannot find this user in the group.")

    try:
        await client.unban_chat_member(message.chat.id, user_id)
    except:
        return await message.reply_text(f"I don't have permission to {message.command[0]} this user.")

    await message.reply_text(f'Successfully {message.command[0]} {user.mention} in {message.chat.title}.')