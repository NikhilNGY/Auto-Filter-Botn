import asyncio
import re
from time import time as time_now
import math, os
import qrcode, random
from hydrogram.errors import ListenerTimeout
from hydrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
from datetime import datetime, timedelta
from info import PICS, TUTORIAL, SHORTLINK_API, SHORTLINK_URL, SECOND_FILES_DATABASE_URL, ADMINS, MAX_BTN, DELETE_TIME, FILMS_LINK, LOG_CHANNEL, SUPPORT_GROUP, SUPPORT_LINK, UPDATES_LINK
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from hydrogram import Client, filters, enums
from utils import get_size, is_subscribed, is_check_admin, get_wish, get_shortlink, get_readable_time, get_poster, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import get_search_results,delete_files, db_count_documents, second_db_count_documents
from plugins.commands import get_grp_stg

BUTTONS = {}
CAP = {}

# -------------------- PM SEARCH -------------------- #
@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_search(client: Client, message):
    if message.text.startswith("/"):
        return

    stg = db.get_bot_sttgs() or {}
    if not stg.get('PM_SEARCH', False):
        return await message.reply_text('⚠️ PM search is currently disabled!')

    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return

    if await is_premium(user_id, client):
        if not stg.get('AUTO_FILTER', False):
            return await message.reply_text('⚠️ Auto filter is currently disabled!')

        s = await message.reply(f"<b><i>⚠️ `{message.text}` searching...</i></b>", quote=True)
        await auto_filter(client, message, s)
    else:
        # Non-premium: show same as original search
        files, n_offset, total = await db.get_search_results(message.text)

        btn = [
            [InlineKeyboardButton("🗂 ᴄʟɪᴄᴋ ʜᴇʀᴇ 🗂", url=FILMS_LINK)],
            [InlineKeyboardButton("⚔️  ಕನ್ನಡ ಹೊಸ ಮೂವೀಗಳು  ⚔️", url=f"https://t.me/KR_PICTURE")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)

        if int(total) > 0:
            await message.reply_text(
                f'<b><i>🤗 Total <code>{total}</code> results found in this group 👇</i></b>',
                reply_markup=reply_markup
            )


# -------------------- GROUP SEARCH -------------------- #
@Client.on_message(filters.group & filters.text & filters.incoming)
async def group_search(client: Client, message):
    chat_id = message.chat.id
    user = message.from_user
    user_id = user.id if user else None
    stg = db.get_bot_sttgs() or {}

    if not stg.get('AUTO_FILTER', False):
        tmp_msg = await message.reply_text('Auto Filter is OFF! ❌')
        await asyncio.sleep(5)
        await tmp_msg.delete()
        try:
            await message.delete()
        except:
            pass
        return

    if not user_id:
        await message.reply("I'm not working for anonymous admin!")
        return

    # Support group search
    if chat_id == SUPPORT_GROUP:
        files, offset, total = await db.get_search_results(message.text)
        if files:
            btn = [[InlineKeyboardButton("Here", url=FILMS_LINK)]]
            await message.reply_text(
                f'Total {total} results found in this group',
                reply_markup=InlineKeyboardMarkup(btn)
            )
        return

    if message.text.startswith("/"):
        return

    # Link protection
    if re.findall(r'https?://\S+|www\.\S+|t\.me/\S+|@\w+', message.text):
        if await is_check_admin(client, chat_id, user_id):
            return
        try:
            await message.delete()
        except:
            pass
        await message.reply('Links are not allowed here!')
        return

    # Auto-filter search
    s = await message.reply(f"<b><i>⚠️ `{message.text}` searching...</i></b>")
    await auto_filter(client, message, s)

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot: Client, query: CallbackQuery):
    try:
        ident, req, key, offset = query.data.split("_")
        user_id = query.from_user.id

        if int(req) not in [user_id, 0]:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nDon't click other users' results!",
                show_alert=True
            )

        try:
            offset = int(offset)
        except ValueError:
            offset = 0

        search_text = temp.FILES.get(key)
        cap = temp.FILES.get(f"cap_{key}", "")

        if not search_text:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nSend a new request again!",
                show_alert=True
            )

        files, n_offset, total = await get_search_results(search_text, offset=offset)
        try:
            n_offset = int(n_offset)
        except Exception:
            n_offset = 0

        if not files:
            return

        temp.FILES[key] = files
        settings = await get_settings(query.message.chat.id)
        del_msg = f"\n\n<b>⚠️ This message will auto-delete after <code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues</b>" if settings.get("auto_delete") else ''
        files_link = ''

        # Text links or inline buttons
        if settings.get('links'):
            for idx, file in enumerate(files, start=offset + 1):
                files_link += f"\n<b>{idx}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file['_id']}>[{get_size(file['file_size'])}] {file['file_name']}</a></b>"
            btn = []
        else:
            btn = [
                [InlineKeyboardButton(f"{get_size(file['file_size'])} - {file['file_name']}", callback_data=f"file#{file['_id']}")]
                for file in files
            ]

        # Send All button
        if settings.get('shortlink') and not await is_premium(user_id, bot):
            send_all_btn = [
                InlineKeyboardButton("•  Bᴀᴄᴋ Uᴘ Cʜᴀɴɴᴇʟ  •", url=f"https://t.me/sandalwood_kannada_moviesz")
                ]
        else:
            send_all_btn = [InlineKeyboardButton("•  Bᴀᴄᴋ Uᴘ Cʜᴀɴɴᴇʟ  •", url=f"https://t.me/sandalwood_kannada_moviesz")
                ]

        # Pagination
        off_set = 0 if 0 < offset <= MAX_BTN else None if offset == 0 else offset - MAX_BTN
        page_btn = []
        current_page = math.ceil(int(offset) / MAX_BTN) + 1
        total_pages = math.ceil(total / MAX_BTN)

        if n_offset == 0:
            page_btn = [
                InlineKeyboardButton("« Back", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="buttons")
            ]
        elif off_set is None:
            page_btn = [
                InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="buttons"),
                InlineKeyboardButton("Next »", callback_data=f"next_{req}_{key}_{n_offset}")
            ]
        else:
            page_btn = [
                InlineKeyboardButton("« Back", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="buttons"),
                InlineKeyboardButton("Next »", callback_data=f"next_{req}_{key}_{n_offset}")
            ]

        # Build final buttons
        btn.insert(0, send_all_btn)
        btn.append([InlineKeyboardButton("⚔️  ಕನ್ನಡ ಹೊಸ ಮೂವೀಗಳು  ⚔️", url=f"https://t.me/KR_PICTURE")])
        btn.append(page_btn)

        await query.message.edit_text(
            cap + files_link + del_msg,
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

    except Exception:
        await query.answer("An error occurred, please try again.", show_alert=True)

@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, movie_id, user_id = query.data.split("#")
    user_id = int(user_id)

    # Prevent others from clicking
    if user_id != 0 and query.from_user.id != user_id:
        return await query.answer(f"Hello {query.from_user.first_name},\nDon't Click Other Results!", show_alert=True)

    # Fetch movie details
    movie = await get_poster(movie_id, id=True)
    if not movie:
        await query.answer("Movie not found!", show_alert=True)
        return

    search_title = movie.get('title', 'Unknown')
    msg = await query.message.edit_text(f"<b><i><code>{search_title}</code> checking in my database...</i></b>")
    await query.answer()  # acknowledge callback

    # Search for files
    files, offset, total_results = await get_search_results(search_title)
    if files:
        # Pass results to auto_filter
        await auto_filter(bot, query, msg, (search_title, files, offset, total_results))
    else:
        # No results found
        no_result_msg = await query.message.edit_text(
            f"""<b>⚠️ Dᴏɴ'ᴛ Aꜱᴋ Lɪᴋᴇ Tʜɪꜱ. Aꜱᴋ Oɴʟʏ Mᴏᴠɪᴇ Nᴀᴍᴇ Wɪᴛʜ Yᴇᴀʀ. (Cʜᴇᴄᴋ Cᴏʀʀᴇᴄᴛ Sᴘᴇʟʟɪɴɢ Sᴀᴍᴇ Aꜱ Iɴ Gᴏᴏɢʟᴇ) Dᴏɴ'ᴛ Aᴅᴅ Aɴʏ Wᴏʀᴅꜱ Wʜɪʟᴇ RᴇQᴜᴇꜱᴛɪɴɢ. Oᴛʜᴇʀᴡɪꜱᴇ Yᴏᴜ Dᴏɴ'ᴛ Gᴇᴛ Tʜᴇ Mᴏᴠɪᴇ Cᴏʀʀᴇᴄᴛʟʏ🚫⚠️\n \nAᴅᴅ Mᴏᴠɪᴇ Nᴀᴍᴇ: \nEg:\n777 ᴄʜᴀʀʟɪᴇ ✅\n777 ᴄʜᴀʀʟɪᴇ 2022 ✅\n777 ᴄʜᴀʀʟɪᴇ ᴋᴀɴɴᴀᴅᴀ ✅\n777ᴄʜᴀʀʟɪᴇ ❌ \n777 ᴄʜᴀʀʟɪᴇ ᴍᴏᴠɪᴇ ❌\n777 ᴄʜᴀʀʟɪᴇ ʟɪɴᴋ ❌ ᴇᴛᴄ.</b>"""
        )
        # Log no result
        await bot.send_message(LOG_CHANNEL, f"#No_Result\n\nRequester: {query.from_user.mention}\nContent: {search_title}")

        # Auto-delete messages after 1 minute
        await asyncio.sleep(60)
        try:
            await no_result_msg.delete()
            if query.message.reply_to_message:
                await query.message.reply_to_message.delete()
        except:
            pass

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    reply_user_id = None
    try:
        reply_user_id = query.message.reply_to_message.from_user.id
    except:
        reply_user_id = user_id

    # --- CLOSE BUTTON ---
    if query.data == "close_data":
        if reply_user_id != 0 and user_id != reply_user_id:
            return await query.answer(f"Hello {query.from_user.first_name},\nThis Is Not For You!", show_alert=True)
        await query.answer("Closed!")
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    # --- FILE BUTTON ---
    elif query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        if reply_user_id != 0 and user_id != reply_user_id:
            return await query.answer(f"Hello {query.from_user.first_name},\nDon't Click Other Results!", show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")

    # --- CHECK SUBSCRIPTION ---
    elif query.data.startswith("checksub"):
        ident, mc = query.data.split("#")
        btn = await is_subscribed(client, query)
        if btn:
            await query.answer(f"Hello {query.from_user.first_name},\nPlease join my updates channel and try again.", show_alert=True)
            btn.append([InlineKeyboardButton("🔁 Try Again 🔁", callback_data=f"checksub#{mc}")])
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
            return
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={mc}")
        await query.message.delete()

    # --- INFORMATION BUTTONS ---
    elif query.data == "buttons":
        await query.answer()

    # --- START BUTTON ---
    elif query.data == "start":
        buttons = [
            [InlineKeyboardButton('🎬   Bᴀᴄᴋ Uᴘ Cʜᴀɴɴᴇʟ   🎬', url=f'https://t.me/+pCz5eoun5Zk5YzRl')
                ],[
                    InlineKeyboardButton('🎞 Mᴀɪɴ Gʀᴏᴜᴘ ', url=f"https://t.me/Sandalwood_Kannada_Group"),
                    InlineKeyboardButton('🆕 Mᴀɪɴ Cʜᴀɴɴᴇʟ ', url="https://t.me/KR_PICTURE")
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(temp.PICS), caption=script.START_TXT.format(query.from_user.mention, get_wish())),
            reply_markup=reply_markup
        )

    # --- STATS BUTTON ---
    elif query.data == "stats":
        if user_id not in ADMINS:
            return await query.answer("ADMINS Only!", show_alert=True)
        files = db_count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        prm = db.get_premium_count()
        used_files_db_size = get_size(await db.get_files_db_size())
        used_data_db_size = get_size(await db.get_data_db_size())
        if SECOND_FILES_DATABASE_URL:
            secnd_files_db_used_size = get_size(await db.get_second_files_db_size())
            secnd_files = second_db_count_documents()
        else:
            secnd_files_db_used_size = '-'
            secnd_files = '-'
        uptime = get_readable_time(time_now() - START_TIME)
        buttons = [[InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='start')]]
        await query.edit_message_media(
            InputMediaPhoto(random.choice(temp.PICS), caption=script.STATUS_TXT.format(
                users, prm, chats, used_data_db_size, files, used_files_db_size, secnd_files, secnd_files_db_used_size, uptime
            )),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # --- USER & ADMIN COMMANDS ---
    elif query.data == "user_command":
        buttons = [[InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='help')]]
        await query.edit_message_media(InputMediaPhoto(random.choice(temp.PICS), caption=script.USER_COMMAND_TXT), reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "admin_command":
        if user_id not in ADMINS:
            return await query.answer("ADMINS Only!", show_alert=True)
        buttons = [[InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='help')]]
        await query.edit_message_media(InputMediaPhoto(random.choice(temp.PICS), caption=script.ADMIN_COMMAND_TXT), reply_markup=InlineKeyboardMarkup(buttons))

    # --- GROUP SETTINGS ---
    elif query.data.startswith("bool_setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("You not admin in this group.", show_alert=True)
        await save_group_settings(int(grp_id), set_type, status != "True")
        btn = await get_grp_stg(int(grp_id))
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))

    # --- OPEN SETTINGS ---
    elif query.data == "open_group_settings":
        if not await is_check_admin(client, query.message.chat.id, user_id):
            return await query.answer("You not admin in this group.", show_alert=True)
        btn = await get_grp_stg(query.message.chat.id)
        await query.message.edit(text=f"Change your settings for <b>'{query.message.chat.title}'</b> as your wish. ⚙", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "open_pm_settings":
        if not await is_check_admin(client, query.message.chat.id, user_id):
            return await query.answer("You not admin in this group.", show_alert=True)
        btn = await get_grp_stg(query.message.chat.id)
        try:
            await client.send_message(user_id, f"Change your settings for <b>'{query.message.chat.title}'</b> as your wish. ⚙", reply_markup=InlineKeyboardMarkup(btn))
        except:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start=settings_{query.message.chat.id}")
        await query.message.edit("Settings menu has been sent to PM", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go To PM', url=f"https://t.me/{temp.U_NAME}")]]))

    # --- DELETE FILES ---
    elif query.data.startswith("delete"):
        _, query_ = query.data.split("_", 1)
        await query.message.edit('Deleting...')
        deleted = await delete_files(query_)
        await query.message.edit(f'Deleted {deleted} files in your database in your query {query_}')

    # --- KICK DELETED ACCOUNTS ---
    elif query.data == "kick_deleted_accounts_members":
        if not await is_check_admin(client, query.message.chat.id, user_id):
            return await query.answer("This Is Not For You!", show_alert=True)
        users_id = []
        await query.message.edit("Kick deleted accounts started! This process may take some time...")
        try:
            async for member in client.get_chat_members(query.message.chat.id):
                if member.user.is_deleted:
                    users_id.append(member.user.id)
            for uid in users_id:
                await client.ban_chat_member(query.message.chat.id, uid, datetime.now() + timedelta(seconds=30))
        except Exception as e:
            await query.message.delete()
            await query.message.reply(f'Something went wrong.\n\n<code>{e}</code>')
            return
        await query.message.delete()
        if users_id:
            await query.message.reply(f"Successfully kicked deleted <code>{len(users_id)}</code> accounts.")
        else:
            await query.message.reply('Nothing to kick deleted accounts.')

async def auto_filter(client, msg, s, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        search = re.sub(r"\s+", " ", re.sub(r"[-:\"';!]", " ", message.text)).strip()
        files, offset, total_results = await get_search_results(search)

        if not files:
            if settings.get("spell_check"):
                return await advantage_spell_chok(message, s)
            return await s.edit(f"I couldn't find <b>{search}</b>")
    else:
        # Callback search
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll

    req = message.from_user.id if message and message.from_user else 0
    key = f"{message.chat.id}-{message.id}"

    # Store results in temporary cache
    temp.FILES[key] = files
    temp.BUTTONS[key] = search

    # Build file links text
    files_link = ""
    if settings.get("links"):
        for i, file in enumerate(files, start=1):
            files_link += (
                f"\n\n<b>{i}. "
                f"<a href=https://t.me/{temp.U_NAME}?start=file_{message.chat.id}_{file['_id']}>"
                f"[{get_size(file['file_size'])}] {file['file_name']}</a></b>"
            )

    # Build inline buttons
    if settings.get("links"):
        btn = []
    else:
        btn = [[
            InlineKeyboardButton(
                text=f"{get_size(file['file_size'])} - {file['file_name']}",
                callback_data=f'file#{file["_id"]}'
            )
        ] for file in files]

    # Pagination buttons (simplified)
    if offset != "":
        btn.append([
            InlineKeyboardButton(f"1/{math.ceil(int(total_results) / MAX_BTN)}", callback_data="buttons"),
            InlineKeyboardButton("Next »", callback_data=f"next_{req}_{key}_{offset}")
        ])

    # Join Kannada Channel button
    btn.append([
        InlineKeyboardButton("⚔️  ಕನ್ನಡ ಹೊಸ ಮೂವೀಗಳು  ⚔️", url=f"https://t.me/KR_PICTURE")
    ])

    # IMDB integration
    imdb = await get_poster(search, file=(files[0])["file_name"]) if settings.get("imdb") else None
    template = settings.get("template")

    if imdb:
        try:
            cap = template.format(**imdb, query=search, **locals())
        except Exception:
            cap = f"<b>💭 Hey {message.from_user.mention},\nHere are results for <code>{search}</code>...</b>"
    else:
        cap = f"<b>💭 Hey {message.from_user.mention},\nHere are results for <code>{search}</code>...</b>"

    temp.CAP[key] = cap

    # Auto-delete text
    del_msg = (
        f"\n\n<b>⚠️ This message will auto-delete after "
        f"<code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues.</b>"
        if settings.get("auto_delete") else ""
    )

    # Send final message
    if imdb and imdb.get("poster"):
        await s.delete()
        try:
            k = await message.reply_photo(
                photo=imdb["poster"],
                caption=cap[:1024] + files_link + del_msg,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
        except Exception:
            k = await message.reply_text(
                cap + files_link + del_msg,
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
    else:
        k = await s.edit_text(
            cap + files_link + del_msg,
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

    # Auto-delete
    if settings.get("auto_delete"):
        await asyncio.sleep(DELETE_TIME)
        await k.delete()
        try:
            await message.delete()
        except:
            pass


async def advantage_spell_chok(message, s):
    """
    Spelling correction / alternative suggestions when no results are found.
    """
    search = message.text.strip()
    google_search = search.replace(" ", "+")
    user_mention = message.from_user.mention if message.from_user else "Anonymous"
    user_id = message.from_user.id if message.from_user else 0

    base_btn = [
        [
            InlineKeyboardButton("⚔️  ಕನ್ನಡ ಹೊಸ ಮೂವೀಗಳು  ⚔️", url=f"https://t.me/KR_PICTURE")
        ]
    ]

    try:
        movies = await get_poster(search, bulk=True)
    except Exception:
        n = await s.edit_text(
            text=script.NOT_FILE_TXT.format(user_mention, search),
            reply_markup=InlineKeyboardMarkup(base_btn)
        )
        await asyncio.sleep(60)
        await n.delete()
        try:
            await message.delete()
        except:
            pass
        return

    if not movies:
        n = await s.edit_text(
            text=script.NOT_FILE_TXT.format(user_mention, search),
            reply_markup=InlineKeyboardMarkup(base_btn)
        )
        await asyncio.sleep(3600)
        await n.delete()
        try:
            await message.delete()
        except:
            pass
        return

    movies = list(dict.fromkeys(movies))  # remove duplicates

    suggestion_buttons = [
        [InlineKeyboardButton(text=movie.get("title", "Unknown"), callback_data=f"spolling#{movie.movieID}#{user_id}")]
        for movie in movies
    ]
    suggestion_buttons.append([InlineKeyboardButton("🚫 Close 🚫", callback_data="close_data")])

    suggestion_msg = await s.edit_text(
        text=(
            f"👋 Hello {user_mention},\n\n"
            f"I couldn't find <b>'{search}'</b> in the database.\n"
            f"Did you mean one of these? 👇"
        ),
        reply_markup=InlineKeyboardMarkup(suggestion_buttons)
    )

    # Auto-cleanup
    await asyncio.sleep(3600)
    await suggestion_msg.delete()
    try:
        await message.delete()
    except:
        pass
