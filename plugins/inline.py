from hydrogram import Client
from hydrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
    InlineQuery
)
from database.ia_filterdb import get_search_results
from utils import get_size, temp, get_verify_status, is_subscribed, is_premium
from info import CACHE_TIME, SUPPORT_LINK, UPDATES_LINK, FILE_CAPTION, IS_VERIFY

cache_time = CACHE_TIME


def is_banned(query: InlineQuery) -> bool:
    """Check if user is banned"""
    return query.from_user and query.from_user.id in temp.BANNED_USERS


def get_reply_markup(query_text: str) -> InlineKeyboardMarkup:
    """Generate inline reply markup buttons"""
    buttons = [
        [InlineKeyboardButton('🔎 Search Again', switch_inline_query_current_chat=query_text or '')],
        [
            InlineKeyboardButton('⚡️ Updates Channel ⚡️', url=UPDATES_LINK),
            InlineKeyboardButton('💡 Support Group 💡', url=SUPPORT_LINK)
        ]
    ]
    return InlineKeyboardMarkup(buttons)


@Client.on_inline_query()
async def inline_search(bot, query: InlineQuery):
    """Handle inline search queries"""

    # Force subscription check
    if not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="Join my Updates Channel :(",
            switch_pm_parameter="inline_fsub"
        )
        return

    # Verification check
    verify_status = await get_verify_status(query.from_user.id)
    if IS_VERIFY and not verify_status['is_verified'] and not await is_premium(query.from_user.id, bot):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="You're not verified today :(",
            switch_pm_parameter="inline_verify"
        )
        return

    # Banned check
    if is_banned(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="You're a banned user :(",
            switch_pm_parameter="start"
        )
        return

    # Fetch search results
    results = []
    search_text = query.query
    offset = int(query.offset or 0)
    files, next_offset, total = await get_search_results(search_text, offset=offset)

    for file in files:
        reply_markup = get_reply_markup(search_text)
        caption = FILE_CAPTION.format(
            file_name=file['file_name'],
            file_size=get_size(file['file_size']),
            caption=file.get('caption', '')
        )
        results.append(
            InlineQueryResultCachedDocument(
                title=file['file_name'],
                document_file_id=file['_id'],
                caption=caption,
                description=f"Size: {get_size(file['file_size'])}",
                reply_markup=reply_markup
            )
        )

    # Respond with results
    if results:
        switch_pm_text = f"Results - {total}"
        if search_text:
            switch_pm_text += f" For: {search_text}"

        await query.answer(
            results=results,
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="start",
            next_offset=str(next_offset)
        )
    else:
        switch_pm_text = "No Results"
        if search_text:
            switch_pm_text += f" For: {search_text}"

        await query.answer(
            results=[],
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="start"
        )