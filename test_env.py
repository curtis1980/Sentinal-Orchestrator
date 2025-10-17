import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")

if api_key and model:
    print("✅ Environment loaded successfully!")
    print(f"Model: {model}")
    print(f"Key prefix: {api_key[:10]}...")
else:
    print("❌ Something’s wrong — .env not loading.")
