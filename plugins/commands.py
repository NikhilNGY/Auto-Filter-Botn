import os
import random
import string
import asyncio
from time import time as time_now
from datetime import datetime, timedelta
from Script import script
from hydrogram import Client, filters, enums
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import db_count_documents, get_file_details
from database.users_chats_db import db
from info import (
    STICKERS, INDEX_CHANNELS, ADMINS, IS_VERIFY, VERIFY_TUTORIAL, VERIFY_EXPIRE,
    SHORTLINK_API, SHORTLINK_URL, DELETE_TIME, SUPPORT_LINK, UPDATES_LINK,
    LOG_CHANNEL, PICS, REACTIONS, PM_FILE_DELETE_TIME
)
from utils import (
    get_settings, get_size, is_subscribed, is_check_admin,
    get_shortlink, get_verify_status, update_verify_status,
    temp, get_readable_time, get_wish
)


# ------------------------------
# Delete sticker after delay
# ------------------------------
async def del_stk(sticker_msg):
    await asyncio.sleep(3)
    await sticker_msg.delete()


# ------------------------------
# /start command
# ------------------------------
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    chat_type = message.chat.type
    user = message.from_user.mention if message.from_user else "Dear"
    wish = get_wish()

    # ------------------------------
    # Group start
    # ------------------------------
    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            username = f"@{message.chat.username}" if message.chat.username else "Private"
            await client.send_message(
                LOG_CHANNEL,
                script.NEW_GROUP_TXT.format(message.chat.title, message.chat.id, username, total)
            )
            await db.add_chat(message.chat.id, message.chat.title)

        btn = [[
            InlineKeyboardButton("⚡️ Updates Channel ⚡️", url=UPDATES_LINK),
            InlineKeyboardButton("💡 Support Group 💡", url=SUPPORT_LINK)
        ]]
        return await message.reply(
            text=f"<b>Hey {user}, <i>{wish}</i>\nHow can I help you?</b>",
            reply_markup=InlineKeyboardMarkup(btn)
        )

    # ------------------------------
    # Private start
    # ------------------------------
    # React with random emoji
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        await message.react(emoji="⚡️", big=True)

    # Fun sticker
    d = await client.send_sticker(message.chat.id, random.choice(STICKERS))
    asyncio.create_task(del_stk(d))

    # Register user
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(
            LOG_CHANNEL,
            script.NEW_USER_TXT.format(message.from_user.mention, message.from_user.id)
        )

    # Verify expiration
    verify_status = await get_verify_status(message.from_user.id)
    if verify_status["is_verified"] and datetime.now() > verify_status["expire_time"]:
        await update_verify_status(message.from_user.id, is_verified=False)

    # /start without params
    if len(message.command) == 1 or message.command[1] == "start":
        buttons = [
            [InlineKeyboardButton('Back Channel', url='https://t.me/+pCz5eoun5Zk5YzRl')],
            [
                InlineKeyboardButton('Main Group', url="https://t.me/Sandalwood_Kannada_Group"),
                InlineKeyboardButton('Main Channel', url="https://t.me/KR_PICTURE")
            ]
        ]
        return await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(user, wish),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    # /start with params
    mc = message.command[1]

    # Settings param
    if mc.startswith("settings"):
        _, group_id = mc.split("_")
        if not await is_check_admin(client, int(group_id), message.from_user.id):
            return await message.reply("You are not admin in this group.")
        btn = await get_grp_stg(int(group_id))
        chat = await client.get_chat(int(group_id))
        return await message.reply(
            f"Change settings for <b>'{chat.title}'</b> ⚙",
            reply_markup=InlineKeyboardMarkup(btn)
        )

    # Inline force-subscribe param
    if mc.startswith("inline_fsub"):
        btn = await is_subscribed(client, message)
        if btn:
            return await message.reply(
                "Please join my 'Updates Channel' and use inline search.",
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )

    # Verify param
    if mc.startswith("verify"):
        _, token = mc.split("_", 1)
        if verify_status["verify_token"] != token:
            return await message.reply("Your verify token is invalid.")

        expiry_time = datetime.now() + timedelta(seconds=VERIFY_EXPIRE)
        await update_verify_status(message.from_user.id, is_verified=True, expire_time=expiry_time)

        reply_markup = None
        if verify_status["link"]:
            btn = [[InlineKeyboardButton("📌 Get File 📌", url=f"https://t.me/{temp.U_NAME}?start={verify_status['link']}")]]
            reply_markup = InlineKeyboardMarkup(btn)

        return await message.reply(
            f"✅ Verified until: {get_readable_time(VERIFY_EXPIRE)}",
            reply_markup=reply_markup,
            protect_content=True
        )

    # Verify check
    if IS_VERIFY and not verify_status["is_verified"]:
        token = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        await update_verify_status(message.from_user.id, verify_token=token, link=mc)
        link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f"https://t.me/{temp.U_NAME}?start=verify_{token}")
        btn = [
            [InlineKeyboardButton("🧿 Verify 🧿", url=link)],
            [InlineKeyboardButton("🗳 Tutorial 🗳", url=VERIFY_TUTORIAL)]
        ]
        return await message.reply(
            "You are not verified! Kindly verify now.",
            reply_markup=InlineKeyboardMarkup(btn),
            protect_content=True
        )

    # Force-subscribe check
    btn = await is_subscribed(client, message)
    if btn:
        btn.append([InlineKeyboardButton("🔁 Try Again 🔁", callback_data=f"checksub#{mc}")])
        return await message.reply_photo(
            photo=random.choice(PICS),
            caption=f"Namaskara {user} 🙏\nJoin channel to receive the file.",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------
# Handle single file
# ------------------------------
async def handle_file(client, message, mc):
    type_, grp_id, file_id = mc.split("_", 2)
    file = await get_file_details(file_id)
    if not file:
        return await message.reply("No such file exists!")

    settings = await get_settings(int(grp_id))

    # Shortlink
    if type_ != "shortlink" and settings["shortlink"]:
        link = await get_shortlink(settings["url"], settings["api"], f"https://t.me/{temp.U_NAME}?start=shortlink_{grp_id}_{file_id}")
        btn = [
            [InlineKeyboardButton("♻️ Get File ♻️", url=link)],
            [InlineKeyboardButton("📍 How to Open Link 📍", url=settings["tutorial"])]
        ]
        return await message.reply(
            f"[{get_size(file['file_size'])}] {file['file_name']}\n\nYour file is ready.",
            reply_markup=InlineKeyboardMarkup(btn),
            protect_content=True
        )

    # Caption + buttons
    CAPTION = settings["caption"].format(
        file_name=file["file_name"],
        file_size=get_size(file["file_size"]),
        file_caption=file["caption"]
    )
    btn = [
        [
            InlineKeyboardButton("⚡️ Updates", url=UPDATES_LINK),
            InlineKeyboardButton("💡 Support", url=SUPPORT_LINK)
        ],
        [
            InlineKeyboardButton("⁉️ Close ⁉️", callback_data="close_data")
        ]
    ]
    vp = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=CAPTION,
        protect_content=False,
        reply_markup=InlineKeyboardMarkup(btn)
    )

    msg = await vp.reply(f"⚠️ This file will auto-delete in {get_readable_time(PM_FILE_DELETE_TIME)}.")
    await asyncio.sleep(PM_FILE_DELETE_TIME)
    await msg.delete()
    await vp.delete()
    return await vp.reply(
        "File deleted! Click below to get it again.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Get File Again", callback_data=f"get_del_file#{grp_id}#{file_id}")]])
    )


