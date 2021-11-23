from asyncio.events import set_child_watcher
from aiogram import types


class CompactMessage():
    def __init__(self, message: types.Message) -> None:
        self.sender_id = message.from_user.id
        #
        self.sender_first_name = message.from_user.first_name
        #
        if message.text != None:
            self.text = message.text
        elif message.caption != None:
            self.text = message.caption
        else:
            self.text = None
        #
        self.content_type = message.content_type
        #
        if self.content_type == 'document':
            self.file_id = message.document.file_id
        elif self.content_type == 'photo':
            self.file_id = message.photo[-1].file_id
        else:
            self.file_id = None

    def get_message(self) -> dict:
        return (self.sender_id, self.sender_first_name, self.text, self.file_id, self.content_type)
