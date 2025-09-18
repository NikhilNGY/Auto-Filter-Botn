import re
import time
import asyncio
from hydrogram import Client, filters, enums
from hydrogram.errors import FloodWait
from info import ADMINS, INDEX_EXTENSIONS
from database.ia_filterdb import save_file
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time

lock = asyncio.Lock()


# ---------------- Callback for indexing ---------------- #
@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    _, ident, chat, lst_msg_id, skip = query.data.split("#")

    if ident == 'yes':
        msg = query.message
        await msg.edit("Starting indexing...")
        try:
            chat = int(chat)
        except:
            pass
        await index_files_to_db(int(lst_msg_id), chat, msg, bot, int(skip))

    elif ident == 'cancel':
        temp.CANCEL = True
        await query.message.edit("Trying to cancel indexing...")


# ---------------- /index command ---------------- #
@Client.on_message(filters.command('index') & filters.private & filters.user(ADMINS))
async def send_for_index(bot, message):
    if lock.locked():
        return await message.reply("Wait until previous indexing process completes.")

    i = await message.reply("Forward the last message or send the last message link.")
    msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await i.delete()

    # Get message ID and chat
    if msg.text and msg.text.startswith("https://t.me/"):
        try:
            msg_link = msg.text.split("/")
            last_msg_id = int(msg_link[-1])
            chat_id = msg_link[-2]
            if chat_id.isnumeric():
                chat_id = int(f"-100{chat_id}")
        except:
            return await message.reply("Invalid message link!")
    elif msg.forward_from_chat and msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = msg.forward_from_message_id
        chat_id = msg.forward_from_chat.username or msg.forward_from_chat.id
    else:
        return await message.reply("This is not a forwarded message or a valid link.")

    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f"Error fetching chat - {e}")

    if chat.type != enums.ChatType.CHANNEL:
        return await message.reply("I can only index channels.")

    # Ask for skip message number
    s = await message.reply("Send skip message number (0 for no skip).")
    msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await s.delete()
    try:
        skip = int(msg.text)
    except:
        return await message.reply("Invalid number.")

    # Confirm indexing
    buttons = [
        [InlineKeyboardButton('YES', callback_data=f'index#yes#{chat_id}#{last_msg_id}#{skip}')],
        [InlineKeyboardButton('CANCEL', callback_data='index#cancel#0#0#0')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(
        f"Do you want to index channel <b>{chat.title}</b>?\nTotal Messages: <code>{last_msg_id}</code>",
        reply_markup=reply_markup
    )


# ---------------- Index messages to database ---------------- #
async def index_files_to_db(lst_msg_id, chat, msg, bot, skip):
    start_time = time.time()
    total_files = duplicate = errors = deleted = no_media = unsupported = badfiles = 0
    current = skip

    async with lock:
        try:
            async for message in bot.iter_messages(chat, lst_msg_id, skip):
                if temp.CANCEL:
                    temp.CANCEL = False
                    await msg.edit(f"Indexing cancelled.\n\nSaved <code>{total_files}</code> files.\nDuplicate skipped: <code>{duplicate}</code>\nDeleted skipped: <code>{deleted}</code>\nNon-media skipped: <code>{no_media + unsupported}</code>\nUnsupported: <code>{unsupported}</code>\nErrors: <code>{errors}</code>\nBad files: <code>{badfiles}</code>\nTime taken: {get_readable_time(time.time()-start_time)}")
                    return

                current += 1

                # Update progress every 30 messages
                if current % 30 == 0:
                    btn = [[InlineKeyboardButton('CANCEL', callback_data=f'index#cancel#{chat}#{lst_msg_id}#{skip}')]]
                    try:
                        await msg.edit(
                            text=f"Processed: <code>{current}</code>\nSaved: <code>{total_files}</code>\nDuplicate: <code>{duplicate}</code>\nDeleted: <code>{deleted}</code>\nNon-media skipped: <code>{no_media + unsupported}</code>\nUnsupported: <code>{unsupported}</code>\nErrors: <code>{errors}</code>\nBad files: <code>{badfiles}</code>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)

                # Skip deleted/empty/non-media messages
                if message.empty:
                    deleted += 1
                    continue
                if not message.media:
                    no_media += 1
                    continue
                if message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue

                media = getattr(message, message.media.value, None)
                if not media or not str(media.file_name).lower().endswith(tuple(INDEX_EXTENSIONS)):
                    unsupported += 1
                    continue

                media.caption = message.caption or ""
                file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name))

                # Save file
                status = await save_file(media)
                if status == 'suc':
                    total_files += 1
                elif status == 'dup':
                    duplicate += 1
                elif status == 'err':
                    errors += 1

        except Exception as e:
            await msg.reply(f"Indexing cancelled due to error - {e}")
            return

        # Final report
        await msg.edit(
            f"Indexing completed.\nSaved <code>{total_files}</code> files.\nDuplicate skipped: <code>{duplicate}</code>\nDeleted skipped: <code>{deleted}</code>\nNon-media skipped: <code>{no_media + unsupported}</code>\nUnsupported: <code>{unsupported}</code>\nErrors: <code>{errors}</code>\nBad files: <code>{badfiles}</code>\nTime taken: {get_readable_time(time.time()-start_time)}"
        )