# ------------------------------
# Index Channels Command
# ------------------------------
@Client.on_message(filters.command("index_channels"))
async def channels_info(bot, message):
    if message.from_user.id not in ADMINS:
        return await message.delete()
    if not INDEX_CHANNELS:
        return await message.reply("⚠️ INDEX_CHANNELS not set!")

    text = "**📂 Indexed Channels:**\n\n"
    for cid in INDEX_CHANNELS:
        try:
            chat = await bot.get_chat(cid)
            text += f"✅ {chat.title} (`{cid}`)\n"
        except Exception as e:
            text += f"⚠️ Failed to fetch `{cid}` ({e})\n"

    text += f"\n**Total:** {len(INDEX_CHANNELS)}"
    await message.reply(text)


# ------------------------------
# Stats Command
# ------------------------------
@Client.on_message(filters.command("stats"))
async def stats(bot, message):
    if message.from_user.id not in ADMINS:
        return await message.delete()

    files = db_count_documents()
    users = await db.total_users_count()
    chats = await db.total_chat_count()
    used_files_db_size = get_size(await db.get_files_db_size())
    used_data_db_size = get_size(await db.get_data_db_size())
    uptime = get_readable_time(time_now() - temp.START_TIME)

    await message.reply_text(
        script.STATUS_TXT.format(
            users, "-", chats,
            used_data_db_size, files, used_files_db_size,
            "-", "-", uptime
        )
    )


