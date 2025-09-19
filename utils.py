# @Nikhil5757h 
import asyncio
import re
import requests
import pytz
from datetime import datetime
from hydrogram.errors import UserNotParticipant, FloodWait
from hydrogram import enums
from hydrogram.types import InlineKeyboardButton
from info import LONG_IMDB_DESCRIPTION, ADMINS, TIME_ZONE
from imdb import Cinemagoer
from database.users_chats_db import db
from shortzy import Shortzy

imdb = Cinemagoer()


class Temp:
    """Global temporary storage."""
    START_TIME = 0
    ME = None
    CANCEL = False
    U_NAME = None
    B_NAME = None
    SETTINGS = {}
    VERIFICATIONS = {}
    FILES = {}
    USERS_CANCEL = False
    GROUPS_CANCEL = False
    BOT = None
    BANNED_USERS = []
    BANNED_CHATS = []

temp = Temp()


# -------------------------
# Bot initialization
# -------------------------
async def init_banned_chats():
    """Load disabled chats into memory."""
    all_chats = await db.get_all_chats()
    temp.BANNED_CHATS = [
        c['id'] for c in all_chats if c.get('chat_status', {}).get('is_disabled')
    ]


async def init_group_settings():
    """Load all group settings into memory."""
    all_chats = await db.get_all_chats()
    for chat in all_chats:
        temp.SETTINGS[chat['id']] = chat.get('settings', {})


async def startup(bot):
    """Call this after bot starts."""
    temp.BOT = bot
    await init_banned_chats()
    await init_group_settings()


# -------------------------
# Helper Functions
# -------------------------
async def is_subscribed(bot, query):
    """Check if user is subscribed to required channels."""
    btn = []
    stg = db.get_bot_sttgs()
    if not stg or not stg.get('FORCE_SUB_CHANNELS'):
        return btn
    force_sub_channels = stg.get('FORCE_SUB_CHANNELS', '')
    if force_sub_channels:
        for id in force_sub_channels.split():
            chat = await bot.get_chat(int(id))
            try:
                await bot.get_chat_member(int(id), query.from_user.id)
            except UserNotParticipant:
                btn.append([InlineKeyboardButton(f'Join : {chat.title}', url=chat.invite_link)])
    return btn


def upload_image(file_path):
    """Upload image to uguu.se."""
    try:
        with open(file_path, 'rb') as f:
            files = {'files[]': f}
            response = requests.post("https://uguu.se/upload", files=files)
        if response.status_code == 200:
            data = response.json()
            return data['files'][0]['url'].replace('\\/', '/')
        return None
    except Exception:
        return None


# ------------------------------
# Broadcast Functions
# ------------------------------
async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, None
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except Exception as err:
        return False, str(err)


async def groups_broadcast_messages(chat_id, message):
    try:
        await message.copy(chat_id=chat_id)
        return True, None
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await groups_broadcast_messages(chat_id, message)
    except Exception as err:
        return False, str(err)


# ------------------------------
# IMDB Functions
# ------------------------------
async def get_poster(query, bulk=False, id=False, file=None):
    """Fetch movie/TV info from IMDB."""
    try:
        if not id:
            query = query.strip().lower()
            title = query
            year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
            year = str(year[0]) if year else None
            if year:
                title = query.replace(year, "").strip()
            elif file:
                year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
                year = str(year[0]) if year else None

            movieid_list = imdb.search_movie(title, results=10)
            if not movieid_list:
                return None
            if year:
                filtered = list(
                    filter(lambda k: str(k.get('year')) == str(year),
                           movieid_list)) or movieid_list
            else:
                filtered = movieid_list
            filtered = list(
                filter(lambda k: k.get('kind') in ['movie', 'tv series'],
                       filtered)) or movieid_list
            if bulk:
                return filtered
            movieid = filtered[0].movieID
        else:
            movieid = query

        movie = imdb.get_movie(movieid)
        date = movie.get("original air date") or movie.get("year") or "N/A"
        plot = (movie.get('plot') or ["N/A"])[0] if not LONG_IMDB_DESCRIPTION else movie.get('plot outline') or "N/A"
        if plot and len(plot) > 800:
            plot = plot[:800] + "..."

        return {
            'title': movie.get('title'),
            'votes': movie.get('votes'),
            'aka': list_to_str(movie.get('akas')),
            'seasons': movie.get('number of seasons'),
            'box_office': movie.get('box office'),
            'localized_title': movie.get('localized title'),
            'kind': movie.get('kind'),
            'imdb_id': f"tt{movie.get('imdbID')}",
            'cast': list_to_str(movie.get('cast')),
            'runtime': list_to_str(movie.get('runtimes')),
            'countries': list_to_str(movie.get('countries')),
            'certificates': list_to_str(movie.get('certificates')),
            'languages': list_to_str(movie.get('languages')),
            'director': list_to_str(movie.get('director')),
            'writer': list_to_str(movie.get('writer')),
            'producer': list_to_str(movie.get('producer')),
            'composer': list_to_str(movie.get('composer')),
            'cinematographer': list_to_str(movie.get('cinematographer')),
            'music_team': list_to_str(movie.get('music department')),
            'distributors': list_to_str(movie.get('distributors')),
            'release_date': date,
            'year': movie.get('year'),
            'genres': list_to_str(movie.get('genres')),
            'poster': movie.get('full-size cover url'),
            'plot': plot,
            'rating': str(movie.get('rating')),
            'url': f'https://www.imdb.com/title/tt{movieid}'
        }
    except Exception:
        return None


# ------------------------------
# Admin & Verification
# ------------------------------
async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except Exception:
        return False


async def get_verify_status(user_id):
    verify = temp.VERIFICATIONS.get(user_id)
    if not verify:
        verify = await db.get_verify_status(user_id)
        temp.VERIFICATIONS[user_id] = verify
    return verify


async def update_verify_status(user_id, verify_token="", is_verified=False, link="", expire_time=0):
    current = await get_verify_status(user_id)
    current.update({
        'verify_token': verify_token,
        'is_verified': is_verified,
        'link': link,
        'expire_time': expire_time
    })
    temp.VERIFICATIONS[user_id] = current
    await db.update_verify_status(user_id, current)


# ------------------------------
# Settings
# ------------------------------
async def get_settings(group_id):
    settings = temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        temp.SETTINGS[group_id] = settings
    return settings


async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current[key] = value
    temp.SETTINGS[group_id] = current
    await db.update_settings(group_id, current)


# ------------------------------
# Utils
# ------------------------------
def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"


def list_to_str(lst):
    if not lst:
        return "N/A"
    return ", ".join(str(x) for x in lst) if len(lst) > 1 else str(lst[0])


async def get_shortlink(url, api, link):
    try:
        shortzy = Shortzy(api_key=api, base_site=url)
        return await shortzy.convert(link)
    except Exception:
        return link


def get_readable_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = ""
    for name, sec in periods:
        if seconds >= sec:
            val, seconds = divmod(seconds, sec)
            result += f"{int(val)}{name}"
    return result


def get_wish():
    hour = int(datetime.now(pytz.timezone(TIME_ZONE)).strftime("%H"))
    if hour < 12:
        return "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞"
    elif hour < 18:
        return "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ 🌗"
    else:
        return "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"


async def get_seconds(time_string):
    units_map = {
        "s": 1,
        "min": 60,
        "hour": 3600,
        "day": 86400,
        "month": 86400 * 30,
        "year": 86400 * 365
    }
    value = int(''.join(filter(str.isdigit, time_string)) or 0)
    unit = ''.join(filter(str.isalpha, time_string))
    return value * units_map.get(unit, 0)
