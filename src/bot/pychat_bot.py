from .base_bot import BaseBot

from utils import clean_mentions

from extensions import deepseek

from utils import generate_messageid

class PyChatBot(BaseBot):
    def __init__(self):
        super().__init__(uid=696969)
    
    def on_message(self, chat_id, message, user):
        try:
            super().on_message(chat_id, message, user)

            custom_msgid = generate_messageid()

            content_without_mention = clean_mentions(message["content"]).strip()

            if not content_without_mention:
                self.send_message("😡 Vui lòng nhập một thứ gì đó để tương tác với tôi...", custom_message_id=custom_msgid, save_to_db=False, only_send_to_sender=True)
                return

            self.send_message("Đang tạo đoạn hội thoại, xin vui lòng chờ...", loading=True, custom_message_id=custom_msgid, save_to_db=False)


            completion = deepseek.chat.completions.create(
                model='deepseek-chat',
                messages=[
                    {
                        "role": "user",
                        "content": content_without_mention,
                    },
                ],
            )

            self.send_message(completion.choices[0].message.content, custom_message_id=custom_msgid)
        except Exception as e:
            self.send_message(f"Lỗi hệ thống: {e}", custom_message_id=custom_msgid, save_to_db=False, only_send_to_sender=True)