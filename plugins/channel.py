from hydrogram import Client, filters
from info import INDEX_CHANNELS, INDEX_EXTENSIONS
from database.ia_filterdb import save_file

# Filter for documents and videos
media_filter = filters.document | filters.video

@Client.on_message(filters.chat(INDEX_CHANNELS) & media_filter)
async def media_handler(bot, message):
    """Handles incoming media from INDEX_CHANNELS and saves eligible files."""
    # Get the media object (document or video)
    media = getattr(message, message.media.value, None)
    
    if not media:
        return  # No valid media found
    
    # Check if file extension is in allowed INDEX_EXTENSIONS
    file_name = str(getattr(media, "file_name", "")).lower()
    if not file_name.endswith(tuple(INDEX_EXTENSIONS)):
        return  # Ignore files with disallowed extensions
    
    # Preserve caption if exists
    media.caption = message.caption or ""
    
    # Save the media using database function
    await save_file(media)