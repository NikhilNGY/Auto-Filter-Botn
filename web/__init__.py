# @Nikhil5757h 
from aiohttp import web

# Create aiohttp app
app = web.Application()

# ------------------------
# Health check endpoint
# ------------------------
async def handle_health(request):
    return web.Response(text="Bot is running ✓", status=200)

# Add route
app.add_routes([web.get("/", handle_health)])

# ------------------------
# Run web server
# ------------------------
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
