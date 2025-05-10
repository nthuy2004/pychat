from openai import OpenAI

from config import Config

from google import genai
from google.genai import types
from io import BytesIO

client = genai.Client(api_key=Config.GEMINI_API)

response = client.models.generate_content(
    model="gemini-2.0-flash-preview-image-generation",
    contents="Tạo cho tôi ảnh câu lạc bộ arsenal nâng cúp C1",
    config=types.GenerateContentConfig(
      response_modalities=['TEXT', 'IMAGE']
    )
)

for part in response.candidates[0].content.parts:
  if part.text is not None:
    print(part.text)
  elif part.inline_data is not None:
    print(part.inline_data)