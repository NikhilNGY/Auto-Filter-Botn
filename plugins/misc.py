from info import ADMINS
from speedtest import Speedtest, ConfigRetrievalError, SpeedtestBestServerFailure
from hydrogram import Client, filters, enums
from hydrogram.errors import UserNotParticipant
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_size
from datetime import datetime
import os


# ---------------- /id Command ---------------- #
@Client.on_message(filters.command('id'))
async def showid(client, message):
    chat_type = message.chat.type
    replied_to_msg = message.reply_to_message

    if replied_to_msg:
        if replied_to_msg.forward_from_chat:
            return await message.reply_text(
                f"The forwarded message is from channel <b>{replied_to_msg.forward_from_chat.title}</b>\nID: <code>{replied_to_msg.forward_from_chat.id}</code>"
            )
        else:
            return await message.reply_text(
                f"The message is from user <b>{replied_to_msg.from_user.first_name}</b>\nID: <code>{replied_to_msg.from_user.id}</code>"
            )

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text(f'★ User ID: <code>{message.from_user.id}</code>')

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await message.reply_text(f'★ Group ID: <code>{message.chat.id}</code>')

    elif chat_type == enums.ChatType.CHANNEL:
        await message.reply_text(f'★ Channel ID: <code>{message.chat.id}</code>')


# ---------------- /speedtest Command ---------------- #
@Client.on_message(filters.command('speedtest') & filters.user(ADMINS))
async def speedtest(client, message):
    msg = await message.reply_text("Running Speedtest... ⏳")
    try:
        speed = Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        speed.results.share()
        result = speed.results.dict()
    except (ConfigRetrievalError, SpeedtestBestServerFailure):
        return await msg.edit("❌ Can't connect to Speedtest server. Try again later.")
    except Exception as e:
        return await msg.edit(f"❌ Error: {e}")

    # Formatting result
    timestamp = result.get('timestamp')
    time_str = timestamp
    if timestamp:
        try:
            time_str = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

    text = f"""
<b>➲ SPEEDTEST RESULTS</b>
┠ <b>Upload:</b> <code>{get_size(result['upload'])}/s</code>
┠ <b>Download:</b> <code>{get_size(result['download'])}/s</code>
┠ <b>Ping:</b> <code>{result['ping']} ms</code>
┠ <b>Time:</b> <code>{time_str}</code>
┠ <b>Data Sent:</b> <code>{get_size(int(result['bytes_sent']))}</code>
┖ <b>Data Received:</b> <code>{get_size(int(result['bytes_received']))}</code>

<b>➲ SERVER INFO</b>
┠ <b>Name:</b> <code>{result['server']['name']}</code>
┠ <b>Country:</b> <code>{result['server']['country']}, {result['server']['cc']}</code>
┠ <b>Sponsor:</b> <code>{result['server']['sponsor']}</code>
┠ <b>Latency:</b> <code>{result['server']['latency']} ms</code>
┠ <b>Location:</b> <code>{result['server']['lat']}, {result['server']['lon']}</code>

<b>➲ CLIENT INFO</b>
┠ <b>IP:</b> <code>{result['client']['ip']}</code>
┠ <b>Location:</b> <code>{result['client']['lat']}, {result['client']['lon']}</code>
┠ <b>Country:</b> <code>{result['client']['country']}</code>
┠ <b>ISP:</b> <code>{result['client']['isp']}</code>
┖ <b>ISP Rating:</b> <code>{result['client']['isprating']}</code>
"""

    await message.reply_photo(photo=result['share'], caption=text)
    await msg.delete()


# ---------------- /info Command ---------------- #
@Client.on_message(filters.command("info"))
async def who_is(client, message):
    status_message = await message.reply_text("Fetching user info... ⏳")

    # Determine user
    if message.reply_to_message:
        from_user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        from_user_id = message.command[1]
    else:
        from_user_id = message.from_user.id

    try:
        user = await client.get_users(from_user_id)
    except Exception as e:
        await status_message.edit(f"❌ Error: {e}")
        return

    username = f"@{user.username}" if user.username else "Not available"
    last_name = user.last_name or "Not available"
    dc_id = user.dc_id or "Unknown"

    info_text = (
        f"<b>➲ First Name:</b> {user.first_name}\n"
        f"<b>➲ Last Name:</b> {last_name}\n"
        f"<b>➲ Telegram ID:</b> <code>{user.id}</code>\n"
        f"<b>➲ Username:</b> {username}\n"
        f"<b>➲ Data Centre:</b> <code>{dc_id}</code>\n"
        f"<b>➲ Last Online:</b> {last_online(user)}\n"
        f"<b>➲ User Link:</b> <a href='tg://user?id={user.id}'>Click Here</a>\n"
    )

    # Chat join date (if applicable)
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            member = await message.chat.get_member(user.id)
            if member.joined_date:
                info_text += f"<b>➲ Joined This Chat:</b> <code>{member.joined_date.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
        except UserNotParticipant:
            pass

    # Send photo if available
    if user.photo:
        local_photo = await client.download_media(user.photo.big_file_id)
        await message.reply_photo(photo=local_photo, caption=info_text, parse_mode=enums.ParseMode.HTML)
        os.remove(local_photo)
    else:
        await message.reply_text(info_text, parse_mode=enums.ParseMode.HTML)

    await status_message.delete()


def last_online(user):
    if user.is_bot:
        return "🤖 Bot"
    status = getattr(user, 'status', None)
    if status == enums.UserStatus.ONLINE:
        return "Currently Online"
    elif status == enums.UserStatus.RECENTLY:
        return "Recently"
    elif status == enums.UserStatus.LAST_WEEK:
        return "Within Last Week"
    elif status == enums.UserStatus.LAST_MONTH:
        return "Within Last Month"
    elif status == enums.UserStatus.LONG_AGO:
        return "A long time ago"
    elif status == enums.UserStatus.OFFLINE:
        return user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S") if user.last_online_date else "Offline"
    return "Unknown"