# Working with files
from .delete_files import delete_files
from .update_metadata import update_metadata
from .is_image_or_video import is_image_or_video

# Utils for downloaders
from .music_search_engine import search_music
from .get_applemusic_author import get_applemusic_author
from .get_spotify_author import get_spotify_author
from .spotify_login import get_access_token

#  Work with language
from .google_translate import translate_text

#  Bot utils
from .set_bot_commands import set_default_commands

#  Utils
from .random_emoji import random_emoji
from .random_emoji import random_cookie_file
from .truncate_string import truncate_string
from .register_services import get_service_handler
from .error_handler import handle_download_error
from .proxy import load_proxies

__all__ = [
    "delete_files",
    "get_applemusic_author",
    "get_spotify_author",
    "translate_text",
    "is_image_or_video",
    "search_music",
    "set_default_commands",
    "update_metadata",
    "random_emoji",
    "truncate_string",
    "get_service_handler",
    "handle_download_error",
    "get_access_token",
    "random_cookie_file",
    "load_proxies"
]
