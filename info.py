
import re
import logging
from os import environ
from Script import script

# ---------------- LOGGER ---------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------- HELPERS ---------------- #
def is_enabled(env_name: str, default: bool) -> bool:
    data = environ.get(env_name, str(default)).lower()
    if data in ["true", "yes", "1", "enable", "y"]:
        return True
    elif data in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        logger.error(f"{env_name} is invalid -> {data}. Exiting now.")
        exit(1)


def is_valid_ip(ip: str) -> bool:
    ip_pattern = (
        r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    return re.match(ip_pattern, ip) is not None


def get_required_env(name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        logger.error(f"{name} is missing. Exiting now.")
        exit(1)
    return value


def get_int_env(name: str, default: int) -> int:
    try:
        return int(environ.get(name, default))
    except ValueError:
        logger.error(f"{name} must be an integer. Exiting now.")
        exit(1)


# ---------------- BOT INFO ---------------- #
API_ID = get_int_env("API_ID")
API_HASH = get_required_env("API_HASH")
BOT_TOKEN = get_required_env("BOT_TOKEN")

if BOT_TOKEN:
    BOT_ID = int(BOT_TOKEN.split(":")[0])
else:
    logger.error("BOT_TOKEN is empty. Exiting now.")
    exit(1)

PORT = get_int_env("PORT", 8080)

# ---------------- IMAGES ---------------- #
PICS = environ.get("PICS", "https://envs.sh/t3L.jpg").split() or ["https://envs.sh/t3L.jpg"]

# ---------------- ADMINS ---------------- #
ADMINS = [int(x) for x in get_required_env("ADMINS", "2068233407 2098589219").split()]

# ---------------- CHANNELS ---------------- #
id_pattern = re.compile(r"^-?\d+$")  # Added pattern for checking IDs

INDEX_CHANNELS = [
    int(x) if id_pattern.match(x) else x for x in environ.get("INDEX_CHANNELS", "-1001892397342").split()
]

LOG_CHANNEL = int(get_required_env("LOG_CHANNEL"))
SUPPORT_GROUP = int(get_required_env("SUPPORT_GROUP"))

DELETE_CHANNELS = [
    int(dch) if id_pattern.match(dch) else dch
    for dch in environ.get("DELETE_CHANNELS", "-1001396923650").split()
]

# ---------------- DATABASES ---------------- #
DATA_DATABASE_URL = get_required_env("DATA_DATABASE_URL")
FILES_DATABASE_URL = get_required_env("FILES_DATABASE_URL")
SECOND_FILES_DATABASE_URL = environ.get("SECOND_FILES_DATABASE_URL", "")

DATABASE_NAME = environ.get("DATABASE_NAME", "Autof1")
COLLECTION_NAME = environ.get("COLLECTION_NAME", "Files")

# ---------------- LINKS ---------------- #
SUPPORT_LINK = environ.get("SUPPORT_LINK", "https://t.me/Sandalwood_Kannada_Group")
UPDATES_LINK = environ.get("UPDATES_LINK", "https://t.me/+pCz5eoun5Zk5YzRl")
FILMS_LINK = environ.get("FILMS_LINK", "https://t.me/sandalwood_kannada_moviesz")
TUTORIAL = environ.get("TUTORIAL", "https://t.me/how_to_opan_linkz/6")
VERIFY_TUTORIAL = environ.get("VERIFY_TUTORIAL", "https://t.me/how_to_opan_linkz/6")

# ---------------- BOT SETTINGS ---------------- #
TIME_ZONE = environ.get("TIME_ZONE", "Asia/Colombo")
DELETE_TIME = get_int_env("DELETE_TIME", 3600)
CACHE_TIME = get_int_env("CACHE_TIME", 300)
MAX_BTN = get_int_env("MAX_BTN", 8)

IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", script.IMDB_TEMPLATE)
FILE_CAPTION = environ.get("FILE_CAPTION", script.FILE_CAPTION)
WELCOME_TEXT = environ.get("WELCOME_TEXT", script.WELCOME_TEXT)

SHORTLINK_URL = environ.get("SHORTLINK_URL", "vplink.in")
SHORTLINK_API = environ.get("SHORTLINK_API", "")
VERIFY_EXPIRE = get_int_env("VERIFY_EXPIRE", 86400)
INDEX_EXTENSIONS = [x.lower() for x in environ.get("INDEX_EXTENSIONS", "mp4 mkv").split()]
PM_FILE_DELETE_TIME = get_int_env("PM_FILE_DELETE_TIME", 3600)

# ---------------- BOOLEAN FLAGS ---------------- #
USE_CAPTION_FILTER = is_enabled("USE_CAPTION_FILTER", False)
IS_VERIFY = is_enabled("IS_VERIFY", False)
AUTO_DELETE = is_enabled("AUTO_DELETE", True)
WELCOME = is_enabled("WELCOME", False)
PROTECT_CONTENT = is_enabled("PROTECT_CONTENT", False)
LONG_IMDB_DESCRIPTION = is_enabled("LONG_IMDB_DESCRIPTION", False)
LINK_MODE = is_enabled("LINK_MODE", False)
IMDB = is_enabled("IMDB", False)
SPELL_CHECK = is_enabled("SPELL_CHECK", False)
SHORTLINK = is_enabled("SHORTLINK", False)

# ---------------- REACTIONS & STICKERS ---------------- #
REACTIONS = environ.get(
    "REACTIONS",
    "🤝 😇 🤗 😍 👍 🎅 😐 🥰 🤩 😱 🤣 😘 👏 😛 😈 🎉 ⚡️ 🫡 🤓 😎 🏆 🔥 🤭 🌚 🆒 👻 😁"
).split()

STICKERS = environ.get(
    "STICKERS",
    "CAACAgIAAxkBAAEN4ctnu1NdZUe21tiqF1CjLCZW8rJ28QACmQwAAj9UAUrPkwx5a8EilDYE "
    "CAACAgIAAxkBAAEN1pBntL9sz1tuP_qo0bCdLj_xQa28ngACxgEAAhZCawpKI9T0ydt5RzYE"
).split()