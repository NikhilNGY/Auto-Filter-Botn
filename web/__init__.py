from aiohttp import web

web_app = web.Application()

async def hello(request):
    return web.Response(text="Bot is running!")

web_app.add_routes([web.get("/", hello)])
