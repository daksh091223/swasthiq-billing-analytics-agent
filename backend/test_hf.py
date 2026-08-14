import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

token = os.getenv("HF_TOKEN")

print("Token found:", token is not None)
print("Token prefix:", token[:7] if token else None)

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=token,
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b:groq",
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: SwasthiQ connection works."
        }
    ],
)

print(response.choices[0].message.content)