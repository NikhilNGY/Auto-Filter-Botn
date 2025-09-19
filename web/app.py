# @Nikhil5757h 
from aiohttp import web
import json
import asyncio

# ------------------------
# Create aiohttp app
# ------------------------
app = web.Application()

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
app.router.add_get("/", index)
app.router.add_get("/healthz", health_check)

# ------------------------
# Run webserver
# ------------------------
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
