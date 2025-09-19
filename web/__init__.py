from aiohttp import web

# Minimal aiohttp web app for health check
web_app = web.Application()

async def handle_health(request):
    return web.Response(text="Bot is running ✓")

# Add health check route
web_app.add_routes([web.get("/", handle_health)])