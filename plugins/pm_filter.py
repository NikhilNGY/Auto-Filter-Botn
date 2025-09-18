import asyncio
import re
from time import time as time_now
import math, os
import qrcode, random
from hydrogram.errors import ListenerTimeout
from hydrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
from datetime import datetime, timedelta
from info import IS_PREMIUM, PICS, TUTORIAL, SHORTLINK_API, SHORTLINK_URL, RECEIPT_SEND_USERNAME, UPI_ID, UPI_NAME, PRE_DAY_AMOUNT, SECOND_FILES_DATABASE_URL, ADMINS, URL, MAX_BTN, BIN_CHANNEL, IS_STREAM, DELETE_TIME, FILMS_LINK, LOG_CHANNEL, SUPPORT_GROUP, SUPPORT_LINK, UPDATES_LINK, LANGUAGES, QUALITY
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from hydrogram import Client, filters, enums
from utils import is_premium, get_size, is_subscribed, is_check_admin, get_wish, get_shortlink, get_readable_time, get_poster, temp, get_settings, save_group_settings
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
        # Non-premium: show limited search
        files, n_offset, total = await db.get_search_results(message.text)

        btn = [
            [InlineKeyboardButton("🗂 ᴄʟɪᴄᴋ ʜᴇʀᴇ 🗂", url=FILMS_LINK)],
            [InlineKeyboardButton("🤑 Buy Premium", url=f"https://t.me/{temp.U_NAME}?start=premium")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)

        if int(total) > 0:
            await message.reply_text(
                f'<b><i>🤗 Total <code>{total}</code> results found in this group 👇</i></b>\n\nor buy premium subscription',
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

    # Admin mentions handling
    if '@admin' in message.text.lower() or '@admins' in message.text.lower():
        if await is_check_admin(client, chat_id, user_id):
            return

        admins = []
        async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if not member.user.is_bot:
                admins.append(member.user.id)
                if member.status == enums.ChatMemberStatus.OWNER:
                    target_msg = message.reply_to_message or message
                    try:
                        sent_msg = await target_msg.forward(member.user.id)
                        await sent_msg.reply_text(
                            f"#Attention\n★ User: {user.mention}\n★ Group: {message.chat.title}\n\n"
                            f"★ <a href={target_msg.link}>Go to message</a>",
                            disable_web_page_preview=True
                        )
                    except:
                        pass
        hidden_mentions = ''.join(f'[\u2064](tg://user?id={uid})' for uid in admins)
        await message.reply_text('Report sent!' + hidden_mentions)
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

    # Requests handling
    if '#request' in message.text.lower():
        if user_id in ADMINS:
            return
        await client.send_message(
            LOG_CHANNEL,
            f"#Request\n★ User: {user.mention}\n★ Group: {message.chat.title}\n\n"
            f"★ Message: {re.sub(r'#request', '', message.text, flags=re.IGNORECASE)}"
        )
        await message.reply_text("Request sent!")
        return

    # Auto-filter search
    s = await message.reply(f"<b><i>⚠️ `{message.text}` searching...</i></b>")
    await auto_filter(client, message, s)

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot: Client, query):
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

        search = temp.FILES.get(key)
        cap = temp.FILES.get(f"cap_{key}", "")

        if not search:
            await query.answer(
                f"Hello {query.from_user.first_name},\nSend a new request again!",
                show_alert=True
            )
            return

        files, n_offset, total = await get_search_results(search, offset=offset)
        try:
            n_offset = int(n_offset)
        except:
            n_offset = 0

        if not files:
            return

        temp.FILES[key] = files
        settings = await get_settings(query.message.chat.id)
        del_msg = f"\n\n<b>⚠️ This message will auto-delete after <code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues</b>" if settings.get("auto_delete") else ''
        files_link = ''

        # Text links
        if settings.get('links'):
            for idx, file in enumerate(files, start=offset + 1):
                files_link += f"\n<b>{idx}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file['_id']}>[{get_size(file['file_size'])}] {file['file_name']}</a></b>"
            btn = []
        else:  # Inline buttons
            btn = [
                [InlineKeyboardButton(f"{get_size(file['file_size'])} - {file['file_name']}", callback_data=f"file#{file['_id']}")]
                for file in files
            ]

        # Extra buttons
        languages_btn = [InlineKeyboardButton("📰 Languages", callback_data=f"languages#{key}#{req}#{offset}"),
                         InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{offset}")]
        
        if settings.get('shortlink') and not await is_premium(user_id, bot):
            send_all_btn = [InlineKeyboardButton("♻️ Send All ♻️", url=await get_shortlink(settings['url'], settings['api'], f'https://t.me/{temp.U_NAME}?start=all_{query.message.chat.id}_{key}'))]
        else:
            send_all_btn = [InlineKeyboardButton("♻️ Send All", callback_data=f"send_all#{key}#{req}")]

        # Pagination logic
        off_set = 0 if 0 < offset <= MAX_BTN else None if offset == 0 else offset - MAX_BTN
        page_btn = []
        current_page = math.ceil(int(offset) / MAX_BTN) + 1
        total_pages = math.ceil(total / MAX_BTN)

        if n_offset == 0:
            page_btn = [InlineKeyboardButton("« Back", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="buttons")]
        elif off_set is None:
            page_btn = [InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="buttons"),
                        InlineKeyboardButton("Next »", callback_data=f"next_{req}_{key}_{n_offset}")]
        else:
            page_btn = [InlineKeyboardButton("« Back", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="buttons"),
                        InlineKeyboardButton("Next »", callback_data=f"next_{req}_{key}_{n_offset}")]

        btn.insert(0, languages_btn)
        btn.insert(1, send_all_btn)
        btn.append([InlineKeyboardButton('🤑 Buy Premium', url=f"https://t.me/{temp.U_NAME}?start=premium")])
        btn.append(page_btn)

        await query.message.edit_text(
            cap + files_link + del_msg,
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await query.answer("An error occurred, please try again.", show_alert=True)

from hydrogram import Client, filters, enums
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from utils import get_search_results, get_settings, get_readable_time, get_size, is_premium, temp
from info import QUALITY, DELETE_TIME
import math

@Client.on_callback_query(filters.regex(r"^quality"))
async def quality_callback(client: Client, query: CallbackQuery):
    try:
        _, key, req, offset = query.data.split("#")
        if int(req) != query.from_user.id:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nDon't click other results!",
                show_alert=True
            )

        # Build quality selection buttons (two per row)
        btn = [
            [
                InlineKeyboardButton(text=QUALITY[i].title(), callback_data=f"qual_search#{QUALITY[i]}#{key}#{offset}#{req}"),
                InlineKeyboardButton(text=QUALITY[i+1].title(), callback_data=f"qual_search#{QUALITY[i+1]}#{key}#{offset}#{req}")
            ] for i in range(0, len(QUALITY)-1, 2)
        ]
        # Back to main page button
        btn.append([InlineKeyboardButton(text="⪻ Back to Main Page", callback_data=f"next_{req}_{key}_{offset}")])

        await query.message.edit_text(
            "<b>Select the quality you want 👇</b>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except Exception as e:
        await query.answer("An error occurred. Please try again.", show_alert=True)


@Client.on_callback_query(filters.regex(r"^lang_search"))
async def filter_languages_callback(client: Client, query: CallbackQuery):
    try:
        _, lang, key, offset, req = query.data.split("#")
        if int(req) != query.from_user.id:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nDon't click other results!",
                show_alert=True
            )

        search = temp.FILES.get(key)
        cap = temp.FILES.get(f"cap_{key}", "")

        if not search:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nSend a new request again!",
                show_alert=True
            )

        files, l_offset, total_results = await get_search_results(search, lang=lang)
        if not files:
            return await query.answer(
                f"Sorry, '{lang.title()}' language files not found 😕",
                show_alert=True
            )

        temp.FILES[key] = files
        settings = await get_settings(query.message.chat.id)
        del_msg = f"\n\n<b>⚠️ This message will auto-delete after <code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues</b>" if settings.get("auto_delete") else ''
        files_link = ''

        # Create file links or buttons
        if settings.get('links'):
            for idx, file in enumerate(files, start=1):
                files_link += f"<b>\n\n{idx}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file['_id']}>[{get_size(file['file_size'])}] {file['file_name']}</a></b>"
            btn = []
        else:
            btn = [
                [InlineKeyboardButton(f"{get_size(file['file_size'])} - {file['file_name']}", callback_data=f"file#{file['_id']}")]
                for file in files
            ]

        # Add send all and quality buttons
        if settings.get('shortlink') and not await is_premium(query.from_user.id, client):
            btn.insert(1, [
                InlineKeyboardButton("♻️ Send All ♻️", url=await get_shortlink(settings['url'], settings['api'], f'https://t.me/{temp.U_NAME}?start=all_{query.message.chat.id}_{key}')),
                InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{offset}")
            ])
        else:
            btn.insert(1, [
                InlineKeyboardButton("♻️ Send All", callback_data=f"send_all#{key}#{req}"),
                InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{offset}")
            ])

        # Pagination for language results
        if l_offset:
            btn.append([
                InlineKeyboardButton(f"1/{math.ceil(int(total_results) / 8)}", callback_data="buttons"),
                InlineKeyboardButton("Next »", callback_data=f"lang_next#{req}#{key}#{lang}#{l_offset}#{offset}")
            ])

        # Back to main page button
        btn.append([InlineKeyboardButton("⪻ Back to Main Page", callback_data=f"next_{req}_{key}_{offset}")])

        await query.message.edit_text(
            cap + files_link + del_msg,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await query.answer("An error occurred. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex(r"^lang_next"))
async def lang_next_page(bot: Client, query: CallbackQuery):
    try:
        _, req, key, lang, l_offset, offset = query.data.split("#")
        if int(req) != query.from_user.id:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nDon't click other results!",
                show_alert=True
            )

        l_offset = int(l_offset) if l_offset.isdigit() else 0
        offset = int(offset) if offset.isdigit() else 0

        search = temp.FILES.get(key)
        cap = temp.FILES.get(f"cap_{key}", "")
        if not search:
            return await query.answer(
                f"Hello {query.from_user.first_name},\nSend a new request again!",
                show_alert=True
            )

        settings = await get_settings(query.message.chat.id)
        del_msg = f"\n\n<b>⚠️ This message will auto-delete after <code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues</b>" if settings.get("auto_delete") else ''

        files, n_offset, total = await get_search_results(search, offset=l_offset, lang=lang)
        if not files:
            return

        temp.FILES[key] = files
        n_offset = int(n_offset) if n_offset else 0

        # Build message content
        files_link = ''
        if settings.get('links'):
            for idx, file in enumerate(files, start=l_offset + 1):
                files_link += f"<b>\n\n{idx}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file['_id']}>[{get_size(file['file_size'])}] {file['file_name']}</a></b>"
            btn = []
        else:
            btn = [[InlineKeyboardButton(f"{get_size(file['file_size'])} - {file['file_name']}", callback_data=f"file#{file['_id']}")] for file in files]

        # Add send all / quality buttons
        if settings.get('shortlink') and not await is_premium(query.from_user.id, bot):
            btn.insert(1, [
                InlineKeyboardButton("♻️ Send All ♻️", url=await get_shortlink(settings['url'], settings['api'], f'https://t.me/{temp.U_NAME}?start=all_{query.message.chat.id}_{key}')),
                InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{l_offset}")
            ])
        else:
            btn.insert(1, [
                InlineKeyboardButton("♻️ Send All ♻️", callback_data=f"send_all#{key}#{req}"),
                InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{l_offset}")
            ])

        # Pagination buttons
        if 0 < l_offset <= MAX_BTN:
            b_offset = 0
        elif l_offset == 0:
            b_offset = None
        else:
            b_offset = l_offset - MAX_BTN

        page_number = math.ceil(l_offset / MAX_BTN) + 1
        total_pages = math.ceil(total / MAX_BTN) if total else 1

        if n_offset == 0:
            btn.append([
                InlineKeyboardButton("« Back", callback_data=f"lang_next#{req}#{key}#{lang}#{b_offset}#{offset}"),
                InlineKeyboardButton(f"{page_number}/{total_pages}", callback_data="buttons")
            ])
        elif b_offset is None:
            btn.append([
                InlineKeyboardButton(f"{page_number}/{total_pages}", callback_data="buttons"),
                InlineKeyboardButton("Next »", callback_data=f"lang_next#{req}#{key}#{lang}#{n_offset}#{offset}")
            ])
        else:
            btn.append([
                InlineKeyboardButton("« Back", callback_data=f"lang_next#{req}#{key}#{lang}#{b_offset}#{offset}"),
                InlineKeyboardButton(f"{page_number}/{total_pages}", callback_data="buttons"),
                InlineKeyboardButton("Next »", callback_data=f"lang_next#{req}#{key}#{lang}#{n_offset}#{offset}")
            ])

        # Back to main page button
        btn.append([InlineKeyboardButton("⪻ Back to Main Page", callback_data=f"next_{req}_{key}_{offset}")])

        await query.message.edit_text(
            cap + files_link + del_msg,
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await query.answer("An error occurred. Please try again.", show_alert=True)

async def build_file_buttons(files, chat_id, key, req, offset, settings, premium=False):
    """Build message text and InlineKeyboardMarkup for files."""
    files_link = ''
    if settings['links']:
        for i, file in enumerate(files, start=offset + 1):
            files_link += f"<b>\n\n{i}. <a href=https://t.me/{temp.U_NAME}?start=file_{chat_id}_{file['_id']}>[{get_size(file['file_size'])}] {file['file_name']}</a></b>"
        btn = []
    else:
        btn = [[InlineKeyboardButton(f"{get_size(f['file_size'])} - {f['file_name']}", callback_data=f"file#{f['_id']}")] for f in files]

    # Add send all button
    if settings['shortlink'] and not premium:
        btn.insert(0, [InlineKeyboardButton(
            "♻️ Send All ♻️",
            url=await get_shortlink(settings['url'], settings['api'], f'https://t.me/{temp.U_NAME}?start=all_{chat_id}_{key}')
        )])
    else:
        btn.insert(0, [InlineKeyboardButton("♻️ Send All ♻️", callback_data=f"send_all#{key}#{req}")])

    return files_link, btn

def get_back_offset(current_offset):
    if 0 < current_offset <= MAX_BTN:
        return 0
    elif current_offset == 0:
        return None
    else:
        return current_offset - MAX_BTN

@Client.on_callback_query(filters.regex(r"^qual_search"))
async def quality_search(client: Client, query: CallbackQuery):
    _, qual, key, offset, req = query.data.split("#")
    req = int(req)
    if req != query.from_user.id:
        return await query.answer("Don't Click Other Results!", show_alert=True)

    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        return await query.answer("Send New Request Again!", show_alert=True)

    files, l_offset, total_results = await get_search_results(search, lang=qual)
    if not files:
        return await query.answer(f"sᴏʀʀʏ '{qual.title()}' files not found 😕", show_alert=True)

    temp.FILES[key] = files
    settings = await get_settings(query.message.chat.id)
    del_msg = f"\n\n<b>⚠️ This message will auto delete after <code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues</b>" if settings.get("auto_delete") else ''

    files_link, btn = await build_file_buttons(files, query.message.chat.id, key, req, 0, settings)

    if l_offset:
        btn.append([
            InlineKeyboardButton(f"1/{math.ceil(int(total_results)/MAX_BTN)}", callback_data="buttons"),
            InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"qual_next#{req}#{key}#{qual}#{l_offset}#{offset}")
        ])
    btn.append([InlineKeyboardButton("⪻ Back to Main Page", callback_data=f"next_{req}_{key}_{offset}")])

    await query.message.edit_text(cap + files_link + del_msg, disable_web_page_preview=True,
                                  reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex(r"^qual_next"))
async def quality_next_page(client: Client, query: CallbackQuery):
    _, req, key, qual, l_offset, offset = query.data.split("#")
    req = int(req)
    if req != query.from_user.id:
        return await query.answer("Don't Click Other Results!", show_alert=True)

    try:
        l_offset = int(l_offset)
    except:
        l_offset = 0

    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        return await query.answer("Send New Request Again!", show_alert=True)

    files, n_offset, total = await get_search_results(search, offset=l_offset, lang=qual)
    if not files:
        return

    temp.FILES[key] = files
    settings = await get_settings(query.message.chat.id)
    del_msg = f"\n\n<b>⚠️ This message will auto delete after <code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues</b>" if settings.get("auto_delete") else ''

    files_link, btn = await build_file_buttons(files, query.message.chat.id, key, req, l_offset, settings)

    b_offset = get_back_offset(l_offset)
    page_num = math.ceil(l_offset / MAX_BTN) + 1

    # Pagination buttons
    if n_offset == 0:
        btn.append([
            InlineKeyboardButton("« Back", callback_data=f"qual_next#{req}#{key}#{qual}#{b_offset}#{offset}"),
            InlineKeyboardButton(f"{page_num}/{math.ceil(total/MAX_BTN)}", callback_data="buttons")
        ])
    elif b_offset is None:
        btn.append([
            InlineKeyboardButton(f"{page_num}/{math.ceil(total/MAX_BTN)}", callback_data="buttons"),
            InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"qual_next#{req}#{key}#{qual}#{n_offset}#{offset}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("« Back", callback_data=f"qual_next#{req}#{key}#{qual}#{b_offset}#{offset}"),
            InlineKeyboardButton(f"{page_num}/{math.ceil(total/MAX_BTN)}", callback_data="buttons"),
            InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"qual_next#{req}#{key}#{qual}#{n_offset}#{offset}")
        ])

    btn.append([InlineKeyboardButton("⪻ Back to Main Page", callback_data=f"next_{req}_{key}_{offset}")])

    await query.message.edit_text(cap + files_link + del_msg, disable_web_page_preview=True,
                                  reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

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
            f"👋 Hello {query.from_user.mention},\n\nI couldn't find <b>'{search_title}'</b> in my database. 😔"
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
    if query.data == "close_data":
        try:
            user = query.message.reply_to_message.from_user.id
        except:
            user = query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(f"Hello {query.from_user.first_name},\nThis Is Not For You!", show_alert=True)
        await query.answer("Closed!")
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
  
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        try:
            user = query.message.reply_to_message.from_user.id
        except:
            user = query.message.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(f"Hello {query.from_user.first_name},\nDon't Click Other Results!", show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")

    elif query.data.startswith("get_del_file"):
        ident, group_id, file_id = query.data.split("#")
        if not await is_premium(query.from_user.id, client):
            return await query.answer(f"Only for premium users, use /plan for details", show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{group_id}_{file_id}")
        await query.message.delete()

    elif query.data.startswith("get_del_send_all_files"):
        ident, group_id, key = query.data.split("#")
        if not await is_premium(query.from_user.id, client):
            return await query.answer(f"Only for premium users, use /plan for details", show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=all_{group_id}_{key}")
        await query.message.delete()
        
    elif query.data.startswith("stream"):
        file_id = query.data.split('#', 1)[1]
        if not await is_premium(query.from_user.id, client):
            return await query.answer(f"Only for premium users, use /plan for details", show_alert=True)
        msg = await client.send_cached_media(chat_id=BIN_CHANNEL, file_id=file_id)
        watch = f"{URL}watch/{msg.id}"
        download = f"{URL}download/{msg.id}"
        btn=[[
            InlineKeyboardButton("ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ", url=watch),
            InlineKeyboardButton("ꜰᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ", url=download)
        ],[
            InlineKeyboardButton('❌ ᴄʟᴏsᴇ ❌', callback_data='close_data')
        ]]
        reply_markup=InlineKeyboardMarkup(btn)
        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )
    
            
    elif query.data.startswith("checksub"):
        ident, mc = query.data.split("#")
        settings = await get_settings(int(mc.split("_", 2)[1]))
        btn = await is_subscribed(client, query)
        if btn:
            await query.answer(f"Hello {query.from_user.first_name},\nPlease join my updates channel and try again.", show_alert=True)
            btn.append(
                [InlineKeyboardButton("🔁 Try Again 🔁", callback_data=f"checksub#{mc}")]
            )
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
            return
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={mc}")
        await query.message.delete()

    elif query.data == "buttons":
        await query.answer()

    elif query.data == "instructions":
        await query.answer("Movie request format.\nExample:\nBlack Adam or Black Adam 2022\n\nTV Reries request format.\nExample:\nLoki S01E01 or Loki S01 E01\n\nDon't use symbols.", show_alert=True)

    elif query.data == 'activate_trial':
        mp = db.get_plan(query.from_user.id)
        if mp['trial']:
            return await query.message.edit('You already used trial, use /plan to activate plan')
        ex = datetime.now() + timedelta(hours=1)
        mp['expire'] = ex
        mp['trial'] = True
        mp['plan'] = '1 hour'
        mp['premium'] = True
        db.update_plan(query.from_user.id, mp)
        await query.message.edit(f"Congratulations! Your activated trial for 1 hour\nExpire: {ex.strftime('%Y.%m.%d %H:%M:%S')}")

    elif query.data == 'activate_plan':
        q = await query.message.edit('How many days you need premium plan?\nSend days as number')
        msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        try:
            d = int(msg.text)
        except:
            await q.delete()
            return await query.message.reply('Invalid number\nIf you want 7 days then send 7 only')
        transaction_note = f'{d} days premium plan for {query.from_user.id}'
        amount = d * PRE_DAY_AMOUNT
        upi_uri = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amount}&cu=INR&tn={transaction_note}"
        qr = qrcode.make(upi_uri)
        p = f"upi_qr_{query.from_user.id}.png"
        qr.save(p)
        await q.delete()
        await query.message.reply_photo(p, caption=f"{d} days premium plan amount is {amount} INR\nScan this QR in your UPI support platform and pay that amount (This is dynamic QR)\n\nSend your receipt as photo in here (timeout in 10 mins)\n\nSupport: {RECEIPT_SEND_USERNAME}")
        os.remove(p)
        try:
            msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id, timeout=600)
        except ListenerTimeout:
            await q.delete()
            return await query.message.reply(f'Your time is over, send your receipt to: {RECEIPT_SEND_USERNAME}')
        if msg.photo:
            await q.delete()
            await query.message.reply(f'Your receipt was sent, wait some time\nSupport: {RECEIPT_SEND_USERNAME}')
            await client.send_photo(RECEIPT_SEND_USERNAME, msg.photo.file_id, transaction_note)
        else:
            await q.delete()
            await query.message.reply(f"Not valid photo, send your receipt to: {RECEIPT_SEND_USERNAME}")



    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton("+ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ +", url=f'http://t.me/{temp.U_NAME}?startgroup=start')
        ],[
            InlineKeyboardButton('ℹ️ ᴜᴘᴅᴀᴛᴇs', url=UPDATES_LINK),
            InlineKeyboardButton('🧑‍💻 ꜱᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
        ],[
            InlineKeyboardButton('👨‍🚒 ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('🔎 ɪɴʟɪɴᴇ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('📚 ᴀʙᴏᴜᴛ', callback_data='about')
        ],[
            InlineKeyboardButton('🤑 Buy Premium', url=f"https://t.me/{temp.U_NAME}?start=premium")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.START_TXT.format(query.from_user.mention, get_wish())),
            reply_markup=reply_markup
        )
        
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('📊 sᴛᴀᴛᴜs 📊', callback_data='stats'),
            InlineKeyboardButton('🤖 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 🤖', callback_data='source')
        ],[
            InlineKeyboardButton('🧑‍💻 ʙᴏᴛ ᴏᴡɴᴇʀ 🧑‍💻', callback_data='owner')
        ],[
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.MY_ABOUT_TXT),
            reply_markup=reply_markup
        )

    elif query.data == "stats":
        if query.from_user.id not in ADMINS:
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
        uptime = get_readable_time(time_now() - temp.START_TIME)
        buttons = [[
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='about')
        ]]
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.STATUS_TXT.format(users, prm, chats, used_data_db_size, files, used_files_db_size, secnd_files, secnd_files_db_used_size, uptime)),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif query.data == "owner":
        buttons = [[InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='about')]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.MY_OWNER_TXT),
            reply_markup=reply_markup
        )
        
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('User Command', callback_data='user_command'),
            InlineKeyboardButton('Admin Command', callback_data='admin_command')
        ],[
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.HELP_TXT.format(query.from_user.mention)),
            reply_markup=reply_markup
        )

    elif query.data == "user_command":
        buttons = [[
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.USER_COMMAND_TXT),
            reply_markup=reply_markup
        )
        
    elif query.data == "admin_command":
        if query.from_user.id not in ADMINS:
            return await query.answer("ADMINS Only!", show_alert=True)
        buttons = [[
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.ADMIN_COMMAND_TXT),
            reply_markup=reply_markup
        )

    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('≼ ʙᴀᴄᴋ', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_media(
            InputMediaPhoto(random.choice(PICS), caption=script.SOURCE_TXT),
            reply_markup=reply_markup
        )
  
    elif query.data.startswith("bool_setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer("You not admin in this group.", show_alert=True)
            return

        if status == "True":
            await save_group_settings(int(grp_id), set_type, False)
        else:
            await save_group_settings(int(grp_id), set_type, True)

        btn = await get_grp_stg(int(grp_id))
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))
            
    elif query.data.startswith("imdb_setgs"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        settings = await get_settings(int(grp_id))
        btn = [[
            InlineKeyboardButton('Set IMDb template', callback_data=f'set_imdb#{grp_id}')
        ],[
            InlineKeyboardButton('Default IMDb template', callback_data=f'default_imdb#{grp_id}')
        ],[
            InlineKeyboardButton('Back', callback_data=f'back_setgs#{grp_id}')
        ]]
        await query.message.edit(f'Select you want option\n\nCurrent template:\n{settings["template"]}', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_imdb"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        m = await query.message.edit('Send imdb template with formats')
        msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        await save_group_settings(int(grp_id), 'template', msg.text)
        await m.delete()
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'imdb_setgs#{grp_id}')
        ]]
        await query.message.reply('Successfully changed template', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("default_imdb"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        await save_group_settings(int(grp_id), 'template', script.IMDB_TEMPLATE)
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'imdb_setgs#{grp_id}')
        ]]
        await query.message.edit('Successfully changed template to default', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("welcome_setgs"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        settings = await get_settings(int(grp_id))
        btn = [[
            InlineKeyboardButton('Set Welcome', callback_data=f'set_welcome#{grp_id}')
        ],[
            InlineKeyboardButton('Default Welcome', callback_data=f'default_welcome#{grp_id}')
        ],[
            InlineKeyboardButton('Back', callback_data=f'back_setgs#{grp_id}')
        ]]
        await query.message.edit(f'Select you want option\n\nCurrent welcome:\n{settings["welcome_text"]}', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_welcome"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        m = await query.message.edit('Send Welcome with formats')
        msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        await save_group_settings(int(grp_id), 'welcome_text', msg.text)
        await m.delete()
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'welcome_setgs#{grp_id}')
        ]]
        await query.message.reply('Successfully changed Welcome', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("default_welcome"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        await save_group_settings(int(grp_id), 'welcome_text', script.WELCOME_TEXT)
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'welcome_setgs#{grp_id}')
        ]]
        await query.message.edit('Successfully changed Welcome to default', reply_markup=InlineKeyboardMarkup(btn))

    
    elif query.data.startswith("tutorial_setgs"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        settings = await get_settings(int(grp_id))
        btn = [[
            InlineKeyboardButton('Set tutorial link', callback_data=f'set_tutorial#{grp_id}')
        ],[
            InlineKeyboardButton('Default tutorial link', callback_data=f'default_tutorial#{grp_id}')
        ],[
            InlineKeyboardButton('Back', callback_data=f'back_setgs#{grp_id}')
        ]]
        await query.message.edit(f'Select you want option\n\nCurrent tutorial link:\n{settings["tutorial"]}', reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        
    elif query.data.startswith("set_tutorial"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        m = await query.message.edit('Send tutorial link')
        msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        await save_group_settings(int(grp_id), 'tutorial', msg.text)
        await m.delete()
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'tutorial_setgs#{grp_id}')
        ]]
        await query.message.reply('Successfully changed tutorial link', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("default_tutorial"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        await save_group_settings(int(grp_id), 'tutorial', TUTORIAL)
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'tutorial_setgs#{grp_id}')
        ]]
        await query.message.edit('Successfully changed tutorial link to default', reply_markup=InlineKeyboardMarkup(btn))

    
    elif query.data.startswith("shortlink_setgs"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        settings = await get_settings(int(grp_id))
        btn = [[
            InlineKeyboardButton('Set shortlink', callback_data=f'set_shortlink#{grp_id}')
        ],[
            InlineKeyboardButton('Default shortlink', callback_data=f'default_shortlink#{grp_id}')
        ],[
            InlineKeyboardButton('Back', callback_data=f'back_setgs#{grp_id}')
        ]]
        await query.message.edit(f'Select you want option\n\nCurrent shortlink:\n{settings["url"]} - {settings["api"]}', reply_markup=InlineKeyboardMarkup(btn))
        
    elif query.data.startswith("set_shortlink"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        m = await query.message.edit('Send shortlink url')
        url_msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        await m.delete()
        k = await query.message.reply('Send shortlink api key')
        key_msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        await save_group_settings(int(grp_id), 'url', url_msg.text)
        await save_group_settings(int(grp_id), 'api', key_msg.text)
        await k.delete()
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'shortlink_setgs#{grp_id}')
        ]]
        await query.message.reply('Successfully changed shortlink', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("default_shortlink"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        await save_group_settings(int(grp_id), 'url', SHORTLINK_URL)
        await save_group_settings(int(grp_id), 'api', SHORTLINK_API)
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'shortlink_setgs#{grp_id}')
        ]]
        await query.message.edit('Successfully changed shortlink to default', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("caption_setgs"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        settings = await get_settings(int(grp_id))
        btn = [[
            InlineKeyboardButton('Set caption', callback_data=f'set_caption#{grp_id}')
        ],[
            InlineKeyboardButton('Default caption', callback_data=f'default_caption#{grp_id}')
        ],[
            InlineKeyboardButton('Back', callback_data=f'back_setgs#{grp_id}')
        ]]
        await query.message.edit(f'Select you want option\n\nCurrent caption:\n{settings["caption"]}', reply_markup=InlineKeyboardMarkup(btn))
        
        
    elif query.data.startswith("set_caption"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        m = await query.message.edit('Send caption with formats')
        msg = await client.listen(chat_id=query.message.chat.id, user_id=query.from_user.id)
        await save_group_settings(int(grp_id), 'caption', msg.text)
        await m.delete()
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'caption_setgs#{grp_id}')
        ]]
        await query.message.reply('Successfully changed caption', reply_markup=InlineKeyboardMarkup(btn))


    elif query.data.startswith("default_caption"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        await save_group_settings(int(grp_id), 'caption', script.FILE_CAPTION)
        btn = [[
            InlineKeyboardButton('Back', callback_data=f'caption_setgs#{grp_id}')
        ]]
        await query.message.edit('Successfully changed caption to default', reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("back_setgs"):
        _, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        btn = await get_grp_stg(int(grp_id))
        chat = await client.get_chat(int(grp_id))
        await query.message.edit(text=f"Change your settings for <b>'{chat.title}'</b> as your wish. ⚙", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "open_group_settings":
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, query.message.chat.id, userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        btn = await get_grp_stg(query.message.chat.id)
        await query.message.edit(text=f"Change your settings for <b>'{query.message.chat.title}'</b> as your wish. ⚙", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "open_pm_settings":
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, query.message.chat.id, userid):
            return await query.answer("You not admin in this group.", show_alert=True)
        btn = await get_grp_stg(query.message.chat.id)
        try:
            await client.send_message(query.from_user.id, f"Change your settings for <b>'{query.message.chat.title}'</b> as your wish. ⚙", reply_markup=InlineKeyboardMarkup(btn))
        except:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start=settings_{query.message.chat.id}")
        btn = [[
            InlineKeyboardButton('Go To PM', url=f"https://t.me/{temp.U_NAME}")
        ]]
        await query.message.edit("Settings menu has been sent to PM", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("delete"):
        _, query_ = query.data.split("_", 1)
        await query.message.edit('Deleting...')
        deleted = await delete_files(query_)
        await query.message.edit(f'Deleted {deleted} files in your database in your query {query_}')
     
    elif query.data.startswith("send_all"):
        ident, key, req = query.data.split("#")
        if int(req) != query.from_user.id:
            return await query.answer(f"Hello {query.from_user.first_name},\nDon't Click Other Results!", show_alert=True)        
        files = temp.FILES.get(key)
        if not files:
            await query.answer(f"Hello {query.from_user.first_name},\nSend New Request Again!", show_alert=True)
            return        
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=all_{query.message.chat.id}_{key}")

    elif query.data == "unmute_all_members":
        if not await is_check_admin(client, query.message.chat.id, query.from_user.id):
            await query.answer("This Is Not For You!", show_alert=True)
            return
        users_id = []
        await query.message.edit("Unmute all started! This process maybe get some time...")
        try:
            async for member in client.get_chat_members(query.message.chat.id, filter=enums.ChatMembersFilter.RESTRICTED):
                users_id.append(member.user.id)
            for user_id in users_id:
                await client.unban_chat_member(query.message.chat.id, user_id)
        except Exception as e:
            await query.message.delete()
            await query.message.reply(f'Something went wrong.\n\n<code>{e}</code>')
            return
        await query.message.delete()
        if users_id:
            await query.message.reply(f"Successfully unmuted <code>{len(users_id)}</code> users.")
        else:
            await query.message.reply('Nothing to unmute users.')

    elif query.data == "unban_all_members":
        if not await is_check_admin(client, query.message.chat.id, query.from_user.id):
            await query.answer("This Is Not For You!", show_alert=True)
            return
        users_id = []
        await query.message.edit("Unban all started! This process maybe get some time...")
        try:
            async for member in client.get_chat_members(query.message.chat.id, filter=enums.ChatMembersFilter.BANNED):
                users_id.append(member.user.id)
            for user_id in users_id:
                await client.unban_chat_member(query.message.chat.id, user_id)
        except Exception as e:
            await query.message.delete()
            await query.message.reply(f'Something went wrong.\n\n<code>{e}</code>')
            return
        await query.message.delete()
        if users_id:
            await query.message.reply(f"Successfully unban <code>{len(users_id)}</code> users.")
        else:
            await query.message.reply('Nothing to unban users.')

    elif query.data == "kick_muted_members":
        if not await is_check_admin(client, query.message.chat.id, query.from_user.id):
            await query.answer("This Is Not For You!", show_alert=True)
            return
        users_id = []
        await query.message.edit("Kick muted users started! This process maybe get some time...")
        try:
            async for member in client.get_chat_members(query.message.chat.id, filter=enums.ChatMembersFilter.RESTRICTED):
                users_id.append(member.user.id)
            for user_id in users_id:
                await client.ban_chat_member(query.message.chat.id, user_id, datetime.now() + timedelta(seconds=30))
        except Exception as e:
            await query.message.delete()
            await query.message.reply(f'Something went wrong.\n\n<code>{e}</code>')
            return
        await query.message.delete()
        if users_id:
            await query.message.reply(f"Successfully kicked muted <code>{len(users_id)}</code> users.")
        else:
            await query.message.reply('Nothing to kick muted users.')

    elif query.data == "kick_deleted_accounts_members":
        if not await is_check_admin(client, query.message.chat.id, query.from_user.id):
            await query.answer("This Is Not For You!", show_alert=True)
            return
        users_id = []
        await query.message.edit("Kick deleted accounts started! This process maybe get some time...")
        try:
            async for member in client.get_chat_members(query.message.chat.id):
                if member.user.is_deleted:
                    users_id.append(member.user.id)
            for user_id in users_id:
                await client.ban_chat_member(query.message.chat.id, user_id, datetime.now() + timedelta(seconds=30))
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
    """
    Auto filter function for handling search results, IMDB integration, 
    pagination buttons, and premium/shortlink features.
    """

    # Case: direct message search
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        search = re.sub(r"\s+", " ", re.sub(r"[-:\"';!]", " ", message.text)).strip()

        files, offset, total_results = await get_search_results(search)
        if not files:
            if settings.get("spell_check"):
                return await advantage_spell_chok(message, s)
            return await s.edit(f"I couldn't find <b>{search}</b>")

    # Case: callback search (spoll = tuple passed from query handler)
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll

    req = message.from_user.id if message and message.from_user else 0
    key = f"{message.chat.id}-{message.id}"

    # Store results in temp cache
    temp.FILES[key] = files
    temp.BUTTONS[key] = search

    # Files links text
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

    # Pagination & send-all buttons
    if offset != "":
        # With shortlink and non-premium
        if settings.get("shortlink") and not await is_premium(message.from_user.id, client):
            btn.insert(0, [
                InlineKeyboardButton("📰 Languages", callback_data=f"languages#{key}#{req}#{offset}"),
                InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{offset}")
            ])
            btn.insert(1, [
                InlineKeyboardButton("♻️ Send All ♻️", url=await get_shortlink(
                    settings["url"], settings["api"],
                    f"https://t.me/{temp.U_NAME}?start=all_{message.chat.id}_{key}"
                ))
            ])
        else:
            btn.insert(0, [
                InlineKeyboardButton("📰 Languages", callback_data=f"languages#{key}#{req}#{offset}"),
                InlineKeyboardButton("🔍 Quality", callback_data=f"quality#{key}#{req}#{offset}")
            ])
            btn.insert(1, [
                InlineKeyboardButton("♻️ Send All", callback_data=f"send_all#{key}#{req}")
            ])
        btn.append([
            InlineKeyboardButton(f"1/{math.ceil(int(total_results) / MAX_BTN)}", callback_data="buttons"),
            InlineKeyboardButton("Next »", callback_data=f"next_{req}_{key}_{offset}")
        ])
    else:
        if settings.get("shortlink") and not await is_premium(message.from_user.id, client):
            btn.insert(0, [
                InlineKeyboardButton("♻️ Send All ♻️", url=await get_shortlink(
                    settings["url"], settings["api"],
                    f"https://t.me/{temp.U_NAME}?start=all_{message.chat.id}_{key}"
                ))
            ])
        else:
            btn.insert(0, [
                InlineKeyboardButton("♻️ Send All ♻️", callback_data=f"send_all#{key}#{req}")
            ])

    # Premium button always at end
    btn.append([
        InlineKeyboardButton("🤑 Buy Premium", url=f"https://t.me/{temp.U_NAME}?start=premium")
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

    # Auto-delete message setup
    del_msg = (
        f"\n\n<b>⚠️ This message will auto-delete after "
        f"<code>{get_readable_time(DELETE_TIME)}</code> to avoid copyright issues.</b>"
        if settings.get("auto_delete") else ""
    )

    # Final message sending
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
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            # fallback poster
            poster = imdb["poster"].replace(".jpg", "._V1_UX360.jpg")
            k = await message.reply_photo(
                photo=poster,
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

    # Auto-delete logic
    if settings.get("auto_delete"):
        await asyncio.sleep(DELETE_TIME)
        await k.delete()
        try:
            await message.delete()
        except:
            pass

import asyncio
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils import temp, get_poster
from config import LOG_CHANNEL
import script  # assuming you have `script.NOT_FILE_TXT` defined


async def advantage_spell_chok(message, s):
    """
    Offer spelling correction / alternative movie suggestions when no results are found.
    """
    search = message.text.strip()
    google_search = search.replace(" ", "+")
    user_mention = message.from_user.mention if message.from_user else "Anonymous"
    user_id = message.from_user.id if message.from_user else 0

    # Base buttons (instructions + Google search)
    base_btn = [
        [
            InlineKeyboardButton("⚠️ Instructions ⚠️", callback_data="instructions"),
            InlineKeyboardButton("🔎 Search Google 🔍", url=f"https://www.google.com/search?q={google_search}")
        ]
    ]

    try:
        movies = await get_poster(search, bulk=True)
    except Exception:
        # API error or unexpected failure
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

    # If no movies found
    if not movies:
        n = await s.edit_text(
            text=script.NOT_FILE_TXT.format(user_mention, search),
            reply_markup=InlineKeyboardMarkup(base_btn)
        )
        await temp.BOT.send_message(
            LOG_CHANNEL,
            f"#No_Result\n\nRequester: {user_mention}\nContent: {search}"
        )
        await asyncio.sleep(60)
        await n.delete()
        try:
            await message.delete()
        except:
            pass
        return

    # Remove duplicates while preserving order
    movies = list(dict.fromkeys(movies))

    # Build suggestion buttons
    suggestion_buttons = [
        [InlineKeyboardButton(text=movie.get("title", "Unknown"), callback_data=f"spolling#{movie.movieID}#{user_id}")]
        for movie in movies
    ]
    suggestion_buttons.append([InlineKeyboardButton("🚫 Close 🚫", callback_data="close_data")])

    # Show suggestions
    suggestion_msg = await s.edit_text(
        text=(
            f"👋 Hello {user_mention},\n\n"
            f"I couldn't find <b>'{search}'</b> in the database.\n"
            f"Did you mean one of these? 👇"
        ),
        reply_markup=InlineKeyboardMarkup(suggestion_buttons)
    )

    # Auto-cleanup after 5 minutes
    await asyncio.sleep(300)
    await suggestion_msg.delete()
    try:
        await message.delete()
    except:
        pass