# ------------------------------
# Group Settings Buttons
# ------------------------------
async def get_grp_stg(group_id: int):
    settings = await get_settings(group_id)
    btn = [
        [InlineKeyboardButton("📝 Edit IMDb Template", callback_data=f"imdb_setgs#{group_id}")],
        [InlineKeyboardButton("🔗 Edit Shortlink", callback_data=f"shortlink_setgs#{group_id}")],
        [InlineKeyboardButton("🖊 Edit File Caption", callback_data=f"caption_setgs#{group_id}")],
        [InlineKeyboardButton("👋 Edit Welcome", callback_data=f"welcome_setgs#{group_id}")],
        [InlineKeyboardButton(f"Spelling Check {'✅' if settings['spell_check'] else '❌'}", callback_data=f"bool_setgs#spell_check#{settings['spell_check']}#{group_id}")],
        [InlineKeyboardButton(f"Auto Delete - {get_readable_time(DELETE_TIME)}" if settings["auto_delete"] else "Auto Delete ❌", callback_data=f"bool_setgs#auto_delete#{settings['auto_delete']}#{group_id}")]
    ]
    return btn

# ------------------------------
# /settings command
# ------------------------------
@Client.on_message(filters.command('settings'))
async def settings(client, message):
    group_id = message.chat.id
    chat_type = message.chat.type

    # Group settings
    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not await is_check_admin(client, group_id, message.from_user.id):
            return await message.reply_text('⚠️ You are not an admin in this group.')
        btn = [
            [InlineKeyboardButton("Open Here", callback_data='open_group_settings')],
            [InlineKeyboardButton("Open In PM", callback_data='open_pm_settings')]
        ]
        await message.reply_text(
            'Where do you want to open the settings menu?',
            reply_markup=InlineKeyboardMarkup(btn)
        )

    # Private PM settings
    elif chat_type == enums.ChatType.PRIVATE:
        cons = db.get_connections(message.from_user.id)
        if not cons:
            return await message.reply_text("❌ No groups found!\n\nUse /settings in a group first.")
        buttons = []
        for con in cons:
            try:
                chat = await client.get_chat(con)
                buttons.append([InlineKeyboardButton(chat.title, callback_data=f'back_setgs#{chat.id}')])
            except:
                continue
        await message.reply_text(
            'Select the group to change settings:',
            reply_markup=InlineKeyboardMarkup(buttons)
        )


