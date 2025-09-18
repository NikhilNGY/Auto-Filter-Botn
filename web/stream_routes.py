import secrets
import mimetypes
from utils import temp
from aiohttp import web
from web.utils.render_template import media_watch

routes = web.RouteTableDef()


# -------------------------
# Root route
# -------------------------
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.Response(
        text='<h1 align="center"><a href="https://t.me/HA_Bots"><b>HA Bots</b></a></h1>',
        content_type='text/html'
    )


# -------------------------
# Watch media page
# -------------------------
@routes.get("/watch/{message_id}")
async def watch_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        html_content = await media_watch(message_id)
        return web.Response(text=html_content, content_type='text/html')
    except Exception:
        return web.Response(text="<h1>Something went wrong</h1>", content_type='text/html')


# -------------------------
# Download media
# -------------------------
@routes.get("/download/{message_id}")
async def download_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        return await media_download(request, message_id)
    except Exception:
        return web.Response(text="<h1>Something went wrong</h1>", content_type='text/html')


async def media_download(request, message_id: int):
    """
    Sends the requested media file as a download response.
    Partial content (Range) support is removed for simplicity.
    """
    media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
    media = getattr(media_msg, media_msg.media.value, None)

    file_size = media.file_size
    file_name = media.file_name if media.file_name else f"{secrets.token_hex(2)}.jpeg"
    mime_type = media.mime_type if media.mime_type else mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    # Fetch full media bytes
    file_bytes = await media.download(file_name=None, in_memory=True)

    return web.Response(
        status=200,
        body=file_bytes,
        headers={
            "Content-Type": mime_type,
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Content-Length": str(file_size),
        }
    )