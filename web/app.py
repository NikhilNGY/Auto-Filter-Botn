# web/app.py
from aiohttp import web
import json
import asyncio

# ------------------------
# Create aiohttp app
# ------------------------
web_app = web.Application()

# ------------------------
# Index route
# ------------------------
async def index(request):
    return web.json_response({
        "status": "ok",
        "message": "Bot is running!"
    })

# ------------------------
# Health check route
# ------------------------
async def health_check(request):
    return web.Response(text="OK", status=200)

# ------------------------
# Add routes
# ------------------------
web_app.router.add_get("/", index)
web_app.router.add_get("/healthz", health_check)
