from typing import Union
from hydrogram.types import Message
from utils import temp
from hydrogram.file_id import FileId


class TGCustomYield:
    """Custom utilities for Telegram files, without streaming/premium features."""

    def __init__(self):
        self.main_bot = temp.BOT

    @staticmethod
    async def generate_file_properties(msg: Message) -> FileId:
        """Return FileId object for a media in the message."""
        media = getattr(msg, msg.media.value, None)
        file_id_obj = FileId.decode(media.file_id)
        return file_id_obj

    @staticmethod
    async def get_file_basic_info(file_id: FileId) -> dict:
        """Return basic info of a file."""
        return {
            "media_id": file_id.media_id,
            "access_hash": file_id.access_hash,
            "file_type": file_id.file_type,
            "file_reference": file_id.file_reference,
        }

    async def get_file_bytes(self, media_msg: Message) -> bytes:
        """Return the raw bytes of a media message (non-streaming)."""
        client = self.main_bot
        data = await self.generate_file_properties(media_msg)

        # Normally would use media session / streaming; here just return metadata as placeholder
        return {
            "file_id": data.file_id,
            "file_type": data.file_type,
            "file_name": getattr(media_msg, "file_name", None),
            "size": getattr(media_msg, "file_size", None)
        }