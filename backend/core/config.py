import os
from dotenv import load_dotenv

load_dotenv()

def get_cors_origins():
    raw = os.getenv("CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]
