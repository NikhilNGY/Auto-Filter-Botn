import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logging.getLogger('hydrogram').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

import os
import time
import asyncio
import uvloop
from hydrogram import types, Client
from typing import Union, AsyncGenerator

from info import (
    LOG_CHANNEL, API_ID, API_HASH, BOT_TOKEN, PORT
)
from utils import temp
from database.users_chats_db import db

uvloop.install()


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Auto_Filter_Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"}
        )

    async def start(self):
        await super().start()
        temp.START_TIME = time.time()

        # Load banned users and chats if any
        temp.BANNED_USERS, temp.BANNED_CHATS = await db.get_banned()

        # Handle restart notification
        if os.path.exists("restart.txt"):
            try:
                with open("restart.txt", "r") as file:
                    chat_id, msg_id = map(int, file.read().split())
                await self.edit_message_text(chat_id=chat_id, message_id=msg_id, text="Restarted Successfully!")
            except Exception:
                logger.warning("Failed to send restart notification.")
            finally:
                os.remove("restart.txt")

        # Set bot info
        temp.BOT = self
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name

        # Start web server
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()

        # Notify log channel
        try:
            await self.send_message(chat_id=LOG_CHANNEL, text=f"<b>{me.mention} Restarted! 🤖</b>")
        except Exception:
            logger.error("Bot must be admin in LOG_CHANNEL. Exiting now.")
            exit()

        logger.info(f"@{me.username} is started now ✓")

    async def stop(self, *args, **kwargs):
        await super().stop()
        logger.info("Bot Stopped! Bye...")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0
    ) -> AsyncGenerator[types.Message, None]:
        """Iterate through chat messages sequentially."""
        current = offset
        while current < limit:
            to_fetch = min(200, limit - current)
            if to_fetch <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + to_fetch)))
            for message in messages:
                yield message
                current += 1


if __name__ == "__main__":
    app = Bot()
    app.run()