from aiohttp import web
import json

# Create aiohttp web application
web_app = web.Application()

async def index(request):
    return web.json_response({"status": "ok", "message": "Bot is running!"})

async def health_check(request):
    return web.Response(text="OK", status=200)

# Add routes
web_app.router.add_get("/", index)
web_app.router.add_get("/healthz", health_check)