# ------------------------------
# /connect command
# ------------------------------
@Client.on_message(filters.command('connect'))
async def connect(client, message):
    chat_type = message.chat.type

    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        db.add_connect(message.chat.id, message.from_user.id)
        await message.reply_text(
            '✅ Successfully connected this group to PM.\nYou can manage it using /settings in your PM.'
        )

    elif chat_type == enums.ChatType.PRIVATE:
        if len(message.command) > 1:
            group_id = int(message.command[1])
            if not await is_check_admin(client, group_id, message.from_user.id):
                return await message.reply_text('⚠️ You are not an admin in this group.')
            chat = await client.get_chat(group_id)
            db.add_connect(group_id, message.from_user.id)
            await message.reply_text(f'✅ Successfully connected {chat.title} to PM.')
        else:
            await message.reply_text('Usage:\n<code>/connect group_id</code>\nOr use /connect in a group.')


# ------------------------------
# /delete command (Admin only)
# ------------------------------
@Client.on_message(filters.command('delete'))
async def delete_file(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    try:
        query = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("⚠️ Command incomplete!\nUsage: <code>/delete query</code>")

    btn = [
        [InlineKeyboardButton("✅ YES", callback_data=f"delete_{query}")],
        [InlineKeyboardButton("❌ CLOSE", callback_data="close_data")]
    ]
    await message.reply_text(
        f"⚠️ Delete all results for: <b>{query}</b>?",
        reply_markup=InlineKeyboardMarkup(btn)
    )


# ------------------------------
# /set_fsub command (Admin only)
# ------------------------------
@Client.on_message(filters.command('set_fsub') & filters.user(ADMINS))
async def set_fsub(bot, message):
    try:
        _, ids = message.text.split(' ', 1)
    except ValueError:
        return await message.reply('Usage: <code>/set_fsub -100xxx -100yyy</code>')

    title = ""
    for id in ids.split():
        try:
            chat = await bot.get_chat(int(id))
            title += f'📌 {chat.title}\n'
        except Exception as e:
            return await message.reply(f'❌ ERROR: {e}')

    db.update_bot_sttgs('FORCE_SUB_CHANNELS', ids)
    await message.reply(f'✅ Added force-subscribe channels:\n\n{title}')


# ------------------------------
# /set_req_fsub command (Admin only)
# ------------------------------
@Client.on_message(filters.command('set_req_fsub') & filters.user(ADMINS))
async def set_req_fsub(bot, message):
    try:
        _, id = message.text.split(' ', 1)
    except ValueError:
        return await message.reply('Usage: <code>/set_req_fsub -100xxx</code>')

    try:
        chat = await bot.get_chat(int(id))
    except Exception as e:
        return await message.reply(f'❌ ERROR: {e}')

    db.update_bot_sttgs('REQUEST_FORCE_SUB_CHANNELS', id)
    await message.reply(f'✅ Added request force-subscribe channel: {chat.title}')


# ------------------------------
# Toggle Auto Filter (Admin only)
# ------------------------------
@Client.on_message(filters.command('off_auto_filter') & filters.user(ADMINS))
async def off_auto_filter(bot, message):
    db.update_bot_sttgs('AUTO_FILTER', False)
    await message.reply('✅ Auto filter turned OFF for all groups.')

@Client.on_message(filters.command('on_auto_filter') & filters.user(ADMINS))
async def on_auto_filter(bot, message):
    db.update_bot_sttgs('AUTO_FILTER', True)
    await message.reply('✅ Auto filter turned ON for all groups.')


# ------------------------------
# Toggle PM Search (Admin only)
# ------------------------------
@Client.on_message(filters.command('off_pm_search') & filters.user(ADMINS))
async def off_pm_search(bot, message):
    db.update_bot_sttgs('PM_SEARCH', False)
    await message.reply('✅ PM search turned OFF for all users.')

@Client.on_message(filters.command('on_pm_search') & filters.user(ADMINS))
async def on_pm_search(bot, message):
    db.update_bot_sttgs('PM_SEARCH', True)
    await message.reply('✅ PM search turned ON for all users.')
