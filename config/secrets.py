from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("7834633279:AAFmabhepIVxeT_XQcYYsjOtFWoJizEe6wc")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_SECRET")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
