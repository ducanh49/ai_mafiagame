from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


if not api_key:
    raise RuntimeError("OPENAI_API_KEY nelze najit")
else:
    print(api_key)