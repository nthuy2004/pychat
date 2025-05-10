from .base_bot import BaseBot

from utils import clean_mentions

from extensions import gemini
from google.genai import types

from io import BytesIO
import os

from storage import bucket, DIR_PREFIX, get_url
from utils import generate_attachmentid, generate_messageid

from models.message import MessageAttachment

class GeminiBot(BaseBot):
    def __init__(self):
        super().__init__(uid=121212)
    
    def on_message(self, chat_id, message, user):
        try:
            super().on_message(chat_id, message, user)

            custom_msgid = generate_messageid()

            content_without_mention = clean_mentions(message["content"]).strip()

            if not content_without_mention:
                self.send_message("😡 Vui lòng nhập một thứ gì đó để tương tác với tôi...", custom_message_id=custom_msgid, save_to_db=False, only_send_to_sender=True)
                return

            self.send_message("Đang tạo đoạn hội thoại, xin vui lòng chờ...", loading=True, custom_message_id=custom_msgid, save_to_db=False)

            response = gemini.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=content_without_mention,
                config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
                )
            )

            text_content = ""
            attachments = []

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    text_content += (part.text) + '\n'
                elif part.inline_data is not None:
                    image_bytes = BytesIO(part.inline_data.data)
                    image_bytes.seek(0)

                    unique_filename = f"gemini-{os.urandom(10).hex()}.png"
                    upload_file_namee = f"{DIR_PREFIX}/{unique_filename}"

                    result = bucket.put_object(upload_file_namee, image_bytes)

                    if result.status == 200:
                        mimetype = part.inline_data.mime_type
                        a = MessageAttachment(
                            id=generate_attachmentid(),
                            message_id=custom_msgid,
                            mimetype=mimetype,
                            original_filename=unique_filename,
                            upload_filename=unique_filename
                        )

                        asave = a.save()
                        if asave:
                            attachments.append(asave.to_json())

            

            self.send_message(content=text_content, attachments=attachments, custom_message_id=custom_msgid)
        except Exception as e:
            self.send_message(f"Lỗi hệ thống: {e}", custom_message_id=custom_msgid, save_to_db=False, only_send_to_sender=True